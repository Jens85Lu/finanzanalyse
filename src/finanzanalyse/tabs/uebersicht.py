
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from finanzanalyse.analyse import monthly_summary


def complete_months(summary, perioden):
    """Alle gewünschten Monate ergänzen, auch ohne Buchungen."""

    if "monat" not in summary.columns:
        if summary.index.name == "monat":
            summary = summary.reset_index()
        else:
            raise ValueError(
                f"'monat' fehlt. Spalten: {list(summary.columns)}, "
                f"Indexname: {summary.index.name!r}"
            )

    if summary.empty:
        return pd.DataFrame({
            "monat": perioden,
            "einnahmen": 0.0,
            "ausgaben": 0.0,
            "differenz": 0.0,
        })

    summary = summary.copy()
    summary["monat"] = pd.PeriodIndex(
        summary["monat"].astype(str),
        freq="M",
    )

    return (
        summary.set_index("monat")
        .reindex(perioden, fill_value=0)
        .rename_axis("monat")
        .reset_index()
    )


def format_euro(value):
    """Zahlen im deutschen Euroformat anzeigen."""
    return (
        f"{value:,.2f} €"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def zeige_uebersicht(auswahl, monat_name, jahr):
    """Kennzahlen und Diagramme der Übersichtsseite."""

    einnahmen = auswahl.loc[
        auswahl["betrag"] > 0, "betrag"
    ].sum()

    ausgaben = -auswahl.loc[
        auswahl["betrag"] < 0, "betrag"
    ].sum()

    bilanz = einnahmen - ausgaben

    st.subheader(f"Übersicht: {monat_name} {jahr}")

    c1, c2, c3 = st.columns(3)

    c1.metric("Einnahmen", format_euro(einnahmen))
    c2.metric("Ausgaben", format_euro(ausgaben))
    c3.metric("Bilanz", format_euro(bilanz))

    # ------------------------------------------------------------
    # Monatsdaten für das linke Diagramm
    # ------------------------------------------------------------

    if monat_name == "Alle Monate":
        perioden = pd.period_range(
            f"{jahr}-01",
            f"{jahr}-12",
            freq="M",
        )
    else:
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

        monat_nummer = monat_namen.index(monat_name)

        perioden = pd.period_range(
            f"{jahr}-{monat_nummer:02d}",
            f"{jahr}-{monat_nummer:02d}",
            freq="M",
        )

    monthly_auswahl = complete_months(
        monthly_summary(auswahl),
        perioden,
    )

    plot_df = monthly_auswahl.copy()
    plot_df["monat"] = plot_df["monat"].astype(str)

    # Ausgaben für die Balkendarstellung positiv anzeigen
    plot_df["ausgaben_anzeige"] = -plot_df["ausgaben"]

    col_1, col_2 = st.columns(2)

    # Einnahmen, Ausgaben und Bilanz
    with col_1:
        fig = go.Figure()

        fig.add_bar(
            x=plot_df["monat"],
            y=plot_df["einnahmen"],
            name="Einnahmen",
        )

        fig.add_bar(
            x=plot_df["monat"],
            y=plot_df["ausgaben_anzeige"],
            name="Ausgaben",
        )

        fig.add_scatter(
            x=plot_df["monat"],
            y=plot_df["differenz"],
            name="Bilanz",
            mode="lines+markers",
            line=dict(color="red", width=3),
        )

        fig.update_layout(
            title="Einnahmen, Ausgaben und Bilanz",
            barmode="group",
            height=400,
            xaxis_title="Monat",
            yaxis_title="Betrag in €",
            yaxis=dict(
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor="gray",
            ),
            legend=dict(
                orientation="h",
                y=1.12,
            ),
        )

        st.plotly_chart(
            fig,
            width='stretch',
        )

    # Kontostandsverlauf
    with col_2:
        if "saldo" in auswahl.columns:
            saldo_df = auswahl.sort_values("buchung")

            fig_saldo = go.Figure()

            fig_saldo.add_scatter(
                x=saldo_df["buchung"],
                y=saldo_df["saldo"],
                mode="lines",
                name="Kontostand",
                line=dict(width=2),
            )

            fig_saldo.update_layout(
                title="Kontostandsverlauf",
                height=400,
                xaxis_title="Buchungsdatum",
                yaxis_title="Kontostand in €",
                showlegend=False,
            )

            # X-Achse über das gesamte Jahr erstrecken
            fig_saldo.update_xaxes(
                type="date",
                range=[
                    f"{jahr}-01-01",
                    f"{jahr}-12-31",
                ],
            )

            st.plotly_chart(
                fig_saldo,
                width='stretch',
            )
        else:
            st.info(
                "Die ausgewählten Buchungen enthalten keine "
                "Spalte 'saldo'."
            )
