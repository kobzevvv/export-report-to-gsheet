#!/usr/bin/env python3
"""
Strategy 3: Flexible Array Matching Extraction Strategy

This strategy treats JSON as an array or wraps it in an array, then performs
flexible field matching. This corresponds to "Try 3" in the original code.
"""

from .base_strategy import BaseJsonExtractionStrategy, JsonExtractionContext


class FlexibleArrayExtractionStrategy(BaseJsonExtractionStrategy):
    """
    Flexible array matching extraction strategy.
    
    This strategy handles JSON that is either already an array or gets wrapped
    in an array, then searches through elements for matching field titles using
    extended matching keys and value keys.
    
    SQL Pattern Generated:
    ```sql
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
                WHEN jsonb_typeof(json_column) = 'array'
                THEN json_column
                ELSE jsonb_build_array(json_column)
            END
        ) elem
        WHERE LOWER(elem->>'question_title') LIKE LOWER('%pattern%')
           OR LOWER(elem->>'title') LIKE LOWER('%pattern%')
           OR LOWER(elem->>'question') LIKE LOWER('%pattern%')
           OR LOWER(elem->>'name') LIKE LOWER('%pattern%')
           OR LOWER(elem->>'label') LIKE LOWER('%pattern%')
           OR LOWER(elem->>'key') LIKE LOWER('%pattern%')
        LIMIT 1
    )
    ```
    """
    
    def generate_sql_expression(self, context: JsonExtractionContext) -> str:
        """
        Generate SQL expression for flexible array matching.
        
        Args:
            context: JsonExtractionContext with extraction parameters
            
        Returns:
            SQL subquery for flexible array element matching
        """
        # Extended value keys for this strategy (more comprehensive than basic strategy)
        extended_value_keys = [
            "value_text", "value", "text", "answer", "response", 
            "description", "comment"
        ]
        
        # Extended match keys for this strategy
        extended_match_keys = [
            "question_title", "title", "question", "name", "label", "key"
        ]
        
        # Build extended COALESCE and match conditions
        value_coalesce = self._build_extended_value_coalesce(extended_value_keys, "elem")
        match_conditions = self._build_extended_match_conditions(extended_match_keys, context.pattern, "elem")
        
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
            WHERE {match_conditions}
            LIMIT 1
        )"""
        
        return sql_expression.strip()
    
    def get_strategy_name(self) -> str:
        """Get human-readable strategy name"""
        return "FlexibleArrayMatching"
    
    def is_applicable(self, context: JsonExtractionContext) -> bool:
        """
        This strategy is always applicable as a fallback.
        
        Args:
            context: JsonExtractionContext (not used for applicability check)
            
        Returns:
            Always True - this strategy provides flexible matching
        """
        return True
    
    def get_description(self) -> str:
        """Get detailed description of what this strategy does"""
        return """
        Strategy 3: Flexible Array Matching
        
        Handles JSON structures that are either arrays or need to be wrapped in arrays.
        Provides more comprehensive field matching with extended value and match keys.
        
        JSON Structures Handled:
        1. Direct arrays: [{"title": "Field", "value": "Data"}, ...]
        2. Non-arrays wrapped: {"field": "value"} -> [{"field": "value"}]
        
        Extended Matching:
        - More value keys: value_text, value, text, answer, response, description, comment
        - More match keys: question_title, title, question, name, label, key
        
        Use Case:
        Fallback when nested list structure doesn't match but data exists in array format.
        """
