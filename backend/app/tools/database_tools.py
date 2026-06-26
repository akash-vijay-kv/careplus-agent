"""Database query toolkit for executing arbitrary SQL queries."""

import json
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


class DatabaseQueryTools(Toolkit):
    """Tools for executing database queries directly."""

    def __init__(self, db_session: Session, **kwargs):
        """Initialize database query tools.

        Parameters
        ----------
        db_session : Session
            SQLAlchemy database session for query execution.
        """
        tools = [self.get_schema, self.execute_query]
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

        Call this BEFORE execute_query to learn the exact table and column names.

        Returns:
            JSON string with the full database schema (tables and columns).
        """
        try:
            result = self.db_session.execute(text(_SCHEMA_QUERY))
            rows = result.fetchall()

            tables: dict[str, list[dict]] = {}
            for table_name, column_name, data_type, is_nullable, column_default in rows:
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

    def execute_query(self, query: str) -> str:
        """Execute a SQL query against the database and return results.

        IMPORTANT: Call get_schema first to learn the exact table and column names before writing a query.

        Args:
            query: The SQL query string to execute.

        Returns:
            JSON string containing the query results as a list of row objects.
        """
        try:
            result = self.db_session.execute(text(query))

            if result.returns_rows:
                columns = list(result.keys())
                rows = []
                for row in result.fetchall():
                    row_dict = {
                        col: self._serialize_value(val)
                        for col, val in zip(columns, row)
                    }
                    rows.append(row_dict)

                return json.dumps({
                    "status": "success",
                    "row_count": len(rows),
                    "columns": columns,
                    "rows": rows,
                })

            self.db_session.commit()
            return json.dumps({
                "status": "success",
                "message": "Query executed successfully.",
                "rows_affected": result.rowcount,
            })

        except Exception as e:
            self.db_session.rollback()
            return json.dumps({
                "status": "error",
                "message": f"Query execution failed: {str(e)}",
            })
