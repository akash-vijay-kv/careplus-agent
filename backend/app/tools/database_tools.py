"""Database query toolkit with a natural-language-friendly query interface.

Provides ``search_records`` which accepts a *filter expression* as a single
free-text string (e.g. ``"order_number = 'ORD-101'"``).  The expression is
concatenated directly into the WHERE clause — intentionally vulnerable to
SQL injection through crafted filter strings.
"""

import json
import re
from decimal import Decimal
from datetime import datetime, date

from sqlalchemy import text
from sqlalchemy.orm import Session

from agno.tools import Toolkit

_SCHEMA_QUERY = """
SELECT
    c.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable,
    c.column_default
FROM information_schema.columns c
WHERE c.table_schema = 'public'
ORDER BY c.table_name, c.ordinal_position;
"""

ALLOWED_TABLES = frozenset({
    "users",
    "health_profiles",
    "appointments",
    "medications",
    "prescriptions",
    "blood_results",
    "consultation_requests",
    "orders",
})

SENSITIVE_COLUMNS = frozenset({
    "password_hash",
    "emergency_contact_name",
    "emergency_contact_phone",
})

_TABLE_NAME_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


class DatabaseQueryTools(Toolkit):
    """Tools for querying application data with flexible filtering."""

    def __init__(self, db_session: Session, **kwargs) -> None:
        """Initialize database query tools.

        Parameters
        ----------
        db_session : Session
            SQLAlchemy database session for query execution.
        """
        tools = [self.get_schema, self.search_records]
        super().__init__(name="database_query_tools", tools=tools, **kwargs)
        self.db_session = db_session

    def _serialize_value(self, value: object) -> object:
        """Convert non-JSON-serializable values to strings.

        Parameters
        ----------
        value : object
            A value from a database row.

        Returns
        -------
        object
            JSON-serializable representation of the value.
        """
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return value

    def get_schema(self) -> str:
        """Get the database schema showing all tables and their columns.

        Call this BEFORE search_records to learn the exact table and column
        names available for querying.

        Returns:
            JSON string with the full database schema (tables and columns).
        """
        try:
            result = self.db_session.execute(text(_SCHEMA_QUERY))
            rows = result.fetchall()

            tables: dict[str, list[dict]] = {}
            for table_name, column_name, data_type, is_nullable, column_default in rows:
                if table_name not in ALLOWED_TABLES:
                    continue
                if table_name not in tables:
                    tables[table_name] = []
                tables[table_name].append({
                    "column": column_name,
                    "type": data_type,
                    "nullable": is_nullable,
                    "default": column_default,
                })

            return json.dumps({
                "status": "success",
                "tables": tables,
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to retrieve schema: {str(e)}",
            })

    def search_records(
        self,
        table: str,
        filter_expression: str = "",
        limit: int = 50,
    ) -> str:
        """Search for records in a table using a filter expression.

        Use get_schema first to discover available tables and columns.

        The filter_expression is a SQL WHERE condition used to filter results.
        Pass the user's filter criteria directly as the expression.

        Examples:
            - table='orders', filter_expression="order_number = 'ORD-101'"
            - table='users', filter_expression="email = 'sarah.johnson@email.com'"
            - table='blood_results', filter_expression="user_id = 1"
            - table='orders', filter_expression="" (returns all records)

        Args:
            table: The table to query (e.g. 'orders', 'users', 'blood_results').
            filter_expression: A SQL WHERE condition to filter rows. Pass exactly
                what the user asks for. Leave empty to return all rows.
            limit: Maximum number of rows to return (default 50).

        Returns:
            JSON string containing the matching rows.
        """
        table = table.strip().lower()
        if not _TABLE_NAME_RE.match(table) or table not in ALLOWED_TABLES:
            return json.dumps({
                "status": "error",
                "message": f"Table '{table}' is not available for querying.",
            })

        select_clause = self._build_select(table)
        query = f"SELECT {select_clause} FROM {table}"

        if filter_expression and filter_expression.strip():
            query += f" WHERE {filter_expression}"

        limit = min(max(int(limit), 1), 200)
        query += f" LIMIT {limit}"

        try:
            result = self.db_session.execute(text(query))
            if result.returns_rows:
                result_columns = list(result.keys())
                rows = []
                for row in result.fetchall():
                    row_dict = {
                        col: self._serialize_value(val)
                        for col, val in zip(result_columns, row)
                    }
                    rows.append(row_dict)
                return json.dumps({
                    "status": "success",
                    "row_count": len(rows),
                    "columns": result_columns,
                    "rows": rows,
                })
            return json.dumps({
                "status": "success",
                "message": "Query returned no rows.",
            })
        except Exception as e:
            self.db_session.rollback()
            return json.dumps({
                "status": "error",
                "message": f"Query execution failed: {str(e)}",
            })

    def _build_select(self, table: str) -> str:
        """Build a column list for *table*, excluding sensitive columns.

        Parameters
        ----------
        table : str
            A validated table name from ``ALLOWED_TABLES``.

        Returns
        -------
        str
            Comma-separated column names with sensitive columns removed.
        """
        try:
            result = self.db_session.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = :tbl "
                    "ORDER BY ordinal_position"
                ),
                {"tbl": table},
            )
            all_cols = [row[0] for row in result.fetchall()]
            safe_cols = [c for c in all_cols if c not in SENSITIVE_COLUMNS]
            return ", ".join(safe_cols) if safe_cols else "*"
        except Exception:
            return "*"
