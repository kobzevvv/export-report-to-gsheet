#!/usr/bin/env python3
"""
Strategy 4: Direct String Value Extraction Strategy

This strategy looks for field titles as direct string values at array index 0.
Corresponds to "Try 4" in the original code.
"""

from .base_strategy import BaseJsonExtractionStrategy, JsonExtractionContext


class DirectStringValueExtractionStrategy(BaseJsonExtractionStrategy):
    """
    Direct string value extraction strategy.
    
    This strategy searches for the field title as a direct string value
    in the first element (index 0) of array elements, then extracts
    the corresponding value fields.
    
    SQL Pattern Generated:
    ```sql
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
                WHEN jsonb_typeof(json_column) = 'array'
                THEN json_column
                ELSE jsonb_build_array(json_column)
            END
        ) elem
        WHERE LOWER(elem->>0)::text LIKE LOWER('%pattern%')
        LIMIT 1
    )
    ```
    """
    
    def generate_sql_expression(self, context: JsonExtractionContext) -> str:
        """
        Generate SQL expression for direct string value extraction.
        
        Args:
            context: JsonExtractionContext with extraction parameters
            
        Returns:
            SQL subquery that looks for direct string values at index 0
        """
        # Value keys for this strategy (subset of extended keys)
        value_keys = ["value_text", "value", "text", "answer", "response"]
        
        # Build value COALESCE
        value_coalesce = self._build_value_coalesce(value_keys, "elem")
        
        # Generate the complete SQL expression
        sql_expression = f"""
        (
            SELECT {value_coalesce}
            FROM jsonb_array_elements(
                CASE
                    WHEN jsonb_typeof({context.json_column}) = 'array'
                    THEN {context.json_column}
                    ELSE jsonb_build_array({context.json_column})
                END
            ) elem
            WHERE LOWER(elem->>0)::text LIKE LOWER('%{context.pattern}%')
            LIMIT 1
        )"""
        
        return sql_expression.strip()
    
    def get_strategy_name(self) -> str:
        """Get human-readable strategy name"""
        return "DirectStringValue"
    
    def is_applicable(self, context: JsonExtractionContext) -> bool:
        """
        This strategy is always applicable as part of the fallback chain.
        
        Args:
            context: JsonExtractionContext (not used for applicability check)
            
        Returns:
            Always True - provides another fallback option
        """
        return True
    
    def get_description(self) -> str:
        """Get detailed description of what this strategy does"""
        return """
        Strategy 4: Direct String Value Extraction
        
        Looks for field titles as direct string values in the first element (index 0)
        of JSON array elements. This handles cases where the field title itself
        is stored as the first value in an array structure.
        
        JSON Structure Example:
        [
            ["Field Name", "Field Value", "metadata"],
            ["Another Field", "Another Value", "more data"]
        ]
        
        Matching Logic:
        - Checks elem->>0 (first element) against pattern
        - Extracts value from standard value fields
        - Uses LIKE for flexible matching
        
        Use Case:
        Handles array-of-arrays JSON structures where field names are positional.
        """
