
import streamlit as st

from finanzanalyse.database import load_transactions, create_database
from finanzanalyse.analyse import add_metaData
from finanzanalyse.data_import import import_all_files

from finanzanalyse.tabs.uebersicht import zeige_uebersicht
from finanzanalyse.tabs.kategorien import zeige_kategorien
from finanzanalyse.tabs.ausgaben import zeige_ausgaben
from finanzanalyse.tabs.einnahmen import zeige_einnahmen
from finanzanalyse.tabs.buchungen import zeige_buchungen


st.set_page_config(
    page_title="Finanzanalyse",
    page_icon="💶",
    layout="wide",
)

create_database()
import_all_files()


@st.cache_data
def load_data():
    """Buchungen laden und vorbereiten."""
    df = load_transactions("2000-01-01", "2100-01-01")

    if df.empty:
        return df

    df["buchung"] = df["buchung"].astype("datetime64[ns]")
    return add_metaData(df)


def main():
    st.title("Finanzanalyse")
    st.caption("Einnahmen, Ausgaben und finanzielle Entwicklung")

    df = load_data()

    if df.empty:
        st.warning("Keine Buchungen gefunden.")
        return

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
