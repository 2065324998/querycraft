"""AST node types for SQL queries."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CTE:
    """A Common Table Expression (WITH clause)."""
    name: str
    query: Optional['Query'] = None
    recursive: bool = False


@dataclass
class Query:
    """Represents a complete SQL query."""
    select_columns: list = field(default_factory=list)
    from_table: Optional[str] = None
    from_subquery: Optional['Query'] = None
    from_alias: Optional[str] = None
    joins: list = field(default_factory=list)
    wheres: list = field(default_factory=list)
    group_by: list = field(default_factory=list)
    havings: list = field(default_factory=list)
    order_by: list = field(default_factory=list)
    limit: Optional[int] = None
    offset: Optional[int] = None
    distinct: bool = False
    query_type: str = "select"

    # CTE fields
    ctes: list = field(default_factory=list)

    # Compound query fields (UNION/INTERSECT/EXCEPT)
    compound_op: Optional[str] = None
    compound_right: Optional['Query'] = None
    compound_all: bool = False

    # INSERT fields
    insert_table: Optional[str] = None
    insert_columns: list = field(default_factory=list)
    insert_values: list = field(default_factory=list)

    # UPDATE fields
    update_table: Optional[str] = None
    update_sets: list = field(default_factory=list)

    # DELETE fields
    delete_table: Optional[str] = None


@dataclass
class Join:
    """A JOIN clause."""
    join_type: str = "INNER"
    table: Optional[str] = None
    subquery: Optional[Query] = None
    alias: Optional[str] = None
    condition: Optional[object] = None


@dataclass
class OrderByItem:
    """An ORDER BY item."""
    column: str
    direction: str = "ASC"
