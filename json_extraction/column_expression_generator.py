#!/usr/bin/env python3
"""
Column Expression Generator - Strategy Coordinator

This module coordinates multiple JSON extraction strategies to generate
COALESCE expressions that match the original system's extraction logic.
"""

import re
from typing import List
from .strategies.base_strategy import JsonExtractionContext, IJsonExtractionStrategy
from .strategies.nested_list_strategy import NestedListExtractionStrategy
from .strategies.direct_field_strategy import DirectFieldExtractionStrategy
from .strategies.flexible_array_strategy import FlexibleArrayExtractionStrategy
from .strategies.direct_string_strategy import DirectStringValueExtractionStrategy
from .strategies.wildcard_search_strategy import WildcardSearchExtractionStrategy


class ColumnExpressionGenerator:
    """
    Coordinates multiple extraction strategies to build COALESCE expressions.
    
    This class maintains the same 5-strategy extraction order as the original code:
    1. NestedListExtractionStrategy (Try 1: nested 'list' array)
    2. DirectFieldExtractionStrategy (Try 2: direct field access - disabled)
    3. FlexibleArrayExtractionStrategy (Try 3: flexible array matching)
    4. DirectStringValueExtractionStrategy (Try 4: direct string values)
    5. WildcardSearchExtractionStrategy (Try 5: wildcard search)
    """
    
    def __init__(self):
        """Initialize with all 5 strategies in the correct order"""
        self.strategies: List[IJsonExtractionStrategy] = [
            NestedListExtractionStrategy(),      # Strategy 1
            DirectFieldExtractionStrategy(),     # Strategy 2 (disabled)
            FlexibleArrayExtractionStrategy(),   # Strategy 3
            DirectStringValueExtractionStrategy(), # Strategy 4
            WildcardSearchExtractionStrategy()   # Strategy 5
        ]
    
    def generate_column_expression(self, 
                                  field_title: str, 
                                  index: int,
                                  json_column: str) -> str:
        """
        Generate complete COALESCE expression with all applicable strategies.
        
        This method replicates the original transform() method's column generation
        logic but uses the strategy pattern for clean separation of concerns.
        
        Args:
            field_title: Original field title from user input
            index: Field index for generating safe column names
            json_column: Name of JSON column to extract from
            
        Returns:
            Complete SQL column expression with COALESCE and column alias
            
        Example:
            ```sql
            COALESCE(
                -- Try 1: Nested list strategy SQL...
                -- Try 2: NULL (disabled)
                -- Try 3: Flexible array strategy SQL...
                -- Try 4: Direct string strategy SQL...
                -- Try 5: Wildcard search strategy SQL...
                ''
            ) AS "safe_column_name"
            ```
        """
        # Create pattern (truncated to 30 chars, escaped for SQL)
        pattern = self._create_pattern(field_title)
        
        # Create safe column name
        safe_column_name = self._make_safe_column_name(field_title, index)
        
        # Create extraction context
        context = JsonExtractionContext(
            json_column=json_column,
            pattern=pattern,
            field_title=field_title,
            safe_column_name=safe_column_name
        )
        
        # Generate expressions for all applicable strategies
        strategy_expressions = []
        for strategy in self.strategies:
            if strategy.is_applicable(context):
                expr = strategy.generate_sql_expression(context)
                strategy_expressions.append(expr)
        
        # Build COALESCE with fallback to empty string
        coalesce_expr = "COALESCE(\n" + ",\n".join([
            f"                {expr}" for expr in strategy_expressions
        ]) + ",\n                ''\n            )"
        
        return f'{coalesce_expr} AS "{safe_column_name}"'
    
    def _create_pattern(self, field_title: str) -> str:
        """
        Create search pattern from field title (matches original logic).
        
        Args:
            field_title: Original field title
            
        Returns:
            Pattern truncated to 30 characters with escaped quotes
        """
        # Truncate to 30 characters and escape single quotes (original behavior)
        pattern = field_title[:30].replace("'", "''")
        return pattern
    
    def _make_safe_column_name(self, field_title: str, index: int) -> str:
        """
        Convert field title to safe PostgreSQL column name (matches original logic).
        
        This method replicates the exact behavior from the original code's
        _make_safe_column_name method.
        
        Args:
            field_title: Original field title
            index: Field index for uniqueness
            
        Returns:
            PostgreSQL-safe column name
        """
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
    
    def get_strategy_count(self) -> int:
        """Get total number of strategies available"""
        return len(self.strategies)
    
    def get_applicable_strategy_count(self, context: JsonExtractionContext) -> int:
        """
        Get number of strategies applicable for given context.
        
        Args:
            context: JsonExtractionContext for applicability testing
            
        Returns:
            Number of applicable strategies
        """
        return sum(1 for strategy in self.strategies if strategy.is_applicable(context))
    
    def get_strategy_names(self) -> List[str]:
        """Get names of all strategies in order"""
        return [strategy.get_strategy_name() for strategy in self.strategies]
