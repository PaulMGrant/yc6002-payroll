from __future__ import annotations

from datetime import date

from db import initialise_database
from domain import Employee, Contract
from repositories import (
    EmployeeRepository,
    ContractRepository,
    PayrollRunRepository,
)
from payroll_service import PayrollService


def parse_date(value: str) -> date:
    return date.fromisoformat(value.strip())


def prompt_employee() -> Employee:
    print("Create new employee")
    first_name = input("First name: ").strip()
    last_name = input("Last name: ").strip()
    address = input("Address: ").strip()
    start_date_str = input("Start date (YYYY-MM-DD): ").strip()
    ni_number = input("NI number: ").strip().upper()
    department = input("Department: ").strip()
    branch = input("Branch (e.g., Yeovil, London): ").strip()
    contract_type = input(
        "Contract type (SALARIED, PART_TIME, HOURLY): ",
    ).strip()

    start_date = parse_date(start_date_str)

    return Employee(
        id=None,
        first_name=first_name,
        last_name=last_name,
        address=address,
        start_date=start_date,
        ni_number=ni_number,
        department=department,
        branch=branch,
        contract_type=contract_type,
    )


def prompt_contract(employee_id: int) -> Contract:
    print("Create contract")
    base_salary_str = input("Base salary (blank if N/A): ").strip() or None
    hourly_rate_str = input("Hourly rate (blank if N/A): ").strip() or None
    contract_hours_str = input(
        "Contract hours (blank if N/A): ",
    ).strip() or None
    effective_from_str = input("Effective from (YYYY-MM-DD): ").strip()
    effective_to_str = input(
        "Effective to (YYYY-MM-DD, blank if open‑ended): ",
    ).strip() or None

    base_salary = float(base_salary_str) if base_salary_str else None
    hourly_rate = float(hourly_rate_str) if hourly_rate_str else None
    contract_hours = (
        float(contract_hours_str) if contract_hours_str else None
    )
    effective_from = parse_date(effective_from_str)
    effective_to = (
        parse_date(effective_to_str) if effective_to_str else None
    )

    return Contract(
        id=None,
        employee_id=employee_id,
        base_salary=base_salary,
        hourly_rate=hourly_rate,
        contract_hours=contract_hours,
        effective_from=effective_from,
        effective_to=effective_to,
    )


def create_employee_flow(
    employee_repository: EmployeeRepository,
    contract_repository: ContractRepository,
) -> None:
    employee = prompt_employee()
    employee_id = employee_repository.add(employee)
    print(f"Employee created with id {employee_id}")

    contract = prompt_contract(employee_id)
    contract_repository.add(contract)
    print("Contract created.")


def run_payroll_flow(
    payroll_service: PayrollService,
) -> None:
    try:
        employee_id = int(input("Employee id: ").strip())
    except ValueError:
        print("Invalid employee id.")
        return

    try:
        hours_worked = float(input("Hours worked this period: ").strip())
    except ValueError:
        print("Invalid hours worked.")
        return

    start_str = input("Pay period start (YYYY-MM-DD): ").strip()
    end_str = input("Pay period end (YYYY-MM-DD): ").strip()

    try:
        pay_period_start = parse_date(start_str)
        pay_period_end = parse_date(end_str)
    except ValueError:
        print("Invalid date format.")
        return

    try:
        payroll_run = payroll_service.run_payroll_for_employee(
            employee_id=employee_id,
            hours_worked=hours_worked,
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
        )
    except ValueError as error:
        print(f"Error: {error}")
        return

    print("\nPayslip")
    print("-------")
    print(f"Employee id: {payroll_run.employee_id}")
    print(f"Period: {pay_period_start} to {pay_period_end}")
    print(f"Hours worked: {payroll_run.hours_worked}")
    print(f"Gross pay: £{payroll_run.gross_pay:.2f}")
    if payroll_run.london_weighting_applied:
        print("Includes London weighting.")


def main() -> None:
    initialise_database()

    employee_repository = EmployeeRepository()
    contract_repository = ContractRepository()
    payroll_run_repository = PayrollRunRepository()
    payroll_service = PayrollService(
        employee_repository=employee_repository,
        contract_repository=contract_repository,
        payroll_run_repository=payroll_run_repository,
    )

    while True:
        print("\nYeoConnect Payroll System")
        print("1. Create employee and contract")
        print("2. Run payroll for employee")
        print("3. Exit")

        choice = input("Select option: ").strip()

        if choice == "1":
            create_employee_flow(employee_repository, contract_repository)
        elif choice == "2":
            run_payroll_flow(payroll_service)
        elif choice == "3":
            print("Goodbye.")
            break
        else:
            print("Invalid option. Please choose 1, 2 or 3.")


if __name__ == "__main__":
    main()
