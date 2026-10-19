from finanzanalyse.account import load_account_csv
from finanzanalyse import database as db
from finanzanalyse.paths import RAW_DATA_DIR, IMPORTED_DATA_DIR


def import_file(csv_file):
    df = load_account_csv(csv_file)

    number_imported = db.import_transactions(df)

    print(f"  {number_imported} neue Buchungen")

    csv_file.rename(IMPORTED_DATA_DIR / csv_file.name)

    print(f"  {csv_file.name} verschoben.")

    return number_imported


def import_all_files():
    IMPORTED_DATA_DIR.mkdir(exist_ok=True)

    total_imported = 0
    csv_files = list(RAW_DATA_DIR.glob("*.csv"))

    for csv_file in csv_files:
        print(f"Importiere: {csv_file.name}")

        number_imported = import_file(csv_file)

        if number_imported is None:
            raise TypeError(
                f"import_file({csv_file.name}) hat None zurückgegeben."
            )

        total_imported += number_imported

    return total_imported



