"""Tests for the QueryBuilder API."""

from querycraft import QueryBuilder
from querycraft.nodes import Query
from querycraft.expressions import Column, Comparison, InExpression


class TestQueryBuilderAPI:
    def test_builder_creates_query(self):
        builder = QueryBuilder("users")
        query = builder.build()
        assert isinstance(query, Query)
        assert query.from_table == "users"

    def test_select_adds_columns(self):
        query = QueryBuilder("users").select("id", "name").build()
        assert len(query.select_columns) == 2

    def test_where_adds_condition(self):
        query = QueryBuilder("users").where("id", "=", 1).build()
        assert len(query.wheres) == 1
        assert isinstance(query.wheres[0], Comparison)

    def test_where_in_with_values(self):
        query = QueryBuilder("users").where_in("id", [1, 2, 3]).build()
        assert len(query.wheres) == 1
        assert isinstance(query.wheres[0], InExpression)
        assert query.wheres[0].source == [1, 2, 3]

    def test_chaining(self):
        query = (QueryBuilder("users")
            .select("name")
            .where("active", "=", True)
            .order_by("name")
            .limit(10)
            .build())
        assert query.from_table == "users"
        assert len(query.select_columns) == 1
        assert len(query.wheres) == 1
        assert len(query.order_by) == 1
        assert query.limit == 10

    def test_insert_builder(self):
        query = (QueryBuilder.insert_into("users")
            .columns("name", "email")
            .values("test", "test@test.com")
            .build())
        assert query.query_type == "insert"
        assert query.insert_table == "users"

    def test_update_builder(self):
        query = (QueryBuilder.update("users")
            .set("name", "new_name")
            .where("id", "=", 1)
            .build())
        assert query.query_type == "update"
        assert len(query.update_sets) == 1

    def test_delete_builder(self):
        query = (QueryBuilder.delete_from("users")
            .where("id", "=", 1)
            .build())
        assert query.query_type == "delete"
        assert query.delete_table == "users"
