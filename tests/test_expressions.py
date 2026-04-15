"""Tests for expression rendering."""

from querycraft import Compiler, Column, Literal, Star, FunctionCall, Comparison
from querycraft.expressions import LogicalOp


class TestExpressionRendering:
    def setup_method(self):
        self.compiler = Compiler()

    def test_column(self):
        expr = Column(name="id")
        assert self.compiler._render_expr(expr) == "id"

    def test_column_with_table(self):
        expr = Column(name="id", table="users")
        assert self.compiler._render_expr(expr) == "users.id"

    def test_literal(self):
        expr = Literal(value=42)
        assert self.compiler._render_expr(expr) == "?"

    def test_star(self):
        expr = Star()
        assert self.compiler._render_expr(expr) == "*"

    def test_star_with_table(self):
        expr = Star(table="users")
        assert self.compiler._render_expr(expr) == "users.*"

    def test_comparison(self):
        expr = Comparison(
            left=Column(name="age"),
            operator=">=",
            right=Literal(value=18),
        )
        assert self.compiler._render_expr(expr) == "age >= ?"

    def test_function_call(self):
        expr = FunctionCall(name="COUNT", args=[Star()])
        assert self.compiler._render_expr(expr) == "COUNT(*)"

    def test_function_call_with_alias(self):
        expr = FunctionCall(name="SUM", args=[Column(name="total")],
                           alias="grand_total")
        assert self.compiler._render_expr(expr) == "SUM(total) AS grand_total"

    def test_logical_or(self):
        expr = LogicalOp(
            operator="OR",
            children=[
                Comparison(Column("a"), "=", Literal(1)),
                Comparison(Column("b"), "=", Literal(2)),
            ],
        )
        result = self.compiler._render_expr(expr)
        assert result == "(a = ? OR b = ?)"
