from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from abc import ABC, abstractmethod
from typing import Optional


@dataclass
class Employee:
    id: Optional[int]
    first_name: str
    last_name: str
    address: str
    start_date: date
    ni_number: str
    department: str
    branch: str
    contract_type: str


@dataclass
class Contract:
    id: Optional[int]
    employee_id: int
    base_salary: Optional[float]
    hourly_rate: Optional[float]
    contract_hours: Optional[float]
    effective_from: date
    effective_to: Optional[date]


@dataclass
class PayrollRun:
    id: Optional[int]
    employee_id: int
    pay_period_start: date
    pay_period_end: date
    hours_worked: float
    gross_pay: float
    london_weighting_applied: bool


@dataclass
class PhoneSale:
    id: Optional[int]
    employee_id: int
    handset_model: str
    sale_date: date
    sale_price: float
    commission: float


class BaseContractStrategy(ABC):
    """Abstract base class for contract pay strategies."""

    @abstractmethod
    def calculate_gross_pay(self, hours_worked: float) -> float:
        """Return gross pay for the period."""
        raise NotImplementedError


class SalariedStrategy(BaseContractStrategy):
    """Salaried contract where pay does not depend on hours."""

    def __init__(self, base_salary: float) -> None:
        self.base_salary = base_salary

    def calculate_gross_pay(self, hours_worked: float) -> float:
        return self.base_salary


class PartTimeStrategy(BaseContractStrategy):
    """
    Part‑time contract:
    - Base salary covers contract hours.
    - Hours above contract are paid at 2.5 * hourly_rate.
    """

    def __init__(
        self,
        base_salary: float,
        hourly_rate: float,
        contract_hours: float,
    ) -> None:
        self.base_salary = base_salary
        self.hourly_rate = hourly_rate
        self.contract_hours = contract_hours

    def calculate_gross_pay(self, hours_worked: float) -> float:
        overtime_hours = max(0.0, hours_worked - self.contract_hours)
        overtime_pay = overtime_hours * self.hourly_rate * 2.5
        return self.base_salary + overtime_pay


class HourlyStrategy(BaseContractStrategy):
    """
    Hourly contract with incentive overtime:
    - First 37 hours at hourly_rate.
    - Hours above 37 at 2.5 * hourly_rate.
    """

    def __init__(self, hourly_rate: float) -> None:
        self.hourly_rate = hourly_rate

    def calculate_gross_pay(self, hours_worked: float) -> float:
        regular_hours = min(hours_worked, 37.0)
        overtime_hours = max(0.0, hours_worked - 37.0)
        regular_pay = regular_hours * self.hourly_rate
        overtime_pay = overtime_hours * self.hourly_rate * 2.5
        return regular_pay + overtime_pay


class LondonWeightingDecorator(BaseContractStrategy):
    """Decorator that applies 20% London weighting to any strategy."""

    def __init__(self, inner: BaseContractStrategy) -> None:
        self.inner = inner

    def calculate_gross_pay(self, hours_worked: float) -> float:
        base_pay = self.inner.calculate_gross_pay(hours_worked)
        return base_pay * 1.2


def create_contract_strategy(contract: Contract) -> BaseContractStrategy:
    """
    Create a contract strategy based on contract_type stored
    on the employee's contract.
    """
    # The type string is interpreted by the service layer.
    raise NotImplementedError(
        "create_contract_strategy is provided in payroll_service.py "
        "where Employee and Contract are available together."
    )
