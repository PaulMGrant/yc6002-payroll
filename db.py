import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path("yeoconnect.db")


@contextmanager
def get_connection():
    """Context manager that yields an SQLite connection."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialise_database() -> None:
    """Create tables if they do not already exist."""
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                address TEXT NOT NULL,
                start_date TEXT NOT NULL,
                ni_number TEXT NOT NULL UNIQUE,
                department TEXT NOT NULL,
                branch TEXT NOT NULL,
                contract_type TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                base_salary REAL,
                hourly_rate REAL,
                contract_hours REAL,
                effective_from TEXT NOT NULL,
                effective_to TEXT,
                FOREIGN KEY (employee_id)
                    REFERENCES employees (id)
                    ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS payroll_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                pay_period_start TEXT NOT NULL,
                pay_period_end TEXT NOT NULL,
                hours_worked REAL NOT NULL,
                gross_pay REAL NOT NULL,
                london_weighting_applied INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (employee_id)
                    REFERENCES employees (id)
                    ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS phone_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                handset_model TEXT NOT NULL,
                sale_date TEXT NOT NULL,
                sale_price REAL NOT NULL,
                commission REAL NOT NULL,
                FOREIGN KEY (employee_id)
                    REFERENCES employees (id)
                    ON DELETE CASCADE
            )
            """
        )


def dump_database(dump_path: Path | str = "yeoconnect_dump.sql") -> None:
    """
    Write a full SQL dump of the current database to a file.
    """
    dump_path = Path(dump_path)

    # Open a direct connection so we can call iterdump().
    connection = sqlite3.connect(DB_PATH)
    try:
        with dump_path.open("w", encoding="utf-8") as dump_file:
            for line in connection.iterdump():
                dump_file.write(f"{line}\n")
    finally:
        connection.close()

#run the db dump
if __name__ == "__main__":
    from pathlib import Path

    initialise_database()  # optional, but safe
    dump_database(Path("yeoconnect_dump.sql"))
    print("Dump written to yeoconnect_dump.sql")

