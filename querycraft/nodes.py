"""AST node types for SQL queries."""

from dataclasses import dataclass, field
from typing import Optional


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
