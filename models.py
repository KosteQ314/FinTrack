import uuid
from dataclasses import dataclass, field
from enum import Enum


class TransactionType(Enum):
    INCOME = "income"
    EXPENSE = "expense"


@dataclass
class Transaction:
    description: str
    amount: float
    type: TransactionType
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])


@dataclass
class Player:
    name: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])


@dataclass
class Session:
    name: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    players: list = field(default_factory=list)
    transactions: list = field(default_factory=list)

    @property
    def total_income(self):
        return sum(
            t.amount for t in self.transactions if t.type == TransactionType.INCOME
        )

    @property
    def total_expenses(self):
        return sum(
            t.amount for t in self.transactions if t.type == TransactionType.EXPENSE
        )

    @property
    def net_profit(self):
        return self.total_income - self.total_expenses
