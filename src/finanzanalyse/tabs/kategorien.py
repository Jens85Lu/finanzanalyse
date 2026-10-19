import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def zeige_kategorien(auswahl, jahresdaten, monat_name, jahr):
    """Kategorienvergleich anhand der Nettobelastung."""

    st.subheader(f"Nettobelastung nach Kategorien: {monat_name} {jahr}")

    # ------------------------------------------------------------
    # Datengrundlage: alle Buchungen des Jahres
    # ------------------------------------------------------------

    jahresdaten = jahresdaten.copy()

    jahresdaten["buchung"] = pd.to_datetime(
        jahresdaten["buchung"],
        errors="coerce",
    )

    # Positive Werte = Belastung, negative Werte = Erstattung
    jahresdaten["nettobelastung"] = -jahresdaten["betrag"]

    kategorien_jahr = (
        jahresdaten.groupby("kategorie")["nettobelastung"]
        .sum()
        .sort_values(ascending=False)
    )

    kategorien_optionen = kategorien_jahr.index.tolist()

    if not kategorien_optionen:
        st.info("Für dieses Jahr liegen keine Buchungen vor.")
        return

    ausgewaehlte_kategorien = st.multiselect(
        "Kategorien auswählen",
        options=kategorien_optionen,
        default=kategorien_optionen,
        key="kategorien_vergleich",
    )

    if not ausgewaehlte_kategorien:
        st.info("Bitte wähle mindestens eine Kategorie aus.")
        return

    #----------------------------------------------------------------
    # Übersicht: Einnahmen, Ausgaben, Bilanz für gewählte Kategorien
    # ----------------------------------------------------------------

    buchungen_kategorien = (
            auswahl.loc[
                auswahl["kategorie"].isin(ausgewaehlte_kategorien)
            ]
    )

    einnahmen = buchungen_kategorien.loc[
        buchungen_kategorien["betrag"] > 0, "betrag"].sum()

    ausgaben = -buchungen_kategorien.loc[
        buchungen_kategorien["betrag"] < 0, "betrag"].sum()

    nettobelastung = ausgaben - einnahmen

    st.subheader(f"Übersicht: {monat_name} {jahr}")

    c1, c2, c3 = st.columns(3)

    c1.metric("Einnahmen", format_euro(einnahmen))
    c2.metric("Ausgaben", format_euro(ausgaben))
    c3.metric("Nettobelastung", format_euro(nettobelastung))

    # ------------------------------------------------------------
    # Diagramm 1: Nettobelastung im gewählten Zeitraum
    # ------------------------------------------------------------

    kategorien_auswahl = (
        auswahl.loc[
            auswahl["kategorie"].isin(ausgewaehlte_kategorien)
        ]
        .groupby("kategorie")["betrag"]
        .sum()
        .mul(-1)
        .sort_values(ascending=True)
    )

    fig_kategorien = go.Figure()

    if not kategorien_auswahl.empty:
        fig_kategorien.add_bar(
            x=kategorien_auswahl.values,
            y=kategorien_auswahl.index,
            orientation="h",
            name="Nettobelastung",
        )

    fig_kategorien.update_layout(
        title=f"Nettobelastung nach Kategorie – {monat_name} {jahr}",
        height=400,
        xaxis_title="Nettobelastung in €",
        yaxis_title="",
        showlegend=False,
    )

    st.plotly_chart(
        fig_kategorien,
        width='stretch',
    )

    # ------------------------------------------------------------
    # Diagramm 2: Monatliche Nettobelastung je Kategorie
    # ------------------------------------------------------------

    st.subheader(f"Entwicklung im Jahresverlauf {jahr}")

    perioden_jahr = pd.period_range(
        f"{jahr}-01",
        f"{jahr}-12",
        freq="M",
    )

    verlauf = jahresdaten.loc[
        jahresdaten["kategorie"].isin(ausgewaehlte_kategorien)
    ].copy()

    verlauf = verlauf.dropna(subset=["buchung"])
    verlauf["monat"] = verlauf["buchung"].dt.to_period("M")

    monat_kategorie = (
        verlauf.groupby(["monat", "kategorie"])["nettobelastung"]
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
        fig_verlauf.add_bar(
            x=monat_kategorie.index,
            y=monat_kategorie[kategorie],
            name=kategorie,
        )

    fig_verlauf.update_layout(
        title="Monatliche Nettobelastung je Kategorie",
        height=450,
        xaxis_title="Monat",
        yaxis_title="Nettobelastung in €",
        barmode="group",
        hovermode="x unified",
    )

    st.plotly_chart(
        fig_verlauf,
        width='stretch',
    )

    # ------------------------------------------------------------
    # Diagramm 3: Kumulierte Nettobelastung je Kategorie
    # ------------------------------------------------------------

    st.subheader("Kumulierte Nettobelastung im Jahresverlauf")

    kumuliert = monat_kategorie.cumsum()

    fig_kumuliert = go.Figure()

    for kategorie in ausgewaehlte_kategorien:
        fig_kumuliert.add_scatter(
            x=kumuliert.index,
            y=kumuliert[kategorie],
            mode="lines+markers",
            name=kategorie,
        )

    fig_kumuliert.update_layout(
        title="Kumulierte Nettobelastung je Kategorie",
        height=500,
        xaxis_title="Monat",
        yaxis_title="Kumulierte Nettobelastung in €",
        hovermode="x unified",
    )

    st.plotly_chart(
        fig_kumuliert,
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