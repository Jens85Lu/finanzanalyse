import pandas as pd
import plotly.express as px
import streamlit as st


def zeige_ausgaben(auswahl, jahresdaten, monat_name, jahr):
    """Buchungen tabellarisch und grafisch auswerten."""

    st.subheader(f"Buchungen: {monat_name} {jahr}")

    if auswahl.empty:
        st.info("Für diese Auswahl liegen keine Buchungen vor.")
        return

    # --------------------------------------------------
    # Kategorien auswählen
    # --------------------------------------------------
    kategorien_optionen = sorted(
        jahresdaten.loc[
            jahresdaten["betrag"] < 0, "kategorie"
        ].dropna().unique().tolist()
    )

    if not kategorien_optionen:
        st.info("Keine Kategorien vorhanden.")
        return

    ausgewaehlte_kategorien = st.multiselect(
        "Kategorien auswählen",
        options=kategorien_optionen,
        default=kategorien_optionen,
        key="buchungen_kategorien",
    )

    if not ausgewaehlte_kategorien:
        st.info("Bitte wähle mindestens eine Kategorie aus.")
        return

    buchungen = auswahl.loc[
        auswahl["kategorie"].isin(ausgewaehlte_kategorien)
    ].copy()

    # Fehlende optionale Spalten ergänzen
    tabellenspalten = [
        "buchung",
        "betrag",
        "auftraggeber_empfaenger",
        "verwendungszweck",
    ]

    for spalte in tabellenspalten:
        if spalte not in buchungen.columns:
            buchungen[spalte] = ""

    # Datum für Sortierung und Diagramme vereinheitlichen
    buchungen["buchung"] = pd.to_datetime(
        buchungen["buchung"],
        errors="coerce",
    )

    # Leere Empfänger kennzeichnen
    buchungen["auftraggeber_empfaenger"] = (
        buchungen["auftraggeber_empfaenger"]
        .fillna("Unbekannt")
        .replace("", "Unbekannt")
    )

    # --------------------------------------------------
    # Kennzahlen
    # --------------------------------------------------
    einnahmen = buchungen.loc[
        buchungen["betrag"] > 0, "betrag"
    ].sum()

    ausgaben = -buchungen.loc[
        buchungen["betrag"] < 0, "betrag"
    ].sum()

    saldo = buchungen["betrag"].sum()

    ausgaben_df = buchungen.loc[
            buchungen["betrag"] < 0
        ].copy()

    ausgaben_pro_monat = (
        ausgaben_df
        .groupby(ausgaben_df["buchung"].dt.to_period("M"))["betrag"]
        .sum()
    )

    durchschnitt_monat = (
        ausgaben_pro_monat.mean()
        if not ausgaben_pro_monat.empty
        else 0.0
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Buchungen", len(buchungen.loc[buchungen["betrag"]<0]))
    c2.metric("Ausgaben", format_euro(ausgaben))
    c3.metric("Monatsdurchschnitt", format_euro(durchschnitt_monat))
   

    # --------------------------------------------------
    # Datengrundlage für beide Diagramme:
    # Nur Ausgaben, als positive Werte dargestellt
    # --------------------------------------------------
    vergleich = buchungen.loc[
        buchungen["betrag"] < 0
    ].copy()

    vergleich["ausgaben"] = -vergleich["betrag"]

    if vergleich.empty:
        st.info("Für die ausgewählten Kategorien gibt es keine Ausgaben.")
    else:
        # ----------------------------------------------
        # Diagramm 1: Horizontale Balken nach Empfänger
        # ----------------------------------------------
        st.subheader("1. Ausgaben nach Auftraggeber / Empfänger")

        empfaenger_summe = (
            vergleich.groupby(
                ["auftraggeber_empfaenger", "kategorie"],
                as_index=False,
                dropna=False,
            )["ausgaben"]
            .sum()
        )

        # Die 15 größten Empfänger anhand ihrer Gesamtausgaben
        top_empfaenger = (
            empfaenger_summe.groupby(
                "auftraggeber_empfaenger"
            )["ausgaben"]
            .sum()
            .nlargest(15)
            .index
        )

        empfaenger_summe = empfaenger_summe.loc[
            empfaenger_summe["auftraggeber_empfaenger"].isin(
                top_empfaenger
            )
        ].sort_values("ausgaben", ascending=True)

        fig_empfaenger = px.bar(
            empfaenger_summe,
            x="ausgaben",
            y="auftraggeber_empfaenger",
            color="kategorie",
            orientation="h",
            barmode="stack",
            labels={
                "ausgaben": "Ausgaben in €",
                "auftraggeber_empfaenger": "Auftraggeber / Empfänger",
                "kategorie": "Kategorie",
            },
            title=(
                "Die 15 Empfänger mit den höchsten Ausgaben "
                "in den gewählten Kategorien"
            ),
            hover_data={
                "auftraggeber_empfaenger": True,
                "kategorie": True,
                "ausgaben": ":.2f",
            },
        )

        fig_empfaenger.update_layout(
            height=500,
            xaxis_title="Ausgaben in €",
            yaxis_title="",
            legend_title="Kategorie",
            hovermode="closest",
        )

        st.plotly_chart(
            fig_empfaenger,
            width='stretch',
        )

        # ----------------------------------------------
        # Diagramm 2: Monatlicher Vergleich der Empfänger
        # ----------------------------------------------
        st.subheader("2. Monatlicher Vergleich der Empfänger")

        monatsnamen = [
            "Januar", "Februar", "März", "April",
            "Mai", "Juni", "Juli", "August",
            "September", "Oktober", "November", "Dezember",
        ]

        vergleich = vergleich.dropna(
            subset=["buchung"]
        ).copy()

        vergleich["monat_nummer"] = vergleich["buchung"].dt.month
        vergleich["monat"] = vergleich["monat_nummer"].map(
            lambda m: monatsnamen[m - 1]
        )

        # Empfänger und Kategorien je Monat zusammenfassen
        monat_empfaenger = (
            vergleich.groupby(
                [
                    "monat_nummer",
                    "monat",
                    "auftraggeber_empfaenger",
                    "kategorie",
                ],
                as_index=False,
                dropna=False,
            )["ausgaben"]
            .sum()
        )

        # X-Achse abhängig von der Auswahl festlegen
        if monat_name == "Alle Monate":
            x_monate = monatsnamen
            diagramm_titel = f"Empfängervergleich im Jahr {jahr}"

            # Alle Monate in den Daten ergänzen
            vorhandene_empfaenger = monat_empfaenger[
                ["auftraggeber_empfaenger", "kategorie"]
            ].drop_duplicates()

            alle_monate = pd.DataFrame({
                "monat": monatsnamen,
                "monat_nummer": range(1, 13),
            })

            # Jede Empfänger-Kategorie-Kombination mit allen
            # zwölf Monaten kombinieren.
            monat_empfaenger = (
                vorhandene_empfaenger.merge(
                    alle_monate,
                    how="cross",
                )
                .merge(
                    monat_empfaenger[
                        [
                            "monat_nummer",
                            "auftraggeber_empfaenger",
                            "kategorie",
                            "ausgaben",
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

            monat_empfaenger["ausgaben"] = (
                monat_empfaenger["ausgaben"].fillna(0)
            )

        else:
            x_monate = [monat_name]
            diagramm_titel = (
                f"Empfängervergleich – {monat_name} {jahr}"
            )

        fig_monate = px.bar(
            monat_empfaenger,
            x="monat",
            y="ausgaben",
            color="auftraggeber_empfaenger",
            barmode="group",
            category_orders={"monat": x_monate},
            labels={
                "monat": "Monat",
                "ausgaben": "Ausgaben in €",
                "auftraggeber_empfaenger": "Auftraggeber / Empfänger",
                "kategorie": "Kategorie",
            },
            title=diagramm_titel,
            hover_data={
                "monat_nummer": False,
                "monat": True,
                "auftraggeber_empfaenger": True,
                "kategorie": True,
                "ausgaben": ":.2f",
            },
        )

        fig_monate.update_layout(
            height=600,
            xaxis_title="Monat",
            yaxis_title="Ausgaben in €",
            legend_title="Auftraggeber / Empfänger",
            hovermode="closest",
        )

        # Die X-Achse zeigt alle zwölf Monate in fester Reihenfolge.
        # Fehlende Monate bleiben sichtbar, auch ohne Buchungen.
        fig_monate.update_xaxes(
            type="category",
            categoryorder="array",
            categoryarray=x_monate,
        )

        st.plotly_chart(
            fig_monate,
            width='stretch',
        )


        # ----------------------------------------------
        # Diagramm 3: Kumulierte Ausgaben je Empfänger
        # ----------------------------------------------
        st.subheader("3. Kumulierte Ausgaben je Empfänger")

        # Daten des gesamten ausgewählten Jahres verwenden
        verlauf = jahresdaten.loc[
            (jahresdaten["betrag"] < 0)
            & jahresdaten["kategorie"].isin(
                ausgewaehlte_kategorien
            )
        ].copy()

        verlauf["buchung"] = pd.to_datetime(
            verlauf["buchung"],
            errors="coerce",
        )
        verlauf = verlauf.dropna(subset=["buchung"])

        verlauf["auftraggeber_empfaenger"] = (
            verlauf["auftraggeber_empfaenger"]
            .fillna("Unbekannt")
            .replace("", "Unbekannt")
        )
        verlauf["ausgaben"] = -verlauf["betrag"]
        verlauf["monat"] = verlauf["buchung"].dt.to_period("M")

        perioden = pd.period_range(
            f"{jahr}-01",
            f"{jahr}-12",
            freq="M",
        )

        monat_empfaenger_summe = (
            verlauf.groupby(["monat", "auftraggeber_empfaenger"])[
                "ausgaben"
            ]
            .sum()
            .unstack("auftraggeber_empfaenger", fill_value=0)
            .reindex(index=perioden, fill_value=0)
        )

        # Auf Wunsch nur die 15 größten Empfänger darstellen
        top_empfaenger = (
            monat_empfaenger_summe.sum()
            .nlargest(15)
            .index
        )
        monat_empfaenger_summe = monat_empfaenger_summe[
            top_empfaenger
        ]

        kumuliert = monat_empfaenger_summe.cumsum()
        kumuliert.index = kumuliert.index.astype(str)

        fig_kumuliert = px.line(
            kumuliert,
            markers=True,
            labels={
                "index": "Monat",
                "value": "Kumulierte Ausgaben in €",
                "variable": "Empfänger",
            },
            title="Kumulierte Ausgaben der 15 größten Empfänger",
        )

        fig_kumuliert.update_layout(
            height=550,
            xaxis_title="Monat",
            yaxis_title="Kumulierte Ausgaben in €",
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
