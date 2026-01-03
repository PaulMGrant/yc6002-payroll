from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from db import get_connection
from domain import Employee, Contract, PayrollRun, PhoneSale


class EmployeeRepository:
    """Repository for Employee entities."""

    def add(self, employee: Employee) -> int:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO employees (
                    first_name,
                    last_name,
                    address,
                    start_date,
                    ni_number,
                    department,
                    branch,
                    contract_type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    employee.first_name,
                    employee.last_name,
                    employee.address,
                    employee.start_date.isoformat(),
                    employee.ni_number,
                    employee.department,
                    employee.branch,
                    employee.contract_type.upper(),
                ),
            )
            return cursor.lastrowid

    def get(self, employee_id: int) -> Optional[Employee]:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT * FROM employees WHERE id = ?",
                (employee_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return self._row_to_employee(row)

    def search_by_last_name(self, last_name: str) -> List[Employee]:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT * FROM employees WHERE last_name LIKE ?",
                (f"%{last_name}%",),
            )
            return [self._row_to_employee(row) for row in cursor.fetchall()]

    def update(self, employee: Employee) -> None:
        if employee.id is None:
            raise ValueError("Employee ID must not be None for update.")

        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE employees
                SET first_name = ?,
                    last_name = ?,
                    address = ?,
                    start_date = ?,
                    ni_number = ?,
                    department = ?,
                    branch = ?,
                    contract_type = ?
                WHERE id = ?
                """,
                (
                    employee.first_name,
                    employee.last_name,
                    employee.address,
                    employee.start_date.isoformat(),
                    employee.ni_number,
                    employee.department,
                    employee.branch,
                    employee.contract_type.upper(),
                    employee.id,
                ),
            )

    def delete(self, employee_id: int) -> None:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "DELETE FROM employees WHERE id = ?",
                (employee_id,),
            )

    @staticmethod
    def _row_to_employee(row) -> Employee:
        return Employee(
            id=row["id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            address=row["address"],
            start_date=date.fromisoformat(row["start_date"]),
            ni_number=row["ni_number"],
            department=row["department"],
            branch=row["branch"],
            contract_type=row["contract_type"],
        )


class ContractRepository:
    """Repository for Contract entities."""

    def add(self, contract: Contract) -> int:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO contracts (
                    employee_id,
                    base_salary,
                    hourly_rate,
                    contract_hours,
                    effective_from,
                    effective_to
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    contract.employee_id,
                    contract.base_salary,
                    contract.hourly_rate,
                    contract.contract_hours,
                    contract.effective_from.isoformat(),
                    contract.effective_to.isoformat()
                    if contract.effective_to
                    else None,
                ),
            )
            return cursor.lastrowid

    def get_active_for_employee(self, employee_id: int) -> Optional[Contract]:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT *
                FROM contracts
                WHERE employee_id = ?
                ORDER BY effective_from DESC
                LIMIT 1
                """,
                (employee_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return self._row_to_contract(row)

    @staticmethod
    def _row_to_contract(row) -> Contract:
        effective_to_value = row["effective_to"]
        return Contract(
            id=row["id"],
            employee_id=row["employee_id"],
            base_salary=row["base_salary"],
            hourly_rate=row["hourly_rate"],
            contract_hours=row["contract_hours"],
            effective_from=date.fromisoformat(row["effective_from"]),
            effective_to=(
                date.fromisoformat(effective_to_value)
                if effective_to_value
                else None
            ),
        )


class PayrollRunRepository:
    """Repository for PayrollRun entities."""

    def add(self, payroll_run: PayrollRun) -> int:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO payroll_runs (
                    employee_id,
                    pay_period_start,
                    pay_period_end,
                    hours_worked,
                    gross_pay,
                    london_weighting_applied,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payroll_run.employee_id,
                    payroll_run.pay_period_start.isoformat(),
                    payroll_run.pay_period_end.isoformat(),
                    payroll_run.hours_worked,
                    payroll_run.gross_pay,
                    int(payroll_run.london_weighting_applied),
                    datetime.utcnow().isoformat(),
                ),
            )
            return cursor.lastrowid


class PhoneSaleRepository:
    """Repository for PhoneSale entities."""

    def add(self, sale: PhoneSale) -> int:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO phone_sales (
                    employee_id,
                    handset_model,
                    sale_date,
                    sale_price,
                    commission
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    sale.employee_id,
                    sale.handset_model,
                    sale.sale_date.isoformat(),
                    sale.sale_price,
                    sale.commission,
                ),
            )
            return cursor.lastrowid
