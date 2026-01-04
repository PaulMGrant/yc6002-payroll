"""
Simple Tkinter GUI for YeoConnect with login and
basic employee/contract creation and payroll run.
"""

from __future__ import annotations

import hashlib
import os
from datetime import date
from typing import Optional

import tkinter as tk
from tkinter import ttk, messagebox

from db import initialise_database, get_connection
from domain import Employee, Contract
from repositories import EmployeeRepository, ContractRepository, PayrollRunRepository
from payroll_service import PayrollService


# ---------- auth helpers ----------


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """
    Hash a password with SHA-256 and a salt.
    Returns (salt, hex_digest).
    This is intentionally simple for an educational app.
    """
    if salt is None:
        salt = os.urandom(16).hex()
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return salt, digest


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Verify a plaintext password against salted hash."""
    _, computed = hash_password(password, salt=salt)
    return computed == expected_hash


def create_users_table() -> None:
    """Create a basic users table if it does not already exist."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """
        )


def ensure_default_admin() -> None:
    """
    Ensure an 'admin' user exists for testing.
    Username: admin
    Password: admin123
    """
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
        if cursor.fetchone():
            return

        salt, digest = hash_password("admin123")
        cursor.execute(
            """
            INSERT INTO users (username, salt, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            ("admin", salt, digest, "ADMIN"),
        )


def authenticate(username: str, password: str) -> bool:
    """Check username and password against the users table."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT salt, password_hash FROM users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        if row is None:
            return False
        return verify_password(password, row["salt"], row["password_hash"])


# ---------- UI helpers ----------


def parse_date(value: str) -> date:
    return date.fromisoformat(value.strip())


# ---------- main windows ----------


class LoginWindow(tk.Tk):
    """Initial login window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("YeoConnect Login")
        self.geometry("600x360")
        self.resizable(False, False)

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        self._build_widgets()

    def _build_widgets(self) -> None:
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Username:").grid(row=0, column=0, sticky="w")
        username_entry = ttk.Entry(frame, textvariable=self.username_var)
        username_entry.grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(frame, text="Password:").grid(row=1, column=0, sticky="w")
        password_entry = ttk.Entry(
            frame,
            textvariable=self.password_var,
            show="*",
        )
        password_entry.grid(row=1, column=1, sticky="ew", pady=5)

        login_button = ttk.Button(frame, text="Login", command=self._handle_login)
        login_button.grid(row=2, column=0, columnspan=2, pady=10)

        frame.columnconfigure(1, weight=1)

        self.bind("<Return>", lambda event: self._handle_login())

    def _handle_login(self) -> None:
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username or not password:
            messagebox.showerror("Error", "Username and password required.")
            return

        if not authenticate(username, password):
            messagebox.showerror("Error", "Invalid credentials.")
            return

        self.destroy()
        app = MainWindow(current_user=username)
        app.mainloop()


class MainWindow(tk.Tk):
    """Main application window shown after successful login."""

    def __init__(self, current_user: str) -> None:
        super().__init__()
        self.title(f"YeoConnect Payroll - {current_user}")
        self.geometry("600x400")

        # Repositories and services
        self.employee_repository = EmployeeRepository()
        self.contract_repository = ContractRepository()
        self.payroll_run_repository = PayrollRunRepository()
        self.payroll_service = PayrollService(
            employee_repository=self.employee_repository,
            contract_repository=self.contract_repository,
            payroll_run_repository=self.payroll_run_repository,
        )

        self._build_ui()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        employee_frame = ttk.Frame(notebook, padding=10)
        payroll_frame = ttk.Frame(notebook, padding=10)

        notebook.add(employee_frame, text="Employees")
        notebook.add(payroll_frame, text="Payroll")

        self._build_employee_tab(employee_frame)
        self._build_payroll_tab(payroll_frame)

    # ----- Employees tab -----

    def _build_employee_tab(self, parent: ttk.Frame) -> None:
        self.first_name_var = tk.StringVar()
        self.last_name_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.start_date_var = tk.StringVar()
        self.ni_number_var = tk.StringVar()
        self.department_var = tk.StringVar()
        self.branch_var = tk.StringVar()
        self.contract_type_var = tk.StringVar()

        self.base_salary_var = tk.StringVar()
        self.hourly_rate_var = tk.StringVar()
        self.contract_hours_var = tk.StringVar()
        self.contract_from_var = tk.StringVar()
        self.contract_to_var = tk.StringVar()

        left = ttk.Frame(parent)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(left, text="First name").grid(row=row, column=0, sticky="w")
        ttk.Entry(left, textvariable=self.first_name_var).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=2,
        )
        row += 1

        ttk.Label(left, text="Last name").grid(row=row, column=0, sticky="w")
        ttk.Entry(left, textvariable=self.last_name_var).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=2,
        )
        row += 1

        ttk.Label(left, text="Address").grid(row=row, column=0, sticky="w")
        ttk.Entry(left, textvariable=self.address_var).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=2,
        )
        row += 1

        ttk.Label(left, text="Start date (YYYY-MM-DD)").grid(
            row=row,
            column=0,
            sticky="w",
        )
        ttk.Entry(left, textvariable=self.start_date_var).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=2,
        )
        row += 1

        ttk.Label(left, text="NI number").grid(row=row, column=0, sticky="w")
        ttk.Entry(left, textvariable=self.ni_number_var).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=2,
        )
        row += 1

        ttk.Label(left, text="Department").grid(row=row, column=0, sticky="w")
        ttk.Entry(left, textvariable=self.department_var).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=2,
        )
        row += 1

        ttk.Label(left, text="Branch (e.g., London)").grid(
            row=row,
            column=0,
            sticky="w",
        )
        ttk.Entry(left, textvariable=self.branch_var).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=2,
        )
        row += 1

        ttk.Label(left, text="Contract type").grid(row=row, column=0, sticky="w")
        contract_combo = ttk.Combobox(
            left,
            textvariable=self.contract_type_var,
            values=["SALARIED", "PART_TIME", "HOURLY"],
            state="readonly",
        )
        contract_combo.grid(row=row, column=1, sticky="ew", pady=2)
        contract_combo.current(0)
        row += 1

        ttk.Separator(left).grid(row=row, columnspan=2, sticky="ew", pady=6)
        row += 1

        ttk.Label(left, text="Base salary").grid(row=row, column=0, sticky="w")
        ttk.Entry(left, textvariable=self.base_salary_var).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=2,
        )
        row += 1

        ttk.Label(left, text="Hourly rate").grid(row=row, column=0, sticky="w")
        ttk.Entry(left, textvariable=self.hourly_rate_var).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=2,
        )
        row += 1

        ttk.Label(left, text="Contract hours").grid(row=row, column=0, sticky="w")
        ttk.Entry(left, textvariable=self.contract_hours_var).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=2,
        )
        row += 1

        ttk.Label(left, text="Effective from").grid(row=row, column=0, sticky="w")
        ttk.Entry(left, textvariable=self.contract_from_var).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=2,
        )
        row += 1

        ttk.Label(left, text="Effective to (optional)").grid(
            row=row,
            column=0,
            sticky="w",
        )
        ttk.Entry(left, textvariable=self.contract_to_var).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=2,
        )
        row += 1

        create_button = ttk.Button(
            left,
            text="Create employee + contract",
            command=self._handle_create_employee,
        )
        create_button.grid(row=row, column=0, columnspan=2, pady=10)

        left.columnconfigure(1, weight=1)

    def _handle_create_employee(self) -> None:
        try:
            employee = Employee(
                id=None,
                first_name=self.first_name_var.get().strip(),
                last_name=self.last_name_var.get().strip(),
                address=self.address_var.get().strip(),
                start_date=parse_date(self.start_date_var.get()),
                ni_number=self.ni_number_var.get().strip().upper(),
                department=self.department_var.get().strip(),
                branch=self.branch_var.get().strip(),
                contract_type=self.contract_type_var.get().strip(),
            )
        except ValueError:
            messagebox.showerror("Error", "Invalid date format for start date.")
            return

        if not employee.first_name or not employee.last_name:
            messagebox.showerror("Error", "First and last name are required.")
            return

        try:
            employee_id = self.employee_repository.add(employee)
        except Exception as error:
            messagebox.showerror("Error", f"Could not save employee: {error}")
            return

        try:
            base_salary = (
                float(self.base_salary_var.get())
                if self.base_salary_var.get().strip()
                else None
            )
            hourly_rate = (
                float(self.hourly_rate_var.get())
                if self.hourly_rate_var.get().strip()
                else None
            )
            contract_hours = (
                float(self.contract_hours_var.get())
                if self.contract_hours_var.get().strip()
                else None
            )
            effective_from = parse_date(self.contract_from_var.get())
            effective_to = (
                parse_date(self.contract_to_var.get())
                if self.contract_to_var.get().strip()
                else None
            )
        except ValueError:
            messagebox.showerror("Error", "Invalid numeric or date value.")
            return

        contract = Contract(
            id=None,
            employee_id=employee_id,
            base_salary=base_salary,
            hourly_rate=hourly_rate,
            contract_hours=contract_hours,
            effective_from=effective_from,
            effective_to=effective_to,
        )

        try:
            self.contract_repository.add(contract)
        except Exception as error:
            messagebox.showerror("Error", f"Could not save contract: {error}")
            return

        messagebox.showinfo(
            "Success",
            f"Employee created with id {employee_id}.",
        )

    # ----- Payroll tab -----

    def _build_payroll_tab(self, parent: ttk.Frame) -> None:
        self.employee_id_var = tk.StringVar()
        self.hours_worked_var = tk.StringVar()
        self.pay_start_var = tk.StringVar()
        self.pay_end_var = tk.StringVar()

        ttk.Label(parent, text="Employee id").grid(row=0, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.employee_id_var).grid(
            row=0,
            column=1,
            sticky="ew",
            pady=2,
        )

        ttk.Label(parent, text="Hours worked").grid(row=1, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.hours_worked_var).grid(
            row=1,
            column=1,
            sticky="ew",
            pady=2,
        )

        ttk.Label(parent, text="Period start (YYYY-MM-DD)").grid(
            row=2,
            column=0,
            sticky="w",
        )
        ttk.Entry(parent, textvariable=self.pay_start_var).grid(
            row=2,
            column=1,
            sticky="ew",
            pady=2,
        )

        ttk.Label(parent, text="Period end (YYYY-MM-DD)").grid(
            row=3,
            column=0,
            sticky="w",
        )
        ttk.Entry(parent, textvariable=self.pay_end_var).grid(
            row=3,
            column=1,
            sticky="ew",
            pady=2,
        )

        run_button = ttk.Button(
            parent,
            text="Run payroll",
            command=self._handle_run_payroll,
        )
        run_button.grid(row=4, column=0, columnspan=2, pady=10)

        self.result_label = ttk.Label(parent, text="", foreground="blue")
        self.result_label.grid(row=5, column=0, columnspan=2, sticky="w")

        parent.columnconfigure(1, weight=1)

    def _handle_run_payroll(self) -> None:
        try:
            employee_id = int(self.employee_id_var.get())
            hours_worked = float(self.hours_worked_var.get())
            pay_period_start = parse_date(self.pay_start_var.get())
            pay_period_end = parse_date(self.pay_end_var.get())
        except ValueError:
            messagebox.showerror(
                "Error",
                "Invalid employee id, hours, or date format.",
            )
            return

        try:
            payroll_run = self.payroll_service.run_payroll_for_employee(
                employee_id=employee_id,
                hours_worked=hours_worked,
                pay_period_start=pay_period_start,
                pay_period_end=pay_period_end,
            )
        except Exception as error:
            messagebox.showerror("Error", str(error))
            return

        self.result_label.config(
            text=(
                f"Gross pay: £{payroll_run.gross_pay:.2f} "
                f"(London weighting: "
                f"{'yes' if payroll_run.london_weighting_applied else 'no'})"
            )
        )


# ---------- entry point ----------


def main() -> None:
    initialise_database()
    create_users_table()
    ensure_default_admin()

    login_window = LoginWindow()
    login_window.mainloop()


if __name__ == "__main__":
    main()
