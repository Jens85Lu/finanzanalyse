
import pandas as pd
import plotly.express as px
import streamlit as st


def zeige_einnahmen(auswahl, jahresdaten, monat_name, jahr):
    """Einnahmen tabellarisch und grafisch auswerten."""

    st.subheader(f"Einnahmen: {monat_name} {jahr}")

    if auswahl.empty:
        st.info("Für diese Auswahl liegen keine Buchungen vor.")
        return

    # --------------------------------------------------
    # Kategorien auswählen
    # --------------------------------------------------
    kategorien_optionen = sorted(
        jahresdaten.loc[
            jahresdaten["betrag"] > 0, "kategorie"
        ].dropna().unique().tolist()
    )

    if not kategorien_optionen:
        st.info("Keine Kategorien vorhanden.")
        return

    ausgewaehlte_kategorien = st.multiselect(
        "Kategorien auswählen",
        options=kategorien_optionen,
        default=kategorien_optionen,
        key="einnahmen_kategorien",
    )

    if not ausgewaehlte_kategorien:
        st.info("Bitte wähle mindestens eine Kategorie aus.")
        return

    buchungen = auswahl.loc[
        auswahl["kategorie"].isin(ausgewaehlte_kategorien)
    ].copy()

    # Fehlende Spalten ergänzen
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

    buchungen["auftraggeber_empfaenger"] = (
        buchungen["auftraggeber_empfaenger"]
        .fillna("Unbekannt")
        .replace("", "Unbekannt")
    )

    # --------------------------------------------------
    # Kennzahlen für alle ausgewählten Buchungen
    # --------------------------------------------------
    einnahmen = buchungen.loc[
        buchungen["betrag"] > 0, "betrag"
    ].sum()

    ausgaben = -buchungen.loc[
        buchungen["betrag"] < 0, "betrag"
    ].sum()

    einnahmen_df = buchungen.loc[
        buchungen["betrag"] > 0
    ].copy()

    anzahl_einnahmen = len(einnahmen_df)

    durchschnitt = (
        einnahmen_df["betrag"].mean()
        if anzahl_einnahmen > 0
        else 0.0
    )

    einnahmen_pro_monat = (
        einnahmen_df
        .groupby(einnahmen_df["buchung"].dt.to_period("M"))["betrag"]
        .sum()
    )

    durchschnitt_monat = (
        einnahmen_pro_monat.mean()
        if not einnahmen_pro_monat.empty
        else 0.0
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Zahlungseingänge", anzahl_einnahmen)
    c2.metric("Einnahmen", format_euro(einnahmen))
    c3.metric("Monatsdurchschnitt", format_euro(durchschnitt_monat))
    #c3.metric("Durchschnitt", format_euro(durchschnitt))


    # --------------------------------------------------
    # Datengrundlage: positive Buchungen
    # --------------------------------------------------
    if einnahmen_df.empty:
        st.info("Für diese Auswahl liegen keine Einnahmen vor.")
    else:
        # ----------------------------------------------
        # Diagramm 1: Einnahmen nach Auftraggeber
        # Aufteilung nach Kategorie
        # ----------------------------------------------
        st.subheader("1. Einnahmen nach Auftraggeber / Empfänger")

        auftraggeber_summe = (
            einnahmen_df.groupby(
                ["auftraggeber_empfaenger", "kategorie"],
                as_index=False,
                dropna=False,
            )["betrag"]
            .sum()
            .rename(columns={"betrag": "einnahmen"})
        )

        # Die 15 größten Auftraggeber anhand ihrer Gesamteinnahmen
        top_auftraggeber = (
            auftraggeber_summe.groupby(
                "auftraggeber_empfaenger"
            )["einnahmen"]
            .sum()
            .nlargest(15)
            .index
        )

        auftraggeber_summe = auftraggeber_summe.loc[
            auftraggeber_summe["auftraggeber_empfaenger"].isin(
                top_auftraggeber
            )
        ].sort_values("einnahmen", ascending=True)

        fig_auftraggeber = px.bar(
            auftraggeber_summe,
            x="einnahmen",
            y="auftraggeber_empfaenger",
            color="kategorie",
            orientation="h",
            barmode="stack",
            labels={
                "einnahmen": "Einnahmen in €",
                "auftraggeber_empfaenger": "Auftraggeber / Empfänger",
                "kategorie": "Kategorie",
            },
            title="Die 15 Auftraggeber mit den höchsten Einnahmen",
            hover_data={
                "auftraggeber_empfaenger": True,
                "kategorie": True,
                "einnahmen": ":.2f",
            },
        )

        fig_auftraggeber.update_layout(
            height=500,
            xaxis_title="Einnahmen in €",
            yaxis_title="",
            legend_title="Kategorie",
            hovermode="closest",
        )

        st.plotly_chart(
            fig_auftraggeber,
            width='stretch',
        )

        # ----------------------------------------------
        # Diagramm 2: Monatlicher Vergleich der Einnahmen
        # ----------------------------------------------
        st.subheader("2. Monatlicher Vergleich der Auftraggeber")

        monatsnamen = [
            "Januar", "Februar", "März", "April",
            "Mai", "Juni", "Juli", "August",
            "September", "Oktober", "November", "Dezember",
        ]

        einnahmen_df["monat_nummer"] = (
            einnahmen_df["buchung"].dt.month
        )

        einnahmen_df = einnahmen_df.dropna(
            subset=["monat_nummer"]
        ).copy()

        einnahmen_df["monat_nummer"] = (
            einnahmen_df["monat_nummer"].astype(int)
        )

        einnahmen_df["monat"] = einnahmen_df["monat_nummer"].map(
            lambda m: monatsnamen[m - 1]
        )

        monat_auftraggeber = (
            einnahmen_df.groupby(
                [
                    "monat_nummer",
                    "monat",
                    "auftraggeber_empfaenger",
                    "kategorie",
                ],
                as_index=False,
                dropna=False,
            )["betrag"]
            .sum()
            .rename(columns={"betrag": "einnahmen"})
        )

        if monat_name == "Alle Monate":
            x_monate = monatsnamen
            titel = f"Einnahmen nach Auftraggeber im Jahr {jahr}"

            # Alle vorhandenen Auftraggeber-Kategorie-Kombinationen
            vorhandene_auftraggeber = monat_auftraggeber[
                ["auftraggeber_empfaenger", "kategorie"]
            ].drop_duplicates()

            # Alle zwölf Monate erzeugen
            alle_monate = pd.DataFrame({
                "monat": monatsnamen,
                "monat_nummer": range(1, 13),
            })

            # Jede Kombination mit allen Monaten verbinden
            monat_auftraggeber = (
                vorhandene_auftraggeber.merge(
                    alle_monate,
                    how="cross",
                )
                .merge(
                    monat_auftraggeber[
                        [
                            "monat_nummer",
                            "auftraggeber_empfaenger",
                            "kategorie",
                            "einnahmen",
                        ]
                    ],
                    on=[
                        "monat_nummer",
                        "auftraggeber_empfaenger",
                        "kategorie",
                    ],
                    how="left",
                )
            )

            # Monate ohne Einnahmen mit 0 € auffüllen
            monat_auftraggeber["einnahmen"] = (
                monat_auftraggeber["einnahmen"].fillna(0)
            )

        else:
            x_monate = [monat_name]
            titel = (
                f"Einnahmen nach Auftraggeber – {monat_name} {jahr}"
            )

        fig_monate = px.bar(
            monat_auftraggeber,
            x="monat",
            y="einnahmen",
            color="auftraggeber_empfaenger",
            barmode="group",
            category_orders={"monat": x_monate},
            labels={
                "monat": "Monat",
                "einnahmen": "Einnahmen in €",
                "auftraggeber_empfaenger": "Auftraggeber / Empfänger",
                "kategorie": "Kategorie",
            },
            title=titel,
            hover_data={
                "monat_nummer": False,
                "monat": True,
                "auftraggeber_empfaenger": True,
                "kategorie": True,
                "einnahmen": ":.2f",
            },
        )

        fig_monate.update_layout(
            height=600,
            xaxis_title="Monat",
            yaxis_title="Einnahmen in €",
            legend_title="Auftraggeber / Empfänger",
            hovermode="closest",
            xaxis=dict(
                categoryorder="array",
                categoryarray=x_monate,
            ),
        )

        st.plotly_chart(
            fig_monate,
            width='stretch',
        )


def format_euro(value):
    """Zahlen im deutschen Euroformat darstellen."""
    return (
        f"{value:,.2f} €"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
