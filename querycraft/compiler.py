"""SQL compiler that converts Query AST nodes into parameterized SQL.

The compiler uses a two-pass approach for clean separation of concerns:
  1. Render pass: walks the AST to generate SQL strings with placeholders
  2. Collection pass: walks the AST to gather parameter values

This keeps the rendering logic focused on SQL string generation while
parameter collection handles value extraction independently.
"""

from querycraft.nodes import Query, Join, OrderByItem
from querycraft.expressions import (
    Expression, Column, Literal, RawSQL, Comparison, LogicalOp,
    InExpression, ExistsExpression, BetweenExpression, IsNullExpression,
    FunctionCall, Star,
)


class CompilationError(Exception):
    """Raised when a query cannot be compiled."""
    pass


class Compiler:
    """Compiles Query AST nodes into SQL strings with parameter lists."""

    def __init__(self, placeholder="?"):
        self.placeholder = placeholder

    def compile(self, query):
        """Compile a Query node into (sql_string, params_tuple).

        Performs a render pass to generate SQL, then a separate
        parameter collection pass to gather bound values.
        """
        if query.query_type == "insert":
            sql = self._render_insert(query)
            params = self._collect_insert_params(query)
        elif query.query_type == "update":
            sql = self._render_update(query)
            params = self._collect_update_params(query)
        elif query.query_type == "delete":
            sql = self._render_delete(query)
            params = self._collect_delete_params(query)
        else:
            sql = self._render_select(query)
            params = self._collect_select_params(query)
        return sql, tuple(params)

    # ── Render methods (Pass 1: SQL generation) ──────────────────

    def _render_select(self, query):
        """Render a SELECT query to a SQL string."""
        parts = []

        # CTE clause (WITH)
        if query.ctes:
            cte_defs = []
            for cte in query.ctes:
                cte_sql = self._render_select(cte.query)
                cte_defs.append(f"{cte.name} AS ({cte_sql})")
            has_recursive = any(c.recursive for c in query.ctes)
            keyword = "WITH RECURSIVE" if has_recursive else "WITH"
            parts.append(f"{keyword} {', '.join(cte_defs)}")

        # SELECT clause
        select_kw = "SELECT DISTINCT" if query.distinct else "SELECT"
        if not query.select_columns:
            parts.append(f"{select_kw} *")
        else:
            cols = [self._render_expr(col) for col in query.select_columns]
            parts.append(f"{select_kw} {', '.join(cols)}")

        # FROM clause
        if query.from_subquery:
            sub_sql = self._render_select(query.from_subquery)
            alias = f" AS {query.from_alias}" if query.from_alias else ""
            parts.append(f"FROM ({sub_sql}){alias}")
        elif query.from_table:
            alias = f" AS {query.from_alias}" if query.from_alias else ""
            parts.append(f"FROM {query.from_table}{alias}")

        # JOIN clauses
        for join in query.joins:
            parts.append(self._render_join(join))

        # WHERE clause
        if query.wheres:
            conditions = [self._render_expr(c) for c in query.wheres]
            parts.append(f"WHERE {' AND '.join(conditions)}")

        # GROUP BY
        if query.group_by:
            parts.append(f"GROUP BY {', '.join(query.group_by)}")

        # HAVING
        if query.havings:
            conditions = [self._render_expr(c) for c in query.havings]
            parts.append(f"HAVING {' AND '.join(conditions)}")

        # ORDER BY
        if query.order_by:
            items = [f"{item.column} {item.direction}" for item in query.order_by]
            parts.append(f"ORDER BY {', '.join(items)}")

        # LIMIT / OFFSET
        if query.limit is not None:
            parts.append(f"LIMIT {self.placeholder}")
        if query.offset is not None:
            parts.append(f"OFFSET {self.placeholder}")

        # Compound query (UNION/INTERSECT/EXCEPT)
        if query.compound_op:
            op = query.compound_op
            if query.compound_all:
                op += " ALL"
            right_sql = self._render_select(query.compound_right)
            parts.append(op)
            parts.append(right_sql)

        return " ".join(parts)

    def _render_join(self, join):
        """Render a JOIN clause to SQL."""
        if join.subquery:
            sub_sql = self._render_select(join.subquery)
            alias = f" AS {join.alias}" if join.alias else ""
            table_part = f"({sub_sql}){alias}"
        else:
            alias = f" AS {join.alias}" if join.alias else ""
            table_part = f"{join.table}{alias}"

        if join.condition:
            cond_sql = self._render_expr(join.condition)
            return f"{join.join_type} JOIN {table_part} ON {cond_sql}"
        return f"{join.join_type} JOIN {table_part}"

    def _render_expr(self, expr):
        """Render an expression node to SQL."""
        if isinstance(expr, Column):
            return str(expr)
        elif isinstance(expr, Literal):
            return self.placeholder
        elif isinstance(expr, RawSQL):
            return expr.sql
        elif isinstance(expr, Star):
            if expr.table:
                return f"{expr.table}.*"
            return "*"
        elif isinstance(expr, Comparison):
            left = self._render_expr(expr.left)
            right = self._render_expr(expr.right)
            return f"{left} {expr.operator} {right}"
        elif isinstance(expr, LogicalOp):
            parts = [self._render_expr(child) for child in expr.children]
            return f"({f' {expr.operator} '.join(parts)})"
        elif isinstance(expr, InExpression):
            col = self._render_expr(expr.column)
            neg = "NOT " if expr.negated else ""
            if isinstance(expr.source, Query):
                sub_sql = self._render_select(expr.source)
                return f"{col} {neg}IN ({sub_sql})"
            else:
                placeholders = ", ".join(self.placeholder for _ in expr.source)
                return f"{col} {neg}IN ({placeholders})"
        elif isinstance(expr, ExistsExpression):
            sub_sql = self._render_select(expr.subquery)
            neg = "NOT " if expr.negated else ""
            return f"{neg}EXISTS ({sub_sql})"
        elif isinstance(expr, BetweenExpression):
            col = self._render_expr(expr.column)
            low = self._render_expr(expr.low)
            high = self._render_expr(expr.high)
            neg = "NOT " if expr.negated else ""
            return f"{col} {neg}BETWEEN {low} AND {high}"
        elif isinstance(expr, IsNullExpression):
            col = self._render_expr(expr.column)
            if expr.negated:
                return f"{col} IS NOT NULL"
            return f"{col} IS NULL"
        elif isinstance(expr, FunctionCall):
            args = ", ".join(self._render_expr(a) for a in expr.args)
            result = f"{expr.name}({args})"
            if expr.alias:
                result += f" AS {expr.alias}"
            return result
        else:
            raise CompilationError(f"Unknown expression type: {type(expr)}")

    def _render_insert(self, query):
        """Render an INSERT query."""
        cols = ", ".join(query.insert_columns)
        vals = ", ".join(self.placeholder for _ in query.insert_values)
        return f"INSERT INTO {query.insert_table} ({cols}) VALUES ({vals})"

    def _render_update(self, query):
        """Render an UPDATE query."""
        parts = [f"UPDATE {query.update_table}"]
        set_parts = [f"{col} = {self.placeholder}" for col, _ in query.update_sets]
        parts.append(f"SET {', '.join(set_parts)}")
        if query.wheres:
            conditions = [self._render_expr(c) for c in query.wheres]
            parts.append(f"WHERE {' AND '.join(conditions)}")
        return " ".join(parts)

    def _render_delete(self, query):
        """Render a DELETE query."""
        parts = [f"DELETE FROM {query.delete_table}"]
        if query.wheres:
            conditions = [self._render_expr(c) for c in query.wheres]
            parts.append(f"WHERE {' AND '.join(conditions)}")
        return " ".join(parts)

    # ── Parameter collection methods (Pass 2: value gathering) ───

    def _collect_select_params(self, query):
        """Collect parameters for a SELECT query by walking the AST.

        Parameters are collected in two phases:
          1. Scalar parameters from conditions (WHERE, HAVING) and
             query-level values (LIMIT, OFFSET)
          2. Subquery parameters from all nested queries

        This separation ensures subquery parameters are collected
        once via _find_all_subqueries rather than being duplicated
        during condition traversal.
        """
        params = []

        # Phase 1: Collect scalar parameters from conditions
        for condition in query.wheres:
            self._collect_condition_params(condition, params)

        for condition in query.havings:
            self._collect_condition_params(condition, params)

        if query.limit is not None:
            params.append(query.limit)
        if query.offset is not None:
            params.append(query.offset)

        # Phase 2: Collect parameters from all subqueries
        for subquery in self._find_all_subqueries(query):
            params.extend(self._collect_select_params(subquery))

        # Compound query parameters
        if query.compound_right:
            params.extend(self._collect_select_params(query.compound_right))

        return params

    def _collect_condition_params(self, expr, params):
        """Collect scalar parameter values from an expression tree.

        Subquery parameters are NOT collected here — they are gathered
        by _find_all_subqueries() and collected in Phase 2 of
        _collect_select_params to avoid duplication.
        """
        if isinstance(expr, Literal):
            params.append(expr.value)
        elif isinstance(expr, Comparison):
            self._collect_condition_params(expr.left, params)
            self._collect_condition_params(expr.right, params)
        elif isinstance(expr, LogicalOp):
            for child in expr.children:
                self._collect_condition_params(child, params)
        elif isinstance(expr, InExpression):
            # Column ref has no params
            # For value lists, collect each value
            # For subqueries, params are handled by _find_all_subqueries
            if not isinstance(expr.source, Query):
                for val in expr.source:
                    params.append(val)
        elif isinstance(expr, ExistsExpression):
            # Subquery params handled by _find_all_subqueries
            pass
        elif isinstance(expr, BetweenExpression):
            self._collect_condition_params(expr.column, params)
            self._collect_condition_params(expr.low, params)
            self._collect_condition_params(expr.high, params)
        elif isinstance(expr, FunctionCall):
            for arg in expr.args:
                self._collect_condition_params(arg, params)

    def _find_all_subqueries(self, query):
        """Find all subqueries referenced anywhere in this query.

        Searches FROM, JOIN, WHERE, and HAVING clauses for nested
        Query objects. Does not recurse into found subqueries — that
        is handled by _collect_select_params when it processes each one.
        """
        subqueries = []
        if query.from_subquery:
            subqueries.append(query.from_subquery)
        for join in query.joins:
            if join.subquery:
                subqueries.append(join.subquery)
        for condition in query.wheres:
            self._find_subqueries_in_expr(condition, subqueries)
        for condition in query.havings:
            self._find_subqueries_in_expr(condition, subqueries)
        return subqueries

    def _find_subqueries_in_expr(self, expr, result):
        """Recursively find subquery references in an expression tree."""
        if isinstance(expr, InExpression):
            if isinstance(expr.source, Query):
                result.append(expr.source)
        elif isinstance(expr, ExistsExpression):
            result.append(expr.subquery)
        elif isinstance(expr, Comparison):
            self._find_subqueries_in_expr(expr.left, result)
            self._find_subqueries_in_expr(expr.right, result)
        elif isinstance(expr, LogicalOp):
            for child in expr.children:
                self._find_subqueries_in_expr(child, result)

    def _collect_insert_params(self, query):
        """Collect parameters for an INSERT query."""
        return list(query.insert_values)

    def _collect_update_params(self, query):
        """Collect parameters for an UPDATE query."""
        params = [val for _, val in query.update_sets]
        for condition in query.wheres:
            self._collect_condition_params(condition, params)
        return params

    def _collect_delete_params(self, query):
        """Collect parameters for a DELETE query."""
        params = []
        for condition in query.wheres:
            self._collect_condition_params(condition, params)
        return params
