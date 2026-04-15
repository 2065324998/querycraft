"""Expression types for SQL query conditions and values."""

from dataclasses import dataclass, field
from typing import Any, Optional


class Expression:
    """Base class for all expressions."""
    pass


@dataclass
class Column(Expression):
    """A column reference."""
    name: str
    table: Optional[str] = None

    def __str__(self):
        if self.table:
            return f"{self.table}.{self.name}"
        return self.name


@dataclass
class Literal(Expression):
    """A literal value that becomes a bound parameter."""
    value: Any


@dataclass
class RawSQL(Expression):
    """Raw SQL expression passed through without parameterization."""
    sql: str


@dataclass
class Star(Expression):
    """Represents SELECT * or table.*"""
    table: Optional[str] = None


@dataclass
class Comparison(Expression):
    """A binary comparison (col = val, col > val, etc.)."""
    left: Expression
    operator: str
    right: Expression


@dataclass
class LogicalOp(Expression):
    """AND/OR combining multiple expressions."""
    operator: str
    children: list = field(default_factory=list)


@dataclass
class InExpression(Expression):
    """col IN (values) or col IN (subquery)."""
    column: Expression
    source: Any  # list of values or a Query object
    negated: bool = False


@dataclass
class ExistsExpression(Expression):
    """EXISTS (subquery) or NOT EXISTS (subquery)."""
    subquery: Any  # Query object
    negated: bool = False


@dataclass
class BetweenExpression(Expression):
    """col BETWEEN low AND high."""
    column: Expression
    low: Expression
    high: Expression
    negated: bool = False


@dataclass
class IsNullExpression(Expression):
    """col IS NULL or col IS NOT NULL."""
    column: Expression
    negated: bool = False


@dataclass
class FunctionCall(Expression):
    """SQL function call like COUNT(*), SUM(col), etc."""
    name: str
    args: list = field(default_factory=list)
    alias: Optional[str] = None
