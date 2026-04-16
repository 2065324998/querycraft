"""Fluent query builder API for constructing SQL queries."""

from querycraft.nodes import Query, Join, OrderByItem, CTE
from querycraft.expressions import (
    Column, Literal, RawSQL, Star, Comparison, LogicalOp,
    InExpression, ExistsExpression, BetweenExpression,
    IsNullExpression, FunctionCall, Expression,
)
from querycraft.compiler import Compiler


class QueryBuilder:
    """Builds SQL queries using a fluent interface.

    Example:
        query = (QueryBuilder("users")
            .select("name", "email")
            .where("active", "=", True)
            .order_by("name")
            .limit(10))
        sql, params = query.compile()
    """

    def __init__(self, table=None):
        self._query = Query()
        if table:
            self._query.from_table = table

    @classmethod
    def insert_into(cls, table):
        """Create an INSERT query builder."""
        builder = cls()
        builder._query.query_type = "insert"
        builder._query.insert_table = table
        return builder

    @classmethod
    def update(cls, table):
        """Create an UPDATE query builder."""
        builder = cls()
        builder._query.query_type = "update"
        builder._query.update_table = table
        return builder

    @classmethod
    def delete_from(cls, table):
        """Create a DELETE query builder."""
        builder = cls()
        builder._query.query_type = "delete"
        builder._query.delete_table = table
        return builder

    def select(self, *columns):
        """Add columns to the SELECT clause."""
        for col in columns:
            if isinstance(col, Expression):
                self._query.select_columns.append(col)
            elif isinstance(col, str) and col.strip() == "*":
                self._query.select_columns.append(Star())
            else:
                self._query.select_columns.append(Column(name=col))
        return self

    def distinct(self):
        """Add DISTINCT to the SELECT clause."""
        self._query.distinct = True
        return self

    def from_table(self, table, alias=None):
        """Set the FROM table."""
        self._query.from_table = table
        self._query.from_alias = alias
        return self

    def from_subquery(self, subquery, alias=None):
        """Set the FROM clause to a subquery."""
        if isinstance(subquery, QueryBuilder):
            self._query.from_subquery = subquery.build()
        else:
            self._query.from_subquery = subquery
        self._query.from_alias = alias
        return self

    def where(self, column, operator, value):
        """Add a WHERE condition."""
        col = Column(name=column) if isinstance(column, str) else column
        cond = Comparison(left=col, operator=operator, right=Literal(value=value))
        self._query.wheres.append(cond)
        return self

    def where_in(self, column, values_or_subquery):
        """Add a WHERE IN condition with values or a subquery."""
        col = Column(name=column) if isinstance(column, str) else column
        if isinstance(values_or_subquery, QueryBuilder):
            source = values_or_subquery.build()
        elif isinstance(values_or_subquery, Query):
            source = values_or_subquery
        else:
            source = list(values_or_subquery)
        self._query.wheres.append(InExpression(column=col, source=source))
        return self

    def where_not_in(self, column, values_or_subquery):
        """Add a WHERE NOT IN condition."""
        col = Column(name=column) if isinstance(column, str) else column
        if isinstance(values_or_subquery, QueryBuilder):
            source = values_or_subquery.build()
        elif isinstance(values_or_subquery, Query):
            source = values_or_subquery
        else:
            source = list(values_or_subquery)
        self._query.wheres.append(
            InExpression(column=col, source=source, negated=True)
        )
        return self

    def where_exists(self, subquery):
        """Add a WHERE EXISTS (subquery) condition."""
        if isinstance(subquery, QueryBuilder):
            subquery = subquery.build()
        self._query.wheres.append(ExistsExpression(subquery=subquery))
        return self

    def where_between(self, column, low, high):
        """Add a WHERE BETWEEN condition."""
        col = Column(name=column) if isinstance(column, str) else column
        self._query.wheres.append(BetweenExpression(
            column=col,
            low=Literal(value=low),
            high=Literal(value=high),
        ))
        return self

    def where_null(self, column):
        """Add a WHERE IS NULL condition."""
        col = Column(name=column) if isinstance(column, str) else column
        self._query.wheres.append(IsNullExpression(column=col))
        return self

    def where_not_null(self, column):
        """Add a WHERE IS NOT NULL condition."""
        col = Column(name=column) if isinstance(column, str) else column
        self._query.wheres.append(IsNullExpression(column=col, negated=True))
        return self

    def join(self, table, on=None, alias=None, join_type="INNER"):
        """Add a JOIN clause.

        Args:
            table: table name (str) or QueryBuilder/Query for subquery join
            on: raw SQL condition string or Expression object
            alias: table alias
            join_type: INNER, LEFT, RIGHT, or CROSS
        """
        join_node = Join(join_type=join_type, alias=alias)
        if isinstance(table, QueryBuilder):
            join_node.subquery = table.build()
        elif isinstance(table, Query):
            join_node.subquery = table
        else:
            join_node.table = table

        if isinstance(on, str):
            join_node.condition = RawSQL(sql=on)
        elif isinstance(on, Expression):
            join_node.condition = on

        self._query.joins.append(join_node)
        return self

    def left_join(self, table, on=None, alias=None):
        """Add a LEFT JOIN clause."""
        return self.join(table, on=on, alias=alias, join_type="LEFT")

    def group_by(self, *columns):
        """Add GROUP BY columns."""
        self._query.group_by.extend(columns)
        return self

    def having(self, column, operator, value):
        """Add a HAVING condition."""
        col = Column(name=column) if isinstance(column, str) else column
        cond = Comparison(left=col, operator=operator, right=Literal(value=value))
        self._query.havings.append(cond)
        return self

    def order_by(self, column, direction="ASC"):
        """Add an ORDER BY item."""
        self._query.order_by.append(
            OrderByItem(column=column, direction=direction)
        )
        return self

    def limit(self, n):
        """Set the LIMIT value."""
        self._query.limit = n
        return self

    def offset(self, n):
        """Set the OFFSET value."""
        self._query.offset = n
        return self

    def columns(self, *cols):
        """Set INSERT column names."""
        self._query.insert_columns = list(cols)
        return self

    def values(self, *vals):
        """Set INSERT values."""
        self._query.insert_values = list(vals)
        return self

    def set(self, column, value):
        """Add a SET clause for UPDATE."""
        self._query.update_sets.append((column, value))
        return self

    def with_cte(self, name, subquery, recursive=False):
        """Add a CTE (WITH clause).

        Args:
            name: CTE name used to reference it in the main query
            subquery: QueryBuilder or Query defining the CTE body
            recursive: whether this is a RECURSIVE CTE
        """
        if isinstance(subquery, QueryBuilder):
            cte_query = subquery.build()
        else:
            cte_query = subquery
        self._query.ctes.append(
            CTE(name=name, query=cte_query, recursive=recursive)
        )
        return self

    def union(self, other, all=False):
        """Combine with another query using UNION."""
        self._query.compound_op = "UNION"
        self._query.compound_all = all
        if isinstance(other, QueryBuilder):
            self._query.compound_right = other.build()
        else:
            self._query.compound_right = other
        return self

    def intersect(self, other, all=False):
        """Combine with another query using INTERSECT."""
        self._query.compound_op = "INTERSECT"
        self._query.compound_all = all
        if isinstance(other, QueryBuilder):
            self._query.compound_right = other.build()
        else:
            self._query.compound_right = other
        return self

    def except_(self, other, all=False):
        """Combine with another query using EXCEPT."""
        self._query.compound_op = "EXCEPT"
        self._query.compound_all = all
        if isinstance(other, QueryBuilder):
            self._query.compound_right = other.build()
        else:
            self._query.compound_right = other
        return self

    def build(self):
        """Return the underlying Query AST node."""
        return self._query

    def compile(self, compiler=None):
        """Compile the query into (sql_string, params_tuple)."""
        if compiler is None:
            compiler = Compiler()
        return compiler.compile(self._query)
