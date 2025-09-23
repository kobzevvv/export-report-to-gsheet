#!/usr/bin/env python3
"""
Strategy for Hidden Field Extraction

This strategy extracts fields from 'hidden' objects in JSON data, specifically
designed for Typeform responses where data like emails are stored in:
{
    "hidden": {
        "email": "alex.stav@mail.ru",
        "first_name": "Александр"
    }
}

This strategy should be prioritized before other strategies since hidden fields
are typically the most reliable source of structured data in Typeform responses.
"""

from .base_strategy import BaseJsonExtractionStrategy, JsonExtractionContext


class HiddenFieldExtractionStrategy(BaseJsonExtractionStrategy):
    """
    Extracts values from 'hidden' object in JSON data.
    
    This strategy looks for JSON columns that have a 'hidden' key containing
    an object with direct field mappings. This is common in Typeform responses
    where pre-filled or URL parameter data is stored.
    
    SQL Pattern Generated:
    ```sql
    COALESCE(
        json_column->'hidden'->>'email',
        json_column->'hidden'->>'Email', 
        json_column->'hidden'->>'EMAIL',
        json_column->'hidden'->>'field_title'
    )
    ```
    """
    
    def generate_sql_expression(self, context: JsonExtractionContext) -> str:
        """
        Generate SQL expression for hidden field access.
        
        Args:
            context: JsonExtractionContext with extraction parameters
            
        Returns:
            SQL expression that extracts from hidden object
        """
        # For email fields, try common email field variations
        if self._is_email_field(context.field_title):
            return self._generate_email_extraction_sql(context)
        else:
            return self._generate_generic_hidden_field_sql(context)
    
    def _is_email_field(self, field_title: str) -> bool:
        """Check if the field title indicates an email field."""
        email_patterns = ['email', 'e-mail', 'mail', 'электронная', 'почта']
        field_lower = field_title.lower()
        return any(pattern in field_lower for pattern in email_patterns)
    
    def _generate_email_extraction_sql(self, context: JsonExtractionContext) -> str:
        """Generate SQL specifically for email extraction from hidden fields."""
        return f"""
        COALESCE(
            {context.json_column}->'hidden'->>'email',
            {context.json_column}->'hidden'->>'Email',
            {context.json_column}->'hidden'->>'EMAIL',
            {context.json_column}->'hidden'->>'e-mail',
            {context.json_column}->'hidden'->>'E-mail',
            {context.json_column}->'hidden'->>'E-MAIL'
        )"""
    
    def _generate_generic_hidden_field_sql(self, context: JsonExtractionContext) -> str:
        """Generate SQL for generic hidden field extraction."""
        # Try the exact field title and common variations
        field_variations = [
            context.field_title,  # Exact match
            context.field_title.lower(),  # Lowercase
            context.field_title.upper(),  # Uppercase
            context.field_title.replace(' ', '_'),  # Spaces to underscores
            context.field_title.replace(' ', '_').lower(),  # Snake case
        ]
        
        # Remove duplicates while preserving order
        unique_variations = []
        seen = set()
        for var in field_variations:
            if var not in seen:
                unique_variations.append(var)
                seen.add(var)
        
        # Build COALESCE with all variations
        coalesce_parts = []
        for variation in unique_variations:
            clean_variation = variation.replace("'", "''")  # Escape single quotes
            coalesce_parts.append(f"{context.json_column}->'hidden'->'>'{clean_variation}'")
        
        return f"COALESCE(\n            {','.join(coalesce_parts)}\n        )"
    
    def get_strategy_name(self) -> str:
        """Get human-readable strategy name"""
        return "HiddenFieldAccess"
    
    def is_applicable(self, context: JsonExtractionContext) -> bool:
        """
        This strategy is always applicable as it should be tried first.
        
        Args:
            context: JsonExtractionContext (not used for applicability check)
            
        Returns:
            Always True - hidden fields should always be checked first
        """
        return True
    
    def get_priority(self) -> int:
        """
        Get strategy priority (lower number = higher priority).
        
        Returns:
            1 - This should be the first strategy tried
        """
        return 1
    
    def get_description(self) -> str:
        """Get detailed description of what this strategy does"""
        return """
        Strategy: Hidden Field Access (Highest Priority)
        
        Extracts data from 'hidden' objects in JSON, commonly used in Typeform responses
        for pre-filled or URL parameter data.
        
        JSON Structure Handled:
        {
            "hidden": {
                "email": "user@example.com",
                "first_name": "John",
                "company": "Acme Corp"
            }
        }
        
        Special Handling:
        - Email fields: Tries multiple variations (email, Email, EMAIL, e-mail, etc.)
        - Generic fields: Tries exact match, case variations, and underscore formats
        
        Priority: Highest (1) - Should be tried before other extraction strategies
        
        Use Case:
        Primary strategy for Typeform responses where structured data is stored
        in the hidden object. This is typically the most reliable source of
        clean, structured field data.
        """
