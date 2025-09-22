#!/usr/bin/env python3
"""
Refactored JSON Unnesting Module - Strategy Pattern Implementation

This is the refactored version using the strategy pattern that maintains 100%
compatibility with the original json_unnesting.py while providing clean,
testable, and extensible architecture.
"""

import re
from typing import List, Dict, Any, Set
import logging
import json

# Import the new strategy-based architecture
from json_extraction import ColumnExpressionGenerator

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
    """
    Parser for JSON unnesting custom syntax - unchanged from original.
    
    This class maintains the exact same API and behavior as the original
    to ensure no breaking changes.
    """
    
    def __init__(self):
        # Updated pattern to capture fields_as_columns_from with variable field list
        self.custom_syntax_pattern = r'\{\{fields_as_columns_from\(([^,]+),\s*([^,]+),\s*([^,]+),\s*(.+)\)\}\}'

    def parse(self, sql: str) -> Dict[str, Any]:
        """Parse SQL for custom unnesting syntax and return unnesting requests"""
        unnesting_requests = []

        matches = re.findall(self.custom_syntax_pattern, sql)
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


class JsonUnnestingTransformerRefactored:
    """
    Refactored transformer using strategy pattern architecture.
    
    This class maintains the exact same API as the original JsonUnnestingTransformer
    but uses the new strategy-based architecture internally for clean separation
    of concerns and improved maintainability.
    """
    
    def __init__(self):
        """Initialize with strategy-based column expression generator"""
        self.expression_generator = ColumnExpressionGenerator()
    
    def transform(self, sql: str, unnesting_requests: List[Dict[str, Any]]) -> str:
        """
        Transform SQL by replacing custom syntax with CTE for JSON unnesting.
        
        This method maintains the exact same API and behavior as the original
        transform() method but uses the strategy pattern internally.
        
        Args:
            sql: Original SQL with custom syntax
            unnesting_requests: List of parsed unnesting request dictionaries
            
        Returns:
            Transformed SQL with CTE structure
        """
        # Validate unnesting requests (same validation as original)
        for req in unnesting_requests:
            if not all(key in req for key in ["json_column", "name_key", "value_key", "field_titles"]):
                raise ValueError("Invalid unnesting request: missing required keys")

        # Remove template syntax first (same as original)
        clean_sql = re.sub(r'\{\{fields_as_columns_from\([^}]+\)\}\}', '', sql)

        # Find the table name in FROM clause (same as original)
        from_match = re.search(r'FROM\s+([^\s]+)', clean_sql, re.IGNORECASE)
        table_name = from_match.group(1) if from_match else "unknown_table"

        # Extract WHERE clause if present (same as original)
        where_match = re.search(r'\bWHERE\b(.+)', clean_sql, re.IGNORECASE | re.DOTALL)
        where_clause = where_match.group(1).strip() if where_match else ""

        # Early return for no unnesting requests (same as original)
        if not unnesting_requests:
            return clean_sql

        # Process first request (same limitation as original)
        req = unnesting_requests[0]  # Take the first request
        json_column = req["json_column"]
        name_key = req["name_key"]
        value_key = req["value_key"] 
        field_titles = req["field_titles"]

        where_part = f"WHERE {where_clause}" if where_clause else ""

        # Generate column expressions using strategy pattern (NEW!)
        column_expressions = []
        for i, field_title in enumerate(field_titles):
            expr = self.expression_generator.generate_column_expression(
                field_title=field_title,
                index=i,
                json_column=json_column
            )
            column_expressions.append(expr)

        # Combine all columns (same as original)
        all_columns = "*, " + ", ".join(column_expressions)

        # Generate final SQL with CTE (same structure as original)
        final_sql = f"""
        WITH base_data AS (
            SELECT {all_columns}
            FROM {table_name}
            {where_part}
        )
        SELECT * FROM base_data
        """

        return final_sql.strip()
    
    def _make_safe_column_name(self, field_title: str, index: int) -> str:
        """
        DEPRECATED: This method is now handled by ColumnExpressionGenerator.
        
        Keeping for backward compatibility but delegating to the new architecture.
        """
        return self.expression_generator._make_safe_column_name(field_title, index)


# For backward compatibility, create aliases to the original class names
JsonUnnestingTransformer = JsonUnnestingTransformerRefactored


def process_query_with_json_unnesting(sql: str, database_url: str) -> List[Dict[str, Any]]:
    """
    Process a query with JSON unnesting and return results.
    
    This function maintains the exact same API as the original but uses
    the refactored transformer internally.
    """
    parser = JsonUnnestingParser()
    transformer = JsonUnnestingTransformerRefactored()  # Use refactored version

    # Parse the query (same as original)
    parsed = parser.parse(sql)
    unnesting_requests = parsed["unnesting_requests"]

    # Transform if there are unnesting requests (same as original)
    if unnesting_requests:
        transformed_sql = transformer.transform(sql, unnesting_requests)
    else:
        transformed_sql = sql

    # Execute the query only if psycopg is available (same as original)
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
