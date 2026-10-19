import pandas as pd


def load_account_csv(csv_file):
    header_row = None

    with open(csv_file, encoding="cp1252") as file:
        for number, line in enumerate(file, start=1):
            if line.startswith("Buchung;"):
                header_row = number
                break

    if header_row is None:
        raise ValueError("CSV-Header nicht gefunden")

    skiprows = header_row - 1

    df = pd.read_csv(
        csv_file,
        encoding="cp1252",
        sep=";",
        skiprows=skiprows,
    )

    df["Betrag"] = pd.to_numeric(
        df["Betrag"]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    df["Saldo"] = pd.to_numeric(
        df["Saldo"]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    df["Buchung"] = pd.to_datetime(
        df["Buchung"],
        format="%d.%m.%Y"
    )

    df["Wertstellungsdatum"] = pd.to_datetime(
        df["Wertstellungsdatum"],
        format="%d.%m.%Y"
    )

    return df