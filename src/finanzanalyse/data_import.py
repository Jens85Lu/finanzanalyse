from finanzanalyse.account import load_account_csv
from finanzanalyse import database as db
from finanzanalyse.paths import RAW_DATA_DIR, IMPORTED_DATA_DIR


def import_file(csv_file):
    df = load_account_csv(csv_file)

    number_imported = db.import_transactions(df)

    print(f"  {number_imported} neue Buchungen")

    csv_file.rename(IMPORTED_DATA_DIR / csv_file.name)

    print(f"  {csv_file.name} verschoben.")


def import_all_files():
    IMPORTED_DATA_DIR.mkdir(exist_ok=True)

    for csv_file in RAW_DATA_DIR.glob("*.csv"):
        print(f"Importiere: {csv_file.name}")
        import_file(csv_file)

