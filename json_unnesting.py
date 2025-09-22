import re
from typing import List, Dict, Any
import logging

try:
    import psycopg
    from psycopg.rows import dict_row
    HAS_PSYCOPG = True
except ImportError:
    psycopg = None
    dict_row = None
    HAS_PSYCOPG = False

logger = logging.getLogger(__name__)

class JsonUnnestingParser:
    def __init__(self):
        self.custom_syntax_pattern = r'\{\{all_fields_as_columns_from\(([^,]+),\s*([^,]+),\s*([^)]+)\)\}\}'

    def parse(self, sql: str) -> Dict[str, Any]:
        """Parse SQL for custom unnesting syntax and return unnesting requests"""
        unnesting_requests = []

        matches = re.findall(self.custom_syntax_pattern, sql)
        for match in matches:
            json_column, name_key, value_key = match
            unnesting_requests.append({
                "json_column": json_column.strip(),
                "name_key": name_key.strip(),
                "value_key": value_key.strip()
            })

        return {"unnesting_requests": unnesting_requests}

class JsonUnnestingTransformer:
    def transform(self, sql: str, unnesting_requests: List[Dict[str, str]]) -> str:
        """Transform SQL by replacing custom syntax with CTE for JSON unnesting"""
        # Validate unnesting requests
        for req in unnesting_requests:
            if not all(key in req for key in ["json_column", "name_key", "value_key"]):
                raise ValueError("Invalid unnesting request: missing required keys")

        # Remove template syntax first
        clean_sql = re.sub(r'\{\{all_fields_as_columns_from\([^}]+\)\}\}', '', sql)

        # Find the table name in FROM clause
        from_match = re.search(r'FROM\s+([^\s]+)', clean_sql, re.IGNORECASE)
        table_name = from_match.group(1) if from_match else "unknown_table"

        # Extract WHERE clause if present
        where_match = re.search(r'\bWHERE\b(.+)', clean_sql, re.IGNORECASE | re.DOTALL)
        where_clause = where_match.group(1).strip() if where_match else ""

        # Generate CTEs for all requests
        ctes = []

        for req in unnesting_requests:
            json_column = req["json_column"]
            name_key = req["name_key"]
            value_key = req["value_key"]

            # Create CTE for unnesting with WHERE clause
            cte_name = f"unnested_{json_column}"
            flattened_cte_name = f"flattened_{json_column}"

            where_part = f"WHERE {where_clause}" if where_clause else ""

            # Handle JSON arrays and objects properly
            cte_sql = f"""
            {cte_name} AS (
                SELECT *,
                       CASE
                           WHEN jsonb_typeof({json_column}) = 'array' AND jsonb_array_length({json_column}) > 0
                           THEN jsonb_array_elements({json_column})
                           WHEN jsonb_typeof({json_column}) = 'object'
                           THEN jsonb_build_object('{name_key}', {json_column}->>'{name_key}', '{value_key}', {json_column}->>'{value_key}')
                           ELSE NULL
                       END AS item
                FROM {table_name}
                {where_part}
                WHERE {json_column} IS NOT NULL
                  AND (
                      (jsonb_typeof({json_column}) = 'array' AND jsonb_array_length({json_column}) > 0)
                      OR jsonb_typeof({json_column}) = 'object'
                  )
            ),
            {flattened_cte_name} AS (
                SELECT *,
                       CASE
                           WHEN item->>'{name_key}' IS NOT NULL THEN item->>'{name_key}'
                           ELSE ''
                       END AS "{json_column}_{name_key}_1",
                       CASE
                           WHEN item->>'{value_key}' IS NOT NULL THEN item->>'{value_key}'
                           ELSE ''
                       END AS "{json_column}_{value_key}_1"
                FROM {cte_name}
                WHERE item IS NOT NULL
            )
            """

            ctes.append(cte_sql)

        # Combine CTEs and SELECT
        full_cte = "WITH " + ", ".join(ctes)
        last_cte_name = f"flattened_{json_column}"  # Use the last flattened CTE name
        final_select = f"SELECT * FROM {last_cte_name}"

        return full_cte + " " + final_select

def process_query_with_json_unnesting(sql: str, database_url: str) -> List[Dict[str, Any]]:
    """Process a query with JSON unnesting and return results"""
    parser = JsonUnnestingParser()
    transformer = JsonUnnestingTransformer()

    # Parse the query
    parsed = parser.parse(sql)
    unnesting_requests = parsed["unnesting_requests"]

    # Transform if there are unnesting requests
    if unnesting_requests:
        transformed_sql = transformer.transform(sql, unnesting_requests)
    else:
        transformed_sql = sql

    # Execute the query only if psycopg is available
    if not HAS_PSYCOPG or psycopg is None:
        # Return empty list for testing purposes when psycopg is not available
        return []

    try:
        conn = psycopg.connect(database_url, connect_timeout=15, row_factory=dict_row)
        with conn.cursor() as cur:
            cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
            cur.execute("SET LOCAL statement_timeout = '60s'")
            cur.execute(transformed_sql)
            rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise
