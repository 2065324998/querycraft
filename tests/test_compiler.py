"""Tests for the SQL compiler with simple (non-subquery) queries."""

from querycraft import QueryBuilder, Compiler


class TestSelectCompilation:
    def test_select_all(self):
        sql, params = QueryBuilder("users").compile()
        assert sql == "SELECT * FROM users"
        assert params == ()

    def test_select_columns(self):
        sql, params = QueryBuilder("users").select("name", "email").compile()
        assert sql == "SELECT name, email FROM users"
        assert params == ()

    def test_select_distinct(self):
        sql, params = QueryBuilder("users").select("name").distinct().compile()
        assert sql == "SELECT DISTINCT name FROM users"
        assert params == ()

    def test_where_single(self):
        sql, params = QueryBuilder("users").where("active", "=", True).compile()
        assert sql == "SELECT * FROM users WHERE active = ?"
        assert params == (True,)

    def test_where_multiple(self):
        query = (QueryBuilder("users")
            .where("active", "=", True)
            .where("age", ">=", 18))
        sql, params = query.compile()
        assert sql == "SELECT * FROM users WHERE active = ? AND age >= ?"
        assert params == (True, 18)

    def test_where_in_values(self):
        query = QueryBuilder("users").where_in("status", ["active", "pending"])
        sql, params = query.compile()
        assert "IN (?, ?)" in sql
        assert params == ("active", "pending")

    def test_where_between(self):
        query = QueryBuilder("products").where_between("price", 10, 100)
        sql, params = query.compile()
        assert "BETWEEN ? AND ?" in sql
        assert params == (10, 100)

    def test_where_null(self):
        sql, params = QueryBuilder("users").where_null("deleted_at").compile()
        assert "IS NULL" in sql
        assert params == ()

    def test_where_not_null(self):
        sql, params = QueryBuilder("users").where_not_null("email").compile()
        assert "IS NOT NULL" in sql
        assert params == ()

    def test_join_simple(self):
        query = (QueryBuilder("users")
            .select("users.name", "orders.total")
            .join("orders", on="users.id = orders.user_id"))
        sql, params = query.compile()
        assert "INNER JOIN orders ON users.id = orders.user_id" in sql
        assert params == ()

    def test_left_join(self):
        query = (QueryBuilder("users")
            .left_join("profiles", on="users.id = profiles.user_id"))
        sql, params = query.compile()
        assert "LEFT JOIN profiles ON users.id = profiles.user_id" in sql

    def test_group_by(self):
        query = (QueryBuilder("orders")
            .select("status")
            .group_by("status"))
        sql, params = query.compile()
        assert "GROUP BY status" in sql

    def test_having(self):
        query = (QueryBuilder("orders")
            .select("status")
            .group_by("status")
            .having("COUNT(*)", ">", 5))
        sql, params = query.compile()
        assert "HAVING COUNT(*) > ?" in sql
        assert params == (5,)

    def test_order_by(self):
        query = (QueryBuilder("users")
            .select("name")
            .order_by("name", "ASC")
            .order_by("created_at", "DESC"))
        sql, params = query.compile()
        assert "ORDER BY name ASC, created_at DESC" in sql

    def test_limit_offset(self):
        query = QueryBuilder("users").limit(10).offset(20)
        sql, params = query.compile()
        assert "LIMIT ?" in sql
        assert "OFFSET ?" in sql
        assert params == (10, 20)

    def test_where_with_limit(self):
        query = (QueryBuilder("users")
            .where("active", "=", True)
            .limit(5))
        sql, params = query.compile()
        assert params == (True, 5)

    def test_full_query(self):
        query = (QueryBuilder("orders")
            .select("status", "COUNT(*) AS cnt")
            .where("created_at", ">", "2024-01-01")
            .group_by("status")
            .having("COUNT(*)", ">", 10)
            .order_by("cnt", "DESC")
            .limit(5))
        sql, params = query.compile()
        assert params == ("2024-01-01", 10, 5)


class TestInsertCompilation:
    def test_insert(self):
        query = (QueryBuilder.insert_into("users")
            .columns("name", "email")
            .values("Alice", "alice@example.com"))
        sql, params = query.compile()
        assert sql == "INSERT INTO users (name, email) VALUES (?, ?)"
        assert params == ("Alice", "alice@example.com")


class TestUpdateCompilation:
    def test_update(self):
        query = (QueryBuilder.update("users")
            .set("name", "Bob")
            .set("email", "bob@example.com")
            .where("id", "=", 42))
        sql, params = query.compile()
        assert "UPDATE users SET name = ?, email = ? WHERE id = ?" in sql
        assert params == ("Bob", "bob@example.com", 42)


class TestDeleteCompilation:
    def test_delete(self):
        query = (QueryBuilder.delete_from("users")
            .where("active", "=", False))
        sql, params = query.compile()
        assert sql == "DELETE FROM users WHERE active = ?"
        assert params == (False,)
