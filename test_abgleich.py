
from datetime import date

from dotenv import load_dotenv

from finanzanalyse.fints_import import (
    create_client,
    complete_tan,
    get_accounts,
    get_transactions_dataframe,
)
from finanzanalyse.database import load_transactions
from finanzanalyse.abgleich import abgleichen


load_dotenv()


def main():
    # 1. Historische CSV-Daten laden
    csv_df = load_transactions(
        "2000-01-01",
        "2100-01-01",
    )

    if csv_df.empty:
        print("Die CSV-Historie ist leer.")
        return

    letzter_csv_tag = csv_df["buchung"].max().date()
    heute = date.today()

    print(f"Letzter CSV-Buchungstag: {letzter_csv_tag}")

    if (heute - letzter_csv_tag).days > 90:
        print(
            "Die CSV-Historie endet mehr als 90 Tage zurück. "
            "Der FinTS-Zeitraum muss aufgeteilt werden."
        )
        return

    # 2. FinTS-Verbindung aufbauen
    import os

    client = create_client(
        os.environ["ING_ZUGANG"],
        os.environ["ING_PIN"],
    )

    with client:
        complete_tan(client)
        accounts = get_accounts(client)

        if not accounts:
            print("Es wurden keine Konten gefunden.")
            return

        # Das erste Konto ist unser Girokonto.
        girokonto = accounts[0]
        girokonto_iban = str(girokonto.iban)

        print(f"Verwendetes Konto: {girokonto_iban}")
        print(
            f"Lade FinTS-Buchungen von {letzter_csv_tag} "
            f"bis {heute} ..."
        )

        # 3. FinTS ab dem letzten CSV-Buchungstag abrufen
        fints_df = get_transactions_dataframe(
            client,
            [girokonto],
            letzter_csv_tag,
            heute,
        )

        balances = fints_df.attrs.get("balances", {})

    print(f"\nCSV-Buchungen: {len(csv_df)}")
    print(f"FinTS-Buchungen: {len(fints_df)}")

    # 4. Übergangsdaten zur Fehlersuche anzeigen
    print("\nLetzte CSV-Buchungen:")
    print(csv_df.tail(5).to_string(index=False))

    print("\nFinTS-Salden:")
    print(balances.get(girokonto_iban, "Keine Salden vorhanden"))

    # 5. Abgleich durchführen
    anzeige_df, saldo_berechnet, saldo_fints = abgleichen(
        csv_df=csv_df,
        fints_df=fints_df,
        balances=balances,
        konto_iban=girokonto_iban,
    )

    # 6. Ergebnis anzeigen
    print("\nLetzte Buchungen des gemeinsamen DataFrames:")
    print(anzeige_df.tail(10).to_string(index=False))

    print("\nZusammenfassung")
    print("----------------")
    print(f"CSV-Buchungen:     {len(csv_df)}")
    print(f"FinTS-Buchungen:   {len(fints_df)}")
    print(f"Anzeige-Buchungen: {len(anzeige_df)}")
    print(f"Berechneter Saldo: {saldo_berechnet:.2f} €")
    print(f"FinTS-Endsaldo:    {saldo_fints:.2f} €")
    print("Saldo korrekt:", saldo_berechnet == saldo_fints)


if __name__ == "__main__":
    main()
