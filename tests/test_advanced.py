"""Tests for CTE and compound query features."""

from querycraft import QueryBuilder
from querycraft.nodes import CTE


class TestCTEBuilder:
    def test_with_cte_adds_cte(self):
        cte = QueryBuilder("products").select("id", "name")
        query = QueryBuilder("p").with_cte("p", cte).build()
        assert len(query.ctes) == 1
        assert query.ctes[0].name == "p"

    def test_multiple_ctes(self):
        cte1 = QueryBuilder("users").select("id")
        cte2 = QueryBuilder("orders").select("id")
        query = (QueryBuilder("u")
            .with_cte("u", cte1)
            .with_cte("o", cte2)
            .build())
        assert len(query.ctes) == 2

    def test_recursive_cte_flag(self):
        cte = QueryBuilder("nodes").select("id")
        query = QueryBuilder("tree").with_cte("tree", cte, recursive=True).build()
        assert query.ctes[0].recursive is True


class TestCompoundBuilder:
    def test_union_sets_fields(self):
        left = QueryBuilder("t1").select("a")
        right = QueryBuilder("t2").select("b")
        left.union(right)
        query = left.build()
        assert query.compound_op == "UNION"
        assert query.compound_right is not None
        assert query.compound_all is False

    def test_union_all_flag(self):
        left = QueryBuilder("t1").select("a")
        right = QueryBuilder("t2").select("b")
        left.union(right, all=True)
        assert left.build().compound_all is True

    def test_intersect_sets_op(self):
        left = QueryBuilder("t1").select("a")
        right = QueryBuilder("t2").select("b")
        left.intersect(right)
        assert left.build().compound_op == "INTERSECT"

    def test_except_sets_op(self):
        left = QueryBuilder("t1").select("a")
        right = QueryBuilder("t2").select("b")
        left.except_(right)
        assert left.build().compound_op == "EXCEPT"


class TestCTECompilation:
    def test_simple_cte_rendering(self):
        cte = QueryBuilder("products").select("id", "name")
        query = QueryBuilder("products").select("*").with_cte("products", cte)
        sql, params = query.compile()
        assert "WITH products AS (SELECT id, name FROM products)" in sql
        assert params == ()

    def test_recursive_cte_keyword(self):
        base = QueryBuilder("nodes").select("id", "parent_id").where_null("parent_id")
        query = QueryBuilder("tree").select("*").with_cte("tree", base, recursive=True)
        sql, params = query.compile()
        assert "WITH RECURSIVE" in sql
        assert "IS NULL" in sql
        assert params == ()

    def test_multiple_cte_rendering(self):
        cte1 = QueryBuilder("users").select("id", "name")
        cte2 = QueryBuilder("orders").select("user_id", "total")
        query = (QueryBuilder("u")
            .select("u.name", "o.total")
            .with_cte("u", cte1)
            .with_cte("o", cte2)
            .join("o", on="u.id = o.user_id"))
        sql, params = query.compile()
        assert "WITH u AS" in sql
        assert ", o AS" in sql
        assert params == ()


class TestCompoundCompilation:
    def test_union_rendering(self):
        left = QueryBuilder("users").select("name")
        right = QueryBuilder("admins").select("name")
        left.union(right)
        sql, params = left.compile()
        assert "UNION" in sql
        assert "SELECT name FROM users" in sql
        assert "SELECT name FROM admins" in sql
        assert params == ()

    def test_union_all_rendering(self):
        left = QueryBuilder("t1").select("a")
        right = QueryBuilder("t2").select("a")
        left.union(right, all=True)
        sql, params = left.compile()
        assert "UNION ALL" in sql
        assert params == ()

    def test_intersect_rendering(self):
        left = QueryBuilder("t1").select("id")
        right = QueryBuilder("t2").select("id")
        left.intersect(right)
        sql, params = left.compile()
        assert "INTERSECT" in sql
        assert params == ()

    def test_except_rendering(self):
        left = QueryBuilder("t1").select("id")
        right = QueryBuilder("t2").select("id")
        left.except_(right)
        sql, params = left.compile()
        assert "EXCEPT" in sql
        assert params == ()

    def test_compound_no_params(self):
        left = QueryBuilder("t1").select("a")
        right = QueryBuilder("t2").select("a")
        left.union(right)
        sql, params = left.compile()
        assert params == ()
