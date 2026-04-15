"""Tests for schema validation."""

from querycraft.schema import ColumnDef, TableSchema, SchemaRegistry


class TestTableSchema:
    def test_has_column(self):
        schema = TableSchema("users", [
            ColumnDef("id", "INTEGER", primary_key=True),
            ColumnDef("name", "TEXT"),
        ])
        assert schema.has_column("id")
        assert schema.has_column("name")
        assert not schema.has_column("email")

    def test_column_names(self):
        schema = TableSchema("users", [
            ColumnDef("id", "INTEGER"),
            ColumnDef("name", "TEXT"),
            ColumnDef("email", "TEXT"),
        ])
        assert schema.column_names() == ["id", "name", "email"]


class TestSchemaRegistry:
    def test_register_and_get(self):
        registry = SchemaRegistry()
        schema = TableSchema("users", [ColumnDef("id", "INTEGER")])
        registry.register(schema)
        assert registry.get("users") == schema
        assert registry.get("nonexistent") is None

    def test_validate_columns(self):
        registry = SchemaRegistry()
        registry.register(TableSchema("users", [
            ColumnDef("id", "INTEGER"),
            ColumnDef("name", "TEXT"),
        ]))
        assert registry.validate_columns("users", ["id", "name"]) == []
        assert registry.validate_columns("users", ["id", "foo"]) == ["foo"]

    def test_validate_unregistered_table(self):
        registry = SchemaRegistry()
        assert registry.validate_columns("unknown", ["id"]) == []

    def test_tables(self):
        registry = SchemaRegistry()
        registry.register(TableSchema("users", []))
        registry.register(TableSchema("orders", []))
        assert set(registry.tables()) == {"users", "orders"}
