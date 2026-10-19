
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from getpass import getpass

import pandas as pd
from dotenv import load_dotenv
from fints.client import FinTS3PinTanClient, NeedTANResponse
from fints.utils import minimal_interactive_cli_bootstrap


# --------------------------------------------------
# Konfiguration
# --------------------------------------------------

load_dotenv()

BLZ = os.environ.get("ING_BLZ")
FINTS_URL = "https://fints.ing.de/fints/"
MAX_DAYS = 90


# --------------------------------------------------
# Verbindung und Anmeldung
# --------------------------------------------------

def create_client(user_id, pin, product_id=None):
    """Erzeugt einen FinTS-Client, speichert aber keine Daten."""

    if product_id is None:
        product_id = os.environ.get("ING_FINTS_PRODUCT_ID")

    if not product_id:
        raise ValueError(
            "ING_FINTS_PRODUCT_ID fehlt in der .env-Datei."
        )

    return FinTS3PinTanClient(
        BLZ,
        user_id,
        pin,
        FINTS_URL,
        product_id=product_id,
    )


def complete_tan(client):
    """Bearbeitet eine eventuell erforderliche TAN-Abfrage."""

    while isinstance(client.init_tan_response, NeedTANResponse):
        response = client.init_tan_response
        print(response.challenge)

        if response.decoupled:
            input(
                "Bitte in der Banking-App bestätigen "
                "und danach Enter drücken: "
            )
            tan = ""
        else:
            tan = getpass("TAN eingeben: ")

        client.init_tan_response = client.send_tan(
            response, tan
        )


# --------------------------------------------------
# Konten abrufen
# --------------------------------------------------

def get_accounts(client):
    """Liefert die von FinTS bereitgestellten Konten."""

    return client.get_sepa_accounts()


# --------------------------------------------------
# Transaktionen abrufen
# --------------------------------------------------

def as_date(value):
    """Wandelt date, datetime oder ISO-Datum in date um."""

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return date.fromisoformat(str(value)[:10])


def date_text(value):
    if value is None:
        return None

    return as_date(value).isoformat()


def get_counterparty(data):
    """Ermittelt einen verfügbaren Namen des Geschäftspartners."""

    return (
        data.get("applicant_name")
        or data.get("recipient_name")
        or data.get("deviate_applicant")
        or data.get("deviate_recipient")
        or ""
    )


def get_purpose(data):
    """Liefert den verfügbaren Verwendungszweck."""

    return (
        data.get("purpose")
        or data.get("additional_purpose")
        or ""
    )


def get_transactions_dataframe(
    client,
    accounts,
    start_date,
    end_date,
):
    """
    Ruft Buchungen für ein oder mehrere Konten ab.

    Parameter:
        client: angemeldeter FinTS-Client
        accounts: ein Konto oder eine Liste von Konten
        start_date: erster Tag des Zeitraums
        end_date: letzter Tag des Zeitraums

    Rückgabe:
        Pandas-DataFrame mit den Buchungen

    Es werden keine Daten in einer Datenbank gespeichert.
    """

    start_date = as_date(start_date)
    end_date = as_date(end_date)

    if end_date < start_date:
        raise ValueError(
            "Das Enddatum liegt vor dem Startdatum."
        )

    if (end_date - start_date).days > MAX_DAYS:
        raise ValueError(
            f"Der Zeitraum darf maximal {MAX_DAYS} Tage umfassen."
        )

    if not isinstance(accounts, (list, tuple)):
        accounts = [accounts]

    records = []
    balances = {}

    for account in accounts:
        transactions = client.get_transactions(
            account,
            start_date=start_date,
            end_date=end_date,
        )

        if transactions:
            statement = getattr(transactions[0], "transactions", None)

            if statement is not None:
                statement_data = statement.data

                opening = statement_data.get("final_opening_balance")
                closing = statement_data.get("final_closing_balance")

                balances[str(account.iban)] = {
                    "opening": opening,
                    "closing": closing,
                }

        for transaction in transactions:
            data = transaction.data

            booking_date = date_text(data.get("date"))

            amount_obj = data.get("amount")
            if amount_obj is None:
                continue

            amount = Decimal(str(amount_obj.amount))
            currency = getattr(amount_obj, "currency", "EUR")

            records.append({
                "konto_iban": str(account.iban),
                "buchung": booking_date,
                "wertstellungsdatum": date_text(
                    data.get("entry_date")
                ),
                "betrag": float(amount),
                "waehrung": currency,
                "auftraggeber_empfaenger": get_counterparty(data),
                "verwendungszweck": str(
                    get_purpose(data) or ""
                ).strip(),
                "buchungstext": str(
                    data.get("posting_text") or ""
                ),
            })

    columns = [
        "konto_iban",
        "buchung",
        "wertstellungsdatum",
        "betrag",
        "waehrung",
        "auftraggeber_empfaenger",
        "verwendungszweck",
        "buchungstext",
    ]

    df = pd.DataFrame(records, columns=columns)

    if not df.empty:
        df["buchung"] = pd.to_datetime(df["buchung"])
        df["wertstellungsdatum"] = pd.to_datetime(
            df["wertstellungsdatum"]
        )

        df = df.sort_values(
            ["buchung", "konto_iban"],
            ascending=[False, True],
        ).reset_index(drop=True)

        df.attrs["balances"] = balances

    return df

def get_current_balances(client, accounts):
    """Ruft die aktuellen Kontostände der Konten ab."""

    balances = []

    for account in accounts:
        balance = client.get_balance(account)

        balances.append({
            "konto_iban": str(account.iban),
            "betrag": Decimal(str(balance.amount.amount)),
            "waehrung": balance.amount.currency,
        })

    return balances


# --------------------------------------------------
# Transaktionen lesbar ausgeben
# --------------------------------------------------

def format_euro(value):
    """Formatiert einen Betrag im deutschen Zahlenformat."""

    return f"{value:,.2f} €".replace(
        ",", "X"
    ).replace(
        ".", ","
    ).replace(
        "X", "."
    )


def print_transactions(df):
    """Gibt für jedes Konto eine eigene Transaktionstabelle aus."""

    balances = df.attrs.get("balances", {})
    totalBalance = 0

    # Saldi und Gesamtsaldo ausgeben
    for iban, values in balances.items():
        print(f"\nKonto: {iban}")

        for label, key in [
            ("Anfangssaldo", "opening"),
            ("Endsaldo", "closing"),
        ]:
            balance = values.get(key)

            if balance is None:
                print(f"{label}: nicht verfügbar")
                continue

            amount = balance.amount.amount

            print(f"{label}: {format_euro(amount)}")

            if label == "Endsaldo":
                totalBalance += amount

    print(f"\nGesamtsaldo: {format_euro(totalBalance)}\n")

    # Auch bei fehlenden Buchungen die Saldi anzeigen
    if df.empty:
        print("Keine Buchungen im angegebenen Zeitraum.")
        return

    # Für jedes Konto eine separate Tabelle ausgeben
    for iban, konto_df in df.groupby("konto_iban", sort=True):
        print("\n" + "=" * 100)
        print(f"Transaktionen für Konto: {iban}")
        print("=" * 100)

        display_df = konto_df.drop(
            columns=["konto_iban"]
        ).copy()

        display_df["buchung"] = (
            display_df["buchung"].dt.strftime("%d.%m.%Y")
        )
        display_df["wertstellungsdatum"] = (
            display_df["wertstellungsdatum"]
            .dt.strftime("%d.%m.%Y")
        )
        display_df["betrag"] = (
            display_df["betrag"].map(format_euro)
        )

        display_df = display_df.rename(columns={
            "buchung": "Buchung",
            "wertstellungsdatum": "Wertstellung",
            "betrag": "Betrag",
            "waehrung": "Währung",
            "auftraggeber_empfaenger": "Geschäftspartner",
            "verwendungszweck": "Verwendungszweck",
            "buchungstext": "Buchungstext",
        })

        print(display_df.to_string(index=False))
        print(f"\nAnzahl Buchungen: {len(konto_df)}")


# --------------------------------------------------
# Standalone-Start
# --------------------------------------------------

def main():
    # user_id = input("ING-Zugangsnummer: ").strip()
    # pin = getpass("ING-PIN: ")

    user_id = os.environ.get("ING_ZUGANG")
    pin = os.environ.get("ING_PIN")

    client = create_client(user_id, pin)

    # Einmalige interaktive Initialisierung
    minimal_interactive_cli_bootstrap(client)

    with client:
        complete_tan(client)

        accounts = get_accounts(client)
        print(accounts)
        print(type(accounts[0]))

        print(f"\nGefundene Konten: {len(accounts)}")

        for account in accounts:
            print(f"  {account.iban}")

        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        print(
            f"\nBuchungen vom {start_date:%d.%m.%Y} "
            f"bis {end_date:%d.%m.%Y}"
        )

        df = get_transactions_dataframe(
            client,
            accounts,
            start_date,
            end_date,
        )

        print_transactions(df)


if __name__ == "__main__":
    main()
