
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd


def geld(wert):
    """Geldbetrag auf zwei Nachkommastellen bringen."""
    if hasattr(wert, "amount"):
        wert = wert.amount
    if hasattr(wert, "amount"):
        wert = wert.amount

    return Decimal(str(wert)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def abgleichen(csv_df, fints_df, balances, konto_iban):
    """CSV-Historie und aktuelle FinTS-Buchungen verbinden."""

    if csv_df.empty:
        raise ValueError("Die CSV-Historie ist leer.")

    if konto_iban not in balances:
        raise ValueError(f"Keine FinTS-Salden für {konto_iban} gefunden.")

    # CSV chronologisch sortieren.
    csv = csv_df.copy()
    csv["buchung"] = pd.to_datetime(csv["buchung"])
    csv["betrag"] = csv["betrag"].map(geld)
    csv["saldo"] = csv["saldo"].map(geld)

    sortierung = ["buchung"]
    if "id" in csv.columns:
        sortierung.append("id")

    csv = csv.sort_values(sortierung, kind="stable").reset_index(drop=True)

    # Letzten CSV-Buchungstag und den vorherigen Buchungstag finden.
    letzter_tag = csv["buchung"].max().normalize()
    vorherige_tage = csv.loc[
        csv["buchung"].dt.normalize() < letzter_tag, "buchung"
    ]

    if vorherige_tage.empty:
        raise ValueError(
            "Es gibt keinen CSV-Buchungstag vor dem Übergangstag."
        )

    vortag = vorherige_tage.max().normalize()

    # Letzten CSV-Saldo des Vortages verwenden.
    csv_vortag = csv[
        csv["buchung"].dt.normalize() == vortag
    ]
    saldo_csv = csv_vortag.iloc[-1]["saldo"]

    # FinTS-Anfangs- und Endsaldo auslesen.
    saldo_info = balances[konto_iban]
    saldo_anfang = geld(saldo_info["opening"])
    saldo_ende = geld(saldo_info["closing"])

    print(f"CSV-Vortag:          {vortag.date()}")
    print(f"CSV-Übergangstag:    {letzter_tag.date()}")
    print(f"Letzter CSV-Saldo:   {saldo_csv:.2f} €")
    print(f"FinTS-Anfangssaldo:  {saldo_anfang:.2f} €")

    if saldo_csv != saldo_anfang:
        raise ValueError(
            "Der CSV-Saldo des Vortages stimmt nicht mit "
            "dem FinTS-Anfangssaldo überein."
        )

    # CSV-Buchungen des Übergangstages verwerfen.
    anzeige_df = csv[
        csv["buchung"].dt.normalize() < letzter_tag
    ].copy()

    # FinTS-Buchungen des Girokontos auswählen.
    fints = fints_df[
        fints_df["konto_iban"].astype(str) == str(konto_iban)
    ].copy()

    if fints.empty:
        raise ValueError("FinTS hat keine Buchungen für das Konto geliefert.")

    fints["buchung"] = pd.to_datetime(fints["buchung"])
    fints["betrag"] = fints["betrag"].map(geld)
    fints = fints.sort_values("buchung", kind="stable")

    # FinTS-Buchungen anhängen und den laufenden Saldo berechnen.
    saldo = saldo_anfang
    neue_zeilen = []

    for _, buchung in fints.iterrows():
        saldo += buchung["betrag"]

        zeile = {spalte: None for spalte in anzeige_df.columns}
        zeile["buchung"] = buchung["buchung"]
        zeile["betrag"] = buchung["betrag"]
        zeile["saldo"] = saldo

        for spalte in (
            "wertstellungsdatum",
            "auftraggeber_empfaenger",
            "verwendungszweck",
        ):
            if spalte in zeile and spalte in buchung.index:
                zeile[spalte] = buchung[spalte]

        neue_zeilen.append(zeile)

    fints_anzeige = pd.DataFrame(
        neue_zeilen, columns=anzeige_df.columns
    )

    anzeige_df["datenquelle"] = "CSV"
    fints_anzeige["datenquelle"] = "FinTS"

    anzeige_df = pd.concat(
        [anzeige_df, fints_anzeige], ignore_index=True
    )

    # Geldwerte in normale Zahlen für die Anzeige umwandeln.
    anzeige_df["betrag"] = anzeige_df["betrag"].map(float)
    anzeige_df["saldo"] = anzeige_df["saldo"].map(float)

    # Berechneten Saldo mit dem FinTS-Endsaldo vergleichen.
    print(f"Berechneter Endsaldo: {saldo:.2f} €")
    print(f"FinTS-Endsaldo:       {saldo_ende:.2f} €")
    print(f"Saldo korrekt:        {saldo == saldo_ende}")

    if saldo != saldo_ende:
        print("WARNUNG: Die Endsalden stimmen nicht überein.")

    return anzeige_df, saldo, saldo_ende
