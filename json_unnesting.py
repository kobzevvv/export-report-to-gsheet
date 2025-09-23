import re
from typing import List, Dict, Any, Set
import logging
import json

try:
    import psycopg
    from psycopg.rows import dict_row
    HAS_PSYCOPG = True
except ImportError:
    psycopg = None
    dict_row = None
    HAS_PSYCOPG = False

logger = logging.getLogger(__name__)

# Removed the complex FieldDiscovery class - now using explicit field lists instead

class JsonUnnestingParser:
    def __init__(self):
        # Updated pattern to capture fields_as_columns_from with variable field list
        self.custom_syntax_pattern = r'\{\{fields_as_columns_from\(([^,]+),\s*([^,]+),\s*([^,]+),\s*(.+)\)\}\}'

    def parse(self, sql: str) -> Dict[str, Any]:
        """Parse SQL for custom unnesting syntax and return unnesting requests"""
        unnesting_requests = []

        matches = re.findall(self.custom_syntax_pattern, sql, re.DOTALL)
        for match in matches:
            json_column, name_key, value_key, field_list_str = match
            
            # Parse the field list - extract quoted strings
            field_titles = self._parse_field_list(field_list_str)
            
            unnesting_requests.append({
                "json_column": json_column.strip(),
                "name_key": name_key.strip(),
                "value_key": value_key.strip(),
                "field_titles": field_titles
            })

        return {"unnesting_requests": unnesting_requests}
    
    def _parse_field_list(self, field_list_str: str) -> List[str]:
        """Parse comma-separated list of quoted field titles"""
        field_titles = []
        
        # Find all quoted strings (both single and double quotes)
        quoted_pattern = r'"([^"]+)"|\'([^\']+)\''
        matches = re.findall(quoted_pattern, field_list_str)
        
        for match in matches:
            # match is a tuple where one element is empty and one contains the string
            field_title = match[0] if match[0] else match[1]
            if field_title.strip():
                field_titles.append(field_title.strip())
        
        return field_titles

class JsonUnnestingTransformer:
    def transform(self, sql: str, unnesting_requests: List[Dict[str, Any]]) -> str:
        """Transform SQL by replacing custom syntax with CTE for JSON unnesting"""
        # Validate unnesting requests
        for req in unnesting_requests:
            if not all(key in req for key in ["json_column", "name_key", "value_key", "field_titles"]):
                raise ValueError("Invalid unnesting request: missing required keys")

        # Generate CTE with explicit field columns
        if not unnesting_requests:
            # If no unnesting requests, just remove the template syntax and return
            clean_sql = re.sub(r'\{\{fields_as_columns_from\([^}]+\)\}\}', '', sql)
            return clean_sql

        req = unnesting_requests[0]  # Take the first request
        json_column = req["json_column"]
        name_key = req["name_key"]
        value_key = req["value_key"]
        field_titles = req["field_titles"]

        # Find the table name in FROM clause
        from_match = re.search(r'FROM\s+([^\s]+)', sql, re.IGNORECASE)
        table_name = from_match.group(1) if from_match else "unknown_table"

        # Extract WHERE clause and other clauses separately
        where_match = re.search(r'\bWHERE\b(.*?)(?:\s+(?:LIMIT|ORDER\s+BY|GROUP\s+BY|HAVING)\b|$)', sql, re.IGNORECASE | re.DOTALL)
        where_clause = where_match.group(1).strip() if where_match else ""
        where_part = f"WHERE {where_clause}" if where_clause else ""
        
        # Extract additional clauses (LIMIT, ORDER BY, etc.) that come after WHERE
        additional_clauses_match = re.search(r'\bWHERE\b.*?\s+((?:LIMIT|ORDER\s+BY|GROUP\s+BY|HAVING)\b.*?)$', sql, re.IGNORECASE | re.DOTALL)
        if not additional_clauses_match:
            # Try to find these clauses even without WHERE
            additional_clauses_match = re.search(r'\s+((?:LIMIT|ORDER\s+BY|GROUP\s+BY|HAVING)\b.*?)$', sql, re.IGNORECASE | re.DOTALL)
        
        additional_clauses = additional_clauses_match.group(1).strip() if additional_clauses_match else ""

        # Create column expressions for each explicit field
        column_expressions = []
        for i, field_title in enumerate(field_titles):
            safe_column_name = self._make_safe_column_name(field_title, i)
            
            # Create pattern for LIKE matching (truncated to 30 chars, escaped single quotes)
            pattern = field_title[:30].replace("'", "''")

            # Create SQL expression to extract this specific field value
            # Handle nested JSON structure with 'list' array and flexible field matching
            extract_expr = f"""
            COALESCE(
                -- Try 1: Look in nested 'list' array structure (your specific case)
                (
                    SELECT COALESCE(
                        item->>'value_text',
                        item->>'answer',
                        item->>'text',
                        item->>'value',
                        ''
                    )
                    FROM jsonb_array_elements(
                        CASE
                            WHEN {json_column} ? 'list' AND jsonb_typeof({json_column}->'list') = 'array'
                            THEN {json_column}->'list'
                            ELSE '[]'::jsonb
                        END
                    ) item
                    WHERE LOWER(item->>'question_title') LIKE LOWER('%{pattern}%')
                       OR LOWER(item->>'title') LIKE LOWER('%{pattern}%')
                       OR LOWER(item->>'question') LIKE LOWER('%{pattern}%')
                       OR LOWER(item->>'name') LIKE LOWER('%{pattern}%')
                    LIMIT 1
                ),
                -- Try 2: Direct field access with hidden field support (ENHANCED!)
                COALESCE(
                    -- Check hidden fields first (PRIMARY for Typeform responses)
                    {json_column}->'hidden'->>'email',
                    {json_column}->'hidden'->>'Email',
                    {json_column}->'hidden'->>'EMAIL',
                    -- Check direct field access
                    {json_column}->>'email',
                    {json_column}->>'Email',
                    {json_column}->>'EMAIL',
                    -- Try the actual field title in hidden object
                    {json_column}->'hidden'->>'{{field_title.replace("'", "''")}}',
                    -- Try the actual field title directly
                    {json_column}->>'{{field_title.replace("'", "''")}}'
                ),
                -- Try 3: Look in array elements for matching title/question/name with flexible matching
                (
                    SELECT COALESCE(
                        elem->>'value_text',
                        elem->>'value',
                        elem->>'text',
                        elem->>'answer',
                        elem->>'response',
                        elem->>'description',
                        elem->>'comment',
                        ''
                    )
                    FROM jsonb_array_elements(
                        CASE
                            WHEN jsonb_typeof({json_column}) = 'array'
                            THEN {json_column}
                            ELSE jsonb_build_array({json_column})
                        END
                    ) elem
                    WHERE LOWER(elem->>'question_title') LIKE LOWER('%{pattern}%')
                       OR LOWER(elem->>'title') LIKE LOWER('%{pattern}%')
                       OR LOWER(elem->>'question') LIKE LOWER('%{pattern}%')
                       OR LOWER(elem->>'name') LIKE LOWER('%{pattern}%')
                       OR LOWER(elem->>'label') LIKE LOWER('%{pattern}%')
                       OR LOWER(elem->>'key') LIKE LOWER('%{pattern}%')
                    LIMIT 1
                ),
                -- Try 4: Look for field_title as a direct string value in the array
                (
                    SELECT COALESCE(
                        elem->>'value_text',
                        elem->>'value',
                        elem->>'text',
                        elem->>'answer',
                        elem->>'response',
                        ''
                    )
                    FROM jsonb_array_elements(
                        CASE
                            WHEN jsonb_typeof({json_column}) = 'array'
                            THEN {json_column}
                            ELSE jsonb_build_array({json_column})
                        END
                    ) elem
                    WHERE LOWER(elem->>0)::text LIKE LOWER('%{pattern}%')
                    LIMIT 1
                ),
                -- Try 5: Try to find the field_title anywhere in the JSON as a value
                (
                    SELECT COALESCE(
                        value->>'value_text',
                        value->>'value',
                        value->>'text',
                        value->>'answer',
                        ''
                    )
                    FROM jsonb_array_elements(
                        CASE
                            WHEN jsonb_typeof({json_column}) = 'array'
                            THEN {json_column}
                            ELSE jsonb_build_array({json_column})
                        END
                    ) value
                    WHERE LOWER(value->>0)::text LIKE LOWER('%{pattern}%')
                       OR LOWER(value->>'question_title')::text LIKE LOWER('%{pattern}%')
                       OR LOWER(value->>'title')::text LIKE LOWER('%{pattern}%')
                       OR LOWER(value->>'question')::text LIKE LOWER('%{pattern}%')
                       OR LOWER(value->>'name')::text LIKE LOWER('%{pattern}%')
                    LIMIT 1
                ),
                ''
            ) AS "{safe_column_name}"
            """

            column_expressions.append(extract_expr.strip())

        # HYBRID APPROACH: Use CTE for proper data retrieval but preserve user's column selection
        
        # Extract the original SELECT columns from the user's query to preserve order
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql, re.IGNORECASE | re.DOTALL)
        if not select_match:
            raise ValueError("Invalid SQL: Could not extract SELECT clause")
        
        original_select = select_match.group(1).strip()
        
        # Replace the template syntax with extracted column expressions in the SELECT clause
        extracted_columns_sql = ",\n".join(column_expressions)
        user_columns_with_extractions = re.sub(
            r'\{\{fields_as_columns_from\([^}]+\)\}\}',
            extracted_columns_sql,
            original_select
        )

        # Create the final SQL with CTE structure for proper data retrieval
        # but only select the user's specified columns
        final_sql = f"""
        WITH base_data AS (
            SELECT {user_columns_with_extractions}
            FROM {table_name}
            {where_part}
        )
        SELECT * FROM base_data
        {additional_clauses}
        """

        return final_sql.strip()
    
    def _make_safe_column_name(self, field_title: str, index: int) -> str:
        """Convert field title to a safe PostgreSQL column name"""
        # Replace problematic characters
        safe_name = re.sub(r'[^\w\s]', '_', field_title)
        safe_name = re.sub(r'\s+', '_', safe_name)
        safe_name = safe_name.strip('_').lower()
        
        # Ensure it's not too long (PostgreSQL limit is 63 characters)
        if len(safe_name) > 50:
            safe_name = safe_name[:47] + f"_{index}"
        
        # Ensure it doesn't start with a number
        if safe_name and safe_name[0].isdigit():
            safe_name = f"field_{safe_name}"
        
        return safe_name or f"field_{index}"

# Simplified approach: use explicit field lists instead of auto-discovery

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
