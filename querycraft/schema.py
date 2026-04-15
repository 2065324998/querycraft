"""Table schema definitions for query validation."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ColumnDef:
    """A column definition."""
    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False
    default: Optional[str] = None


@dataclass
class TableSchema:
    """A table schema for validation."""
    name: str
    columns: list = field(default_factory=list)

    def get_column(self, name):
        """Get a column definition by name."""
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def has_column(self, name):
        """Check if a column exists."""
        return self.get_column(name) is not None

    def column_names(self):
        """Return all column names."""
        return [col.name for col in self.columns]


class SchemaRegistry:
    """Registry of table schemas for validation."""

    def __init__(self):
        self._tables = {}

    def register(self, schema):
        """Register a table schema."""
        self._tables[schema.name] = schema

    def get(self, table_name):
        """Get a table schema by name."""
        return self._tables.get(table_name)

    def validate_columns(self, table_name, columns):
        """Check if columns exist in the table schema.

        Returns a list of invalid column names, or an empty list
        if all are valid. Returns empty list if the table has no
        registered schema.
        """
        schema = self.get(table_name)
        if schema is None:
            return []
        invalid = []
        for col in columns:
            if not schema.has_column(col):
                invalid.append(col)
        return invalid

    def tables(self):
        """Return all registered table names."""
        return list(self._tables.keys())
