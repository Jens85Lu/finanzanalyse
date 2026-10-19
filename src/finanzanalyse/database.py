import sqlite3
import pandas as pd

from finanzanalyse.paths import DATA_DIR


DB_FILE = DATA_DIR / "beispiel.db"


def create_database():
    with sqlite3.connect(DB_FILE) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                buchung TEXT NOT NULL,
                wertstellungsdatum TEXT,
                betrag REAL NOT NULL,
                saldo REAL NOT NULL,
                auftraggeber_empfaenger TEXT,
                verwendungszweck TEXT,
                UNIQUE(buchung, betrag, saldo)
            )
        """)

def import_transactions(df):
    imported = 0

    with sqlite3.connect(DB_FILE) as connection:
        for _, row in df.iterrows():
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO transactions (
                    buchung,
                    wertstellungsdatum,
                    betrag,
                    saldo,
                    auftraggeber_empfaenger,
                    verwendungszweck
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    row["Buchung"].strftime("%Y-%m-%d"),
                    row["Wertstellungsdatum"].strftime("%Y-%m-%d"),
                    row["Betrag"],
                    row["Saldo"],
                    row["Auftraggeber/Empfänger"],
                    row["Verwendungszweck"]
                )
            )

            imported += cursor.rowcount

    return imported

def load_transactions(start_date, stop_date):
    with sqlite3.connect(DB_FILE) as connection:
        df = pd.read_sql_query(
            """
            SELECT *
            FROM transactions
            WHERE buchung >= ?
              AND buchung < ?
            ORDER BY buchung DESC
            """,
            connection,
            params=(start_date, stop_date)
        )
        df["buchung"] = pd.to_datetime(df["buchung"])
        df["wertstellungsdatum"] = pd.to_datetime(
        df["wertstellungsdatum"])
    
    return df

def load_month(year, month):
    month_pattern = f"{year}-{month:02d}-%"

    with sqlite3.connect(DB_FILE) as connection:
        df = pd.read_sql_query(
            """
            SELECT *
            FROM transactions
            WHERE buchung LIKE ?
            ORDER BY buchung DESC
            """,
            connection,
            params=(month_pattern,)
        )

    df["buchung"] = pd.to_datetime(df["buchung"])
    df["wertstellungsdatum"] = pd.to_datetime(
        df["wertstellungsdatum"]
    )

    return df


def load_monthly_summary(start_date, end_date):
    with sqlite3.connect(DB_FILE) as connection:
        df = pd.read_sql_query(
            """
            SELECT
                substr(buchung, 1, 7) AS monat,
                SUM(CASE WHEN betrag > 0
                    THEN betrag ELSE 0 END) AS einnahmen,
                SUM(CASE WHEN betrag < 0
                    THEN betrag ELSE 0 END) AS ausgaben,
                SUM(betrag) AS differenz
            FROM transactions
            WHERE buchung >= ?
              AND buchung < ?
            GROUP BY monat
            ORDER BY monat
            """,
            connection,
            params=(start_date, end_date)
        )

    return df
