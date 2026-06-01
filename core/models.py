import uuid
from dataclasses import dataclass, field
from enum import Enum


# Transaction types
class TransactionType(Enum):
    INCOME = "income"
    EXPENSE = "expense"


# Specifies a transaction
@dataclass
class Transaction:
    description: str
    amount: int
    type: TransactionType
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])


# Specifies a player
@dataclass
class Player:
    name: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])


# Specifies a split configuration for a session
@dataclass
class SplitConfig:
    mode: str = "equal"
    overrides: dict = field(default_factory=dict)


# Specifies a session
@dataclass
class Session:
    name: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    players: list = field(default_factory=list)
    transactions: list = field(default_factory=list)
    split_config: SplitConfig = field(default_factory=SplitConfig)

    # Calculates the total income from transactions
    @property
    def total_income(self):
        return sum(
            t.amount for t in self.transactions if t.type == TransactionType.INCOME
        )

    # Calculates the total expenses from transactions
    @property
    def total_expenses(self):
        return sum(
            t.amount for t in self.transactions if t.type == TransactionType.EXPENSE
        )

    # Calculates the net profit from transactions
    @property
    def net_profit(self):
        return self.total_income - self.total_expenses

    # Calculates the split of net profit among players
    def calculate_split(self, mode=None, overrides=None):
        if not self.players:
            return {}

        mode = mode or self.split_config.mode
        overrides = overrides or self.split_config.overrides
        profit = self.net_profit

        if mode == "equal":
            share = profit / len(self.players)
            return {p.name: share for p in self.players}

        elif mode == "percentage":
            assigned_pct = sum(overrides.values())
            unassigned = [p for p in self.players if p.name.lower() not in overrides]
            remainder_pct = (100 - assigned_pct) / len(unassigned) if unassigned else 0
            result = {}
            for p in self.players:
                pct = overrides.get(p.name.lower(), remainder_pct) / 100
                result[p.name] = profit * pct
            return result

        elif mode == "fixed":
            assigned = sum(overrides.values())
            remainder = profit - assigned
            unassigned = [p for p in self.players if p.name.lower() not in overrides]
            per_remaining = remainder / len(unassigned) if unassigned else 0
            result = {}
            for p in self.players:
                if p.name.lower() in overrides:
                    result[p.name] = overrides[p.name.lower()]
                else:
                    result[p.name] = per_remaining
            return result

        return {}
