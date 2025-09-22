#!/usr/bin/env python3
"""
Strategy 5: Wildcard Search Extraction Strategy

This strategy performs the most comprehensive search, looking for the field title
anywhere in the JSON structure. Corresponds to "Try 5" in the original code.
"""

from .base_strategy import BaseJsonExtractionStrategy, JsonExtractionContext


class WildcardSearchExtractionStrategy(BaseJsonExtractionStrategy):
    """
    Wildcard search extraction strategy.
    
    This is the most comprehensive strategy that searches for field titles
    anywhere in the JSON structure using multiple approaches:
    1. Direct string value at index 0
    2. Named field matching across multiple key types
    
    This is the final fallback strategy in the COALESCE chain.
    
    SQL Pattern Generated:
    ```sql
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
                WHEN jsonb_typeof(json_column) = 'array'
                THEN json_column
                ELSE jsonb_build_array(json_column)
            END
        ) value
        WHERE LOWER(value->>0)::text LIKE LOWER('%pattern%')
           OR LOWER(value->>'question_title')::text LIKE LOWER('%pattern%')
           OR LOWER(value->>'title')::text LIKE LOWER('%pattern%')
           OR LOWER(value->>'question')::text LIKE LOWER('%pattern%')
           OR LOWER(value->>'name')::text LIKE LOWER('%pattern%')
        LIMIT 1
    )
    ```
    """
    
    def generate_sql_expression(self, context: JsonExtractionContext) -> str:
        """
        Generate SQL expression for wildcard search.
        
        Args:
            context: JsonExtractionContext with extraction parameters
            
        Returns:
            SQL subquery that performs comprehensive wildcard search
        """
        # Minimal value keys for final fallback
        value_keys = ["value_text", "value", "text", "answer"]
        
        # Build value COALESCE
        value_coalesce = self._build_value_coalesce(value_keys, "value")
        
        # Build comprehensive WHERE conditions (both direct and named field matching)
        where_conditions = f"""LOWER(value->>0)::text LIKE LOWER('%{context.pattern}%')
               OR LOWER(value->>'question_title')::text LIKE LOWER('%{context.pattern}%')
               OR LOWER(value->>'title')::text LIKE LOWER('%{context.pattern}%')
               OR LOWER(value->>'question')::text LIKE LOWER('%{context.pattern}%')
               OR LOWER(value->>'name')::text LIKE LOWER('%{context.pattern}%')"""
        
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
            ) value
            WHERE {where_conditions}
            LIMIT 1
        )"""
        
        return sql_expression.strip()
    
    def get_strategy_name(self) -> str:
        """Get human-readable strategy name"""
        return "WildcardSearch"
    
    def is_applicable(self, context: JsonExtractionContext) -> bool:
        """
        This strategy is always applicable as the final fallback.
        
        Args:
            context: JsonExtractionContext (not used for applicability check)
            
        Returns:
            Always True - this is the last resort strategy
        """
        return True
    
    def get_description(self) -> str:
        """Get detailed description of what this strategy does"""
        return """
        Strategy 5: Wildcard Search (Final Fallback)
        
        The most comprehensive search strategy that attempts to find field titles
        anywhere in the JSON structure. This is the final fallback in the COALESCE chain.
        
        Search Approaches:
        1. Direct string match at index 0: value->>0
        2. Named field matching: question_title, title, question, name
        
        Matching Logic:
        - Uses OR conditions to try multiple approaches
        - Case-insensitive LIKE matching with wildcards
        - Limited value key options (final fallback)
        
        Use Case:
        Last resort when all other strategies fail. Catches edge cases and
        unusual JSON structures that don't fit standard patterns.
        
        JSON Structures Handled:
        - Any array-like structure with string values
        - Objects with various title/name field variations
        - Mixed structures where field titles appear in unexpected places
        """
