from finanzanalyse.database import create_database, import_transactions, load_transactions
from finanzanalyse.account import load_account_csv
from finanzanalyse.paths import RAW_DATA_DIR
from finanzanalyse.kategorien import *

def add_metaData(df):
    df = df.copy()
    df["kategorie"] = df.apply(kategorisiere_buchung, axis=1)
    df["monat"] = df["buchung"].dt.to_period("M")
    df["year"] = df["buchung"].dt.to_period("Y")

    return df


def monthly_summary(df):
    # Monat jeder Buchung bestimmen
    df = df.copy()
    df["monat"] = df["buchung"].dt.to_period("M")

    # Einnahmen und Ausgaben getrennt berechnen
    df["einnahmen"] = df["betrag"].where(df["betrag"] > 0, 0)
    df["ausgaben"] = df["betrag"].where(df["betrag"] < 0, 0)

    # Nach Monat gruppieren und Summen berechnen
    monthly = (
        df.groupby("monat", as_index=False)
        .agg(
            einnahmen=("einnahmen", "sum"),
            ausgaben=("ausgaben", "sum"),
            differenz=("betrag", "sum"),
        )
        .sort_values("monat")
        .reset_index(drop=True)
    )

    return monthly

def select_month(df, month, year):
    selected = df.loc[(df["buchung"].dt.year == year)
                      & (df["buchung"].dt.month == month)]
    return selected

def select_category(df, category):

    return df[df["kategorie"].isin(category)]




