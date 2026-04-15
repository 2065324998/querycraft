# QueryCraft

A Python SQL query builder that generates parameterized SQL queries.

## Features

- Fluent query builder API for SELECT, INSERT, UPDATE, DELETE
- Parameterized queries with `?` placeholders
- Support for subqueries (FROM, JOIN, WHERE IN, EXISTS)
- Schema validation
- Multiple SQL dialect support

## Usage

```python
from querycraft import QueryBuilder

query = QueryBuilder("users").select("name", "email").where("active", "=", True)
sql, params = query.compile()
# sql: "SELECT name, email FROM users WHERE active = ?"
# params: (True,)
```

## Installation

```bash
pip install -e ".[dev]"
```

## Testing

```bash
pytest tests/ -v
```
