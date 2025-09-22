#!/usr/bin/env python3
"""
Strategy 1: Nested List Extraction Strategy

This strategy extracts fields from JSON structures that contain a 'list' array:
{
    "list": [
        {"question_title": "Full Name", "value_text": "John Doe"},
        {"question_title": "Email", "value_text": "john@example.com"}
    ]
}

This is the primary strategy based on the current system's main use case.
"""

from .base_strategy import BaseJsonExtractionStrategy, JsonExtractionContext


class NestedListExtractionStrategy(BaseJsonExtractionStrategy):
    """
    Extracts values from nested 'list' array structure.
    
    This strategy looks for JSON columns that have a 'list' key containing an array
    of objects with question/answer pairs. This is Strategy 1 from the original code.
    
    SQL Pattern Generated:
    ```sql
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
                WHEN json_column ? 'list' AND jsonb_typeof(json_column->'list') = 'array'
                THEN json_column->'list'
                ELSE '[]'::jsonb
            END
        ) item
        WHERE LOWER(item->>'question_title') LIKE LOWER('%pattern%')
           OR LOWER(item->>'title') LIKE LOWER('%pattern%')
           OR LOWER(item->>'question') LIKE LOWER('%pattern%')
           OR LOWER(item->>'name') LIKE LOWER('%pattern%')
        LIMIT 1
    )
    ```
    """
    
    def generate_sql_expression(self, context: JsonExtractionContext) -> str:
        """
        Generate SQL expression for nested list extraction.
        
        Args:
            context: JsonExtractionContext with extraction parameters
            
        Returns:
            SQL subquery that extracts from nested 'list' array
        """
        # Build value COALESCE using context's value keys
        value_coalesce = self._build_value_coalesce(context.value_keys, "item")
        
        # Build match conditions using context's match keys  
        match_conditions = self._build_match_conditions(context.match_keys, context.pattern, "item")
        
        # Generate the complete SQL expression
        sql_expression = f"""
        (
            SELECT {value_coalesce}
            FROM jsonb_array_elements(
                CASE
                    WHEN {context.json_column} ? 'list' AND jsonb_typeof({context.json_column}->'list') = 'array'
                    THEN {context.json_column}->'list'
                    ELSE '[]'::jsonb
                END
            ) item
            WHERE {match_conditions}
            LIMIT 1
        )"""
        
        return sql_expression.strip()
    
    def get_strategy_name(self) -> str:
        """Get human-readable strategy name"""
        return "NestedListExtraction"
    
    def is_applicable(self, context: JsonExtractionContext) -> bool:
        """
        This strategy is always applicable as it's the primary extraction method.
        
        Args:
            context: JsonExtractionContext (not used for this strategy)
            
        Returns:
            Always True - this is Strategy 1 and should always be attempted first
        """
        return True
    
    def get_description(self) -> str:
        """Get detailed description of what this strategy does"""
        return """
        Strategy 1: Nested List Extraction
        
        Extracts from JSON structures with nested 'list' arrays containing objects
        with question-answer pairs. This handles the most common JSON structure
        pattern in the current system.
        
        JSON Structure Expected:
        {
            "list": [
                {"question_title": "Field Name", "value_text": "Field Value"},
                ...
            ]
        }
        
        Fallback Behavior:
        - If 'list' key doesn't exist, returns empty array
        - If 'list' is not an array, returns empty array
        - Uses LIMIT 1 to get first matching field only
        """
