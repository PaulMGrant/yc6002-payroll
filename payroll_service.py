from __future__ import annotations

from datetime import date

from domain import (
    BaseContractStrategy,
    SalariedStrategy,
    PartTimeStrategy,
    HourlyStrategy,
    LondonWeightingDecorator,
    Contract,
    PayrollRun,
    Employee,
)
from repositories import EmployeeRepository, ContractRepository, PayrollRunRepository


def create_contract_strategy_for_employee(
    employee: Employee,
    contract: Contract,
) -> BaseContractStrategy:
    """
    Factory that interprets employee.contract_type and
    returns an appropriate strategy, optionally decorated
    with London weighting.
    """
    contract_type = employee.contract_type.upper()

    if contract_type == "SALARIED":
        if contract.base_salary is None:
            raise ValueError("Base salary is required for salaried contract.")
        strategy: BaseContractStrategy = SalariedStrategy(
            base_salary=contract.base_salary,
        )
    elif contract_type == "PART_TIME":
        if (
            contract.base_salary is None
            or contract.hourly_rate is None
            or contract.contract_hours is None
        ):
            raise ValueError(
                "Base salary, hourly rate and contract hours "
                "are required for part‑time contract.",
            )
        strategy = PartTimeStrategy(
            base_salary=contract.base_salary,
            hourly_rate=contract.hourly_rate,
            contract_hours=contract.contract_hours,
        )
    elif contract_type == "HOURLY":
        if contract.hourly_rate is None:
            raise ValueError("Hourly rate is required for hourly contract.")
        strategy = HourlyStrategy(hourly_rate=contract.hourly_rate)
    else:
        raise ValueError(f"Unknown contract type: {contract_type}")

    if employee.branch.upper() == "LONDON":
        strategy = LondonWeightingDecorator(strategy)

    return strategy


class PayrollService:
    """Coordinates payroll calculations and persistence."""

    def __init__(
        self,
        employee_repository: EmployeeRepository,
        contract_repository: ContractRepository,
        payroll_run_repository: PayrollRunRepository,
    ) -> None:
        self.employee_repository = employee_repository
        self.contract_repository = contract_repository
        self.payroll_run_repository = payroll_run_repository

    def run_payroll_for_employee(
        self,
        employee_id: int,
        hours_worked: float,
        pay_period_start: date,
        pay_period_end: date,
    ) -> PayrollRun:
        employee = self.employee_repository.get(employee_id)
        if employee is None:
            raise ValueError(f"Employee with id {employee_id} not found.")

        contract = self.contract_repository.get_active_for_employee(employee_id)
        if contract is None:
            raise ValueError(
                f"No active contract found for employee {employee_id}.",
            )

        strategy = create_contract_strategy_for_employee(employee, contract)
        gross_pay = strategy.calculate_gross_pay(hours_worked)
        london_weighting_applied = employee.branch.upper() == "LONDON"

        payroll_run = PayrollRun(
            id=None,
            employee_id=employee.id,
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            hours_worked=hours_worked,
            gross_pay=gross_pay,
            london_weighting_applied=london_weighting_applied,
        )

        run_id = self.payroll_run_repository.add(payroll_run)
        payroll_run.id = run_id
        return payroll_run
