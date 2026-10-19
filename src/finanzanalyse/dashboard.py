
import streamlit as st
import os
from datetime import date
import pandas as pd
from dotenv import load_dotenv
from finanzanalyse.fints_import import (
    create_client,
    complete_tan,
    get_accounts,
    get_transactions_dataframe,
)
from finanzanalyse.abgleich import abgleichen

from finanzanalyse.database import load_transactions, create_database
from finanzanalyse.analyse import add_metaData
from finanzanalyse.data_import import import_all_files

from finanzanalyse.tabs.uebersicht import (
    zeige_uebersicht,
    zeige_letzte_fints_buchungen,
)
from finanzanalyse.tabs.kategorien import zeige_kategorien
from finanzanalyse.tabs.ausgaben import zeige_ausgaben
from finanzanalyse.tabs.einnahmen import zeige_einnahmen
from finanzanalyse.tabs.buchungen import zeige_buchungen

load_dotenv()


st.set_page_config(
    page_title="Finanzanalyse",
    page_icon="💶",
    layout="wide",
)

create_database()
number_imported = import_all_files()

@st.cache_data
def load_data():
    """Buchungen laden und vorbereiten."""
    df = load_transactions("2000-01-01", "2100-01-01")

    if df.empty:
        return df

    df["buchung"] = df["buchung"].astype("datetime64[ns]")
    return add_metaData(df)


def load_combined_data(csv_df):
    """CSV-Historie und aktuelle FinTS-Buchungen verbinden."""

    if csv_df.empty:
        raise ValueError("Die CSV-Historie ist leer.")

    # Letzter Buchungstag aus der CSV-Historie
    letzter_csv_tag = pd.to_datetime(csv_df["buchung"]).max().date()
    heute = date.today()

    # FinTS-Abfragen sind auf maximal 90 Tage begrenzt.
    zeitraum = (heute - letzter_csv_tag).days
    if zeitraum < 0:
        raise ValueError(
            "Der letzte CSV-Buchungstag liegt in der Zukunft."
        )
    if zeitraum > 90:
        raise ValueError(
            f"Seit dem letzten CSV-Buchungstag sind {zeitraum} Tage "
            "vergangen. Bitte zuerst aktuelle CSV-Daten importieren."
        )

    # Zugangsdaten aus der .env-Datei
    client = create_client(
        os.environ["ING_ZUGANG"],
        os.environ["ING_PIN"],
    )

    with client:
        complete_tan(client)

        accounts = get_accounts(client)
        if not accounts:
            raise ValueError("FinTS hat keine Konten geliefert.")

        # Wie im erfolgreichen Test: erstes Konto ist das Girokonto.
        girokonto = accounts[0]
        girokonto_iban = str(girokonto.iban)

        fints_df = get_transactions_dataframe(
            client,
            [girokonto],
            letzter_csv_tag,
            heute,
        )

        balances = fints_df.attrs.get("balances", {})

    # Den bereits getesteten Abgleich verwenden.
    gemeinsames_df, saldo_berechnet, saldo_fints = abgleichen(
        csv_df=csv_df,
        fints_df=fints_df,
        balances=balances,
        konto_iban=girokonto_iban,
    )

    # Metadaten auch für die neu hinzugefügten FinTS-Buchungen erzeugen.
    gemeinsames_df = add_metaData(gemeinsames_df)

    info = {
        "letzter_csv_tag": letzter_csv_tag,
        "saldo_berechnet": saldo_berechnet,
        "saldo_fints": saldo_fints,
        "konto_iban": girokonto_iban,
    }

    return gemeinsames_df, info

if number_imported > 0:
    load_data.clear()
    st.session_state.pop("gemeinsames_df", None)
    st.session_state.pop("fints_info", None)


def main():
    st.title("Finanzanalyse")
    st.caption("Einnahmen, Ausgaben und finanzielle Entwicklung")

    # CSV-Daten laden
    csv_df = load_data()

    if csv_df.empty:
        st.warning("Keine Buchungen gefunden.")
        return

    # Beim ersten Aufruf zunächst die CSV-Historie anzeigen.
    if "gemeinsames_df" not in st.session_state:
        st.session_state["gemeinsames_df"] = csv_df.copy()

    # FinTS nur auf ausdrücklichen Wunsch aktualisieren.
    if st.button("FinTS-Daten aktualisieren", type="primary"):
        try:
            with st.spinner("FinTS-Buchungen werden geladen und abgeglichen …"):
                gemeinsames_df, info = load_combined_data(csv_df)

            st.session_state["gemeinsames_df"] = gemeinsames_df
            st.session_state["fints_info"] = info

            st.success("CSV- und FinTS-Daten wurden abgeglichen.")

        except Exception as e:
            st.error(f"FinTS-Aktualisierung fehlgeschlagen: {e}")

    # Ab hier verwenden wir den gemeinsamen DataFrame.
    df = st.session_state["gemeinsames_df"]

    # Datenquelle und Übergangsdatum anzeigen
    info = st.session_state.get("fints_info")

    if info:
        letzter_csv_tag = info["letzter_csv_tag"]
        st.caption(
            f"CSV-Historie bis {letzter_csv_tag:%d.%m.%Y} · "
            f"FinTS-Daten ab {letzter_csv_tag:%d.%m.%Y}"
        )
    else:
        letzter_csv_tag = pd.to_datetime(csv_df["buchung"]).max().date()
        st.caption(
            f"CSV-Historie bis {letzter_csv_tag:%d.%m.%Y} · "
            "FinTS noch nicht aktualisiert"
        )

    # Kontrolle: aktueller Datenbestand
    st.write(f"Anzahl Buchungen: {len(df)}")

    # Ab hier folgen deine bisherigen Filter und Tabs.
    # Sie können jetzt den gemeinsamen DataFrame df verwenden.

    # ------------------------------------------------------------
    # Gemeinsame Filter: Jahr und Monat
    # ------------------------------------------------------------

    jahre = sorted(
        df["buchung"].dt.year.unique(),
        reverse=True,
    )

    col_jahr, col_monat = st.columns(2)

    with col_jahr:
        jahr = st.selectbox("Jahr", jahre)

    monat_namen = [
        "Alle Monate",
        "Januar",
        "Februar",
        "März",
        "April",
        "Mai",
        "Juni",
        "Juli",
        "August",
        "September",
        "Oktober",
        "November",
        "Dezember",
    ]

    with col_monat:
        monat_name = st.selectbox("Monat", monat_namen)

    # ------------------------------------------------------------
    # Daten für die aktuelle Auswahl und das gesamte Jahr
    # ------------------------------------------------------------

    jahresdaten = df.loc[
        df["buchung"].dt.year == jahr
    ].copy()

    auswahl = jahresdaten.copy()

    if monat_name != "Alle Monate":
        monat_nummer = monat_namen.index(monat_name)

        auswahl = auswahl.loc[
            auswahl["buchung"].dt.month == monat_nummer
        ]

    # ------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------

    tab_uebersicht, tab_kategorien, tab_ausgaben, tab_einnahmen, tab_buchungen = st.tabs(
    ["Übersicht", "Kategorien", "Ausgaben", "Einnahmen", "Buchungen"]
    )

    with tab_uebersicht:
        if "gemeinsames_df" in st.session_state:
            zeige_letzte_fints_buchungen(
                st.session_state["gemeinsames_df"]
            )
        zeige_uebersicht(auswahl, monat_name, jahr)

    with tab_kategorien:
        zeige_kategorien(auswahl, jahresdaten, monat_name, jahr)

    with tab_ausgaben:
        zeige_ausgaben(auswahl, jahresdaten, monat_name, jahr)

    with tab_einnahmen:
        zeige_einnahmen(auswahl, jahresdaten, monat_name, jahr)

    with tab_buchungen:
        zeige_buchungen(auswahl, jahresdaten, monat_name, jahr)


if __name__ == "__main__":
    main()
