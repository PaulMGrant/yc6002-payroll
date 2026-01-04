BEGIN TRANSACTION;
CREATE TABLE contracts (
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
            );
CREATE TABLE employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                address TEXT NOT NULL,
                start_date TEXT NOT NULL,
                ni_number TEXT NOT NULL UNIQUE,
                department TEXT NOT NULL,
                branch TEXT NOT NULL,
                contract_type TEXT NOT NULL
            );
CREATE TABLE payroll_runs (
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
            );
CREATE TABLE phone_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                handset_model TEXT NOT NULL,
                sale_date TEXT NOT NULL,
                sale_price REAL NOT NULL,
                commission REAL NOT NULL,
                FOREIGN KEY (employee_id)
                    REFERENCES employees (id)
                    ON DELETE CASCADE
            );
CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            );
INSERT INTO "users" VALUES(1,'admin','e74bb1505d50b15c1cb866b35cacef3f','361e3155df2291c12532a1d61fa0ec87afa5c066307f6ff9c6e6b76468ecd94d','ADMIN');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('users',1);
COMMIT;
