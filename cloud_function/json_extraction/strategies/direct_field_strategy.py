#!/usr/bin/env python3
"""
Strategy 2: Direct Field Access Extraction Strategy

This strategy would extract fields through direct JSON field access.
Currently disabled in the original code but architecture ready for future implementation.

Example: json_column->>'field_name'
"""

from .base_strategy import BaseJsonExtractionStrategy, JsonExtractionContext


class DirectFieldExtractionStrategy(BaseJsonExtractionStrategy):
    """
    Direct field access extraction strategy.
    
    This strategy would provide direct access to JSON fields by name,
    but is currently disabled to maintain compatibility with the existing
    pattern matching approach.
    
    When enabled, would generate SQL like:
    ```sql
    json_column->>'field_title'
    ```
    
    Currently returns NULL to skip this strategy while maintaining
    the same COALESCE structure as the original code.
    """
    
    def generate_sql_expression(self, context: JsonExtractionContext) -> str:
        """
        Generate SQL expression for direct field access.
        
        Currently returns NULL to skip this strategy, maintaining compatibility
        with original code which comments this as "skipped for pattern matching approach".
        
        Args:
            context: JsonExtractionContext with extraction parameters
            
        Returns:
            "NULL" to skip this strategy in COALESCE chain
        """
        # Original code comment: "Try 2: Direct field access (skipped for pattern matching approach)"
        return "NULL"
    
    def get_strategy_name(self) -> str:
        """Get human-readable strategy name"""
        return "DirectFieldAccess"
    
    def is_applicable(self, context: JsonExtractionContext) -> bool:
        """
        This strategy is currently disabled.
        
        Args:
            context: JsonExtractionContext (not used)
            
        Returns:
            False - strategy is disabled to maintain existing behavior
        """
        return False  # Disabled to match original behavior
    
    def get_description(self) -> str:
        """Get detailed description of what this strategy would do"""
        return """
        Strategy 2: Direct Field Access (Currently Disabled)
        
        This strategy would provide direct access to JSON fields by their exact name,
        bypassing the pattern matching approach. Currently disabled to maintain
        compatibility with existing pattern-based field matching.
        
        When enabled, would generate:
        json_column->>'exact_field_name'
        
        Future Enhancement:
        Could be enabled for exact field name matches or when field names
        are known to exist as direct JSON keys.
        """
    
    def generate_direct_access_sql(self, context: JsonExtractionContext) -> str:
        """
        Generate direct field access SQL (for future use when strategy is enabled).
        
        Args:
            context: JsonExtractionContext with extraction parameters
            
        Returns:
            SQL expression for direct field access
        """
        # Safe column name cleaning for JSON key access
        clean_field_name = context.field_title.replace("'", "''")
        return f"{context.json_column}->'>'{clean_field_name}'"
