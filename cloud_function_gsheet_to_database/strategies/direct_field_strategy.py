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
        
        Now enhanced to handle hidden fields and direct field access.
        This strategy tries both hidden field access and direct JSON field access.
        
        Args:
            context: JsonExtractionContext with extraction parameters
            
        Returns:
            SQL expression for direct field access including hidden fields
        """
        # For email fields, prioritize hidden field access
        if self._is_email_field(context.field_title):
            return self._generate_email_extraction_sql(context)
        else:
            return self._generate_generic_direct_access_sql(context)
    
    def _is_email_field(self, field_title: str) -> bool:
        """Check if the field title indicates an email field."""
        email_patterns = ['email', 'e-mail', 'mail', 'электронная', 'почта']
        field_lower = field_title.lower()
        return any(pattern in field_lower for pattern in email_patterns)
    
    def _generate_email_extraction_sql(self, context: JsonExtractionContext) -> str:
        """Generate SQL specifically for email extraction."""
        return f"""
        COALESCE(
            -- Try hidden fields first (most reliable for Typeform)
            {context.json_column}->'hidden'->>'email',
            {context.json_column}->'hidden'->>'Email',
            {context.json_column}->'hidden'->>'EMAIL',
            -- Try direct field access
            {context.json_column}->>'email',
            {context.json_column}->>'Email',
            {context.json_column}->>'EMAIL'
        )"""
    
    def _generate_generic_direct_access_sql(self, context: JsonExtractionContext) -> str:
        """Generate SQL for generic direct field access."""
        # Clean field name for JSON access
        clean_field_name = context.field_title.replace("'", "''")
        
        return f"""
        COALESCE(
            -- Try hidden field first
            {context.json_column}->'hidden'->'>'{clean_field_name}',
            -- Try direct field access
            {context.json_column}->'>'{clean_field_name}'
        )"""
    
    def get_strategy_name(self) -> str:
        """Get human-readable strategy name"""
        return "DirectFieldAccess"
    
    def is_applicable(self, context: JsonExtractionContext) -> bool:
        """
        This strategy is now enabled for direct field access.
        
        Args:
            context: JsonExtractionContext (not used for applicability check)
            
        Returns:
            True - strategy is now enabled to handle hidden fields and direct access
        """
        return True  # Now enabled to handle hidden fields
    
    def get_description(self) -> str:
        """Get detailed description of what this strategy does"""
        return """
        Strategy 2: Direct Field Access (Now Enabled)
        
        This strategy provides direct access to JSON fields by their exact name,
        with special handling for hidden fields commonly found in Typeform responses.
        
        Enhanced Features:
        - Hidden field access: json_column->'hidden'->>'field_name'
        - Direct field access: json_column->>'field_name'
        - Email-specific handling with multiple case variations
        - Fallback from hidden to direct access
        
        JSON Structures Handled:
        - Hidden fields: {"hidden": {"email": "user@example.com"}}
        - Direct fields: {"email": "user@example.com"}
        
        Priority: High (should run before pattern matching strategies)
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
