
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def zeige_kategorien(auswahl, jahresdaten, monat_name, jahr):
    """Kategorienvergleich und monatlicher Jahresverlauf."""

    st.subheader(f"Ausgaben nach Kategorien: {monat_name} {jahr}")

    # Nur Ausgaben des gewählten Zeitraums
    ausgaben_auswahl = auswahl.loc[
        auswahl["betrag"] < 0
    ].copy()

    ausgaben_auswahl["ausgabe"] = (
        -ausgaben_auswahl["betrag"]
    )

    # Ausgaben des gesamten Jahres
    ausgaben_jahr = jahresdaten.loc[
        jahresdaten["betrag"] < 0
    ].copy()

    ausgaben_jahr["ausgabe"] = -ausgaben_jahr["betrag"]

    kategorien_jahr = (
        ausgaben_jahr.groupby("kategorie")["ausgabe"]
        .sum()
        .sort_values(ascending=False)
    )

    kategorien_optionen = kategorien_jahr.index.tolist()

    if not kategorien_optionen:
        st.info("Für dieses Jahr liegen keine Ausgaben vor.")
        return

    # Standardmäßig die fünf größten Kategorien auswählen
    standard_kategorien = kategorien_optionen[:5]

    ausgewaehlte_kategorien = st.multiselect(
        "Kategorien auswählen",
        options=kategorien_optionen,
        default=standard_kategorien,
    )

    if not ausgewaehlte_kategorien:
        st.info("Bitte wähle mindestens eine Kategorie aus.")
        return

    # ------------------------------------------------------------
    # Oberes Diagramm: gewählter Monat oder gesamtes Jahr
    # ------------------------------------------------------------

    kategorien_auswahl = (
        ausgaben_auswahl.loc[
            ausgaben_auswahl["kategorie"].isin(
                ausgewaehlte_kategorien
            )
        ]
        .groupby("kategorie")["ausgabe"]
        .sum()
        .sort_values(ascending=True)
    )

    fig_kategorien = go.Figure()

    if not kategorien_auswahl.empty:
        fig_kategorien.add_bar(
            x=kategorien_auswahl.values,
            y=kategorien_auswahl.index,
            orientation="h",
            name="Ausgaben",
        )

    fig_kategorien.update_layout(
        title=f"Ausgaben nach Kategorie – {monat_name} {jahr}",
        height=400,
        xaxis_title="Ausgaben in €",
        yaxis_title="",
        showlegend=False,
    )

    st.plotly_chart(
        fig_kategorien,
        width='stretch',
    )

    # ------------------------------------------------------------
    # Unteres Diagramm: alle zwölf Monate des Jahres
    # ------------------------------------------------------------

    st.subheader(f"Entwicklung im Jahresverlauf {jahr}")

    perioden_jahr = pd.period_range(
        f"{jahr}-01",
        f"{jahr}-12",
        freq="M",
    )

    verlauf = ausgaben_jahr.loc[
        ausgaben_jahr["kategorie"].isin(
            ausgewaehlte_kategorien
        )
    ].copy()

    verlauf["monat"] = verlauf["buchung"].dt.to_period("M")

    monat_kategorie = (
        verlauf.groupby(["monat", "kategorie"])["ausgabe"]
        .sum()
        .unstack("kategorie", fill_value=0)
        .reindex(
            index=perioden_jahr,
            columns=ausgewaehlte_kategorien,
            fill_value=0,
        )
    )

    monat_kategorie.index = monat_kategorie.index.astype(str)

    fig_verlauf = go.Figure()

    for kategorie in ausgewaehlte_kategorien:
        fig_verlauf.add_scatter(
            x=monat_kategorie.index,
            y=monat_kategorie[kategorie],
            mode="lines+markers",
            name=kategorie,
        )

    fig_verlauf.update_layout(
        title="Monatliche Ausgaben je Kategorie",
        height=450,
        xaxis_title="Monat",
        yaxis_title="Ausgaben in €",
        hovermode="x unified",
    )

    st.plotly_chart(
        fig_verlauf,
        width='stretch',
    )
