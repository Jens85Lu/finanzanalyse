import pandas as pd
import streamlit as st


def zeige_buchungen(auswahl, jahresdaten, monat_name, jahr):
    """Alle Einnahmen und Ausgaben nach Kategorie anzeigen."""

    st.subheader(f"Buchungen: {monat_name} {jahr}")

    if auswahl.empty:
        st.info("Für diese Auswahl liegen keine Buchungen vor.")
        return

    # --------------------------------------------------
    # Kategorien auswählen
    # --------------------------------------------------
    kategorien_optionen = sorted(
        auswahl["kategorie"].dropna().unique().tolist()
    )

    if not kategorien_optionen:
        st.info("Keine Kategorien vorhanden.")
        return

    ausgewaehlte_kategorien = st.multiselect(
        "Kategorien auswählen",
        options=kategorien_optionen,
        default=kategorien_optionen,
        key="alle_buchungen_kategorien",
    )

    if not ausgewaehlte_kategorien:
        st.info("Bitte wähle mindestens eine Kategorie aus.")
        return

    buchungen = auswahl.loc[
        auswahl["kategorie"].isin(ausgewaehlte_kategorien)
    ].copy()

    # --------------------------------------------------
    # Benötigte Spalten sicherstellen
    # --------------------------------------------------
    tabellenspalten = [
        "buchung",
        "betrag",
        "auftraggeber_empfaenger",
        "verwendungszweck",
    ]

    for spalte in tabellenspalten:
        if spalte not in buchungen.columns:
            buchungen[spalte] = ""

    buchungen["buchung"] = pd.to_datetime(
        buchungen["buchung"],
        errors="coerce",
    )

    # --------------------------------------------------
    # Gesamtkennzahlen
    # --------------------------------------------------
    einnahmen = buchungen.loc[
        buchungen["betrag"] > 0, "betrag"
    ].sum()

    ausgaben = -buchungen.loc[
        buchungen["betrag"] < 0, "betrag"
    ].sum()

    saldo = buchungen["betrag"].sum()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Buchungen", len(buchungen))
    c2.metric("Einnahmen", format_euro(einnahmen))
    c3.metric("Ausgaben", format_euro(ausgaben))
    c4.metric("Saldo", format_euro(saldo))

    # --------------------------------------------------
    # Tabellen nach Kategorie
    # --------------------------------------------------
    st.subheader("Einzelne Buchungen")

    for kategorie in ausgewaehlte_kategorien:
        daten = buchungen.loc[
            buchungen["kategorie"] == kategorie
        ].copy()

        daten = daten.sort_values(
            "buchung",
            ascending=False,
            na_position="last",
        )

        einnahmen_kat = daten.loc[
            daten["betrag"] > 0, "betrag"
        ].sum()

        ausgaben_kat = -daten.loc[
            daten["betrag"] < 0, "betrag"
        ].sum()

        saldo_kat = daten["betrag"].sum()

        with st.expander(
            f"{kategorie} · {len(daten)} Buchungen",
            expanded=True,
        ):
            st.caption(
                f"Einnahmen: {format_euro(einnahmen_kat)} · "
                f"Ausgaben: {format_euro(ausgaben_kat)} · "
                f"Saldo: {format_euro(saldo_kat)}"
            )

            anzeige = daten[tabellenspalten].copy()

            anzeige["buchung"] = (
                anzeige["buchung"].dt.strftime("%d.%m.%Y")
            )

            anzeige = anzeige.rename(
                columns={
                    "buchung": "Buchung",
                    "betrag": "Betrag (€)",
                    "auftraggeber_empfaenger": (
                        "Auftraggeber / Empfänger"
                    ),
                    "verwendungszweck": "Verwendungszweck",
                }
            )

            st.dataframe(
                anzeige,
                width='stretch',
                hide_index=True,
            )


def format_euro(value):
    """Zahlen im deutschen Euroformat darstellen."""
    return (
        f"{value:,.2f} €"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
