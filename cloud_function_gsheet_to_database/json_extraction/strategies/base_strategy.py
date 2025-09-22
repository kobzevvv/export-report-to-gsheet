#!/usr/bin/env python3
"""
Base Strategy Interface and Context Classes for JSON Field Extraction

This module defines the core abstractions for the Strategy pattern implementation
used in JSON field extraction from complex nested structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class JsonExtractionContext:
    """
    Context object containing all parameters needed for JSON field extraction.
    
    This encapsulates the information each strategy needs to generate SQL expressions
    for extracting specific fields from JSON columns.
    """
    json_column: str        # Name of JSON column to extract from
    pattern: str           # Pattern to match (truncated, escaped field title)
    field_title: str       # Original field title (unmodified)
    safe_column_name: str  # PostgreSQL-safe column name for output
    
    # Configurable key sets for flexibility
    value_keys: List[str] = None    # Keys to look for field values
    match_keys: List[str] = None    # Keys to match against pattern
    
    def __post_init__(self):
        """Set default key sets if not provided"""
        if self.value_keys is None:
            self.value_keys = ["value_text", "answer", "text", "value", "response"]
        if self.match_keys is None:
            self.match_keys = ["question_title", "title", "question", "name"]


class IJsonExtractionStrategy(ABC):
    """
    Interface for JSON field extraction strategies.
    
    Each strategy represents a different approach to finding and extracting
    field values from complex JSON structures. Strategies are applied in
    sequence using COALESCE to provide fallback behavior.
    """
    
    @abstractmethod
    def generate_sql_expression(self, context: JsonExtractionContext) -> str:
        """
        Generate SQL expression for this extraction strategy.
        
        Args:
            context: JsonExtractionContext with all extraction parameters
            
        Returns:
            SQL expression string that can be used in a COALESCE statement
            
        Example return:
            ```sql
            (
                SELECT COALESCE(item->>'value_text', item->>'answer', '')
                FROM jsonb_array_elements(json_col->'list') item
                WHERE LOWER(item->>'question_title') LIKE LOWER('%pattern%')
                LIMIT 1
            )
            ```
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """
        Get human-readable name for this strategy.
        
        Returns:
            String name for logging/debugging purposes
        """
        pass
    
    @abstractmethod
    def is_applicable(self, context: JsonExtractionContext) -> bool:
        """
        Check if this strategy should be attempted for the given context.
        
        Args:
            context: JsonExtractionContext with extraction parameters
            
        Returns:
            True if this strategy should be included in COALESCE chain
        """
        pass


class BaseJsonExtractionStrategy(IJsonExtractionStrategy):
    """
    Abstract base class providing common functionality for concrete strategies.
    
    This class implements shared SQL building utilities that most strategies
    need, reducing code duplication across concrete implementations.
    """
    
    def _build_value_coalesce(self, value_keys: List[str], element_alias: str = "item") -> str:
        """
        Build COALESCE expression for extracting values from JSON elements.
        
        Args:
            value_keys: List of JSON keys to try for field values
            element_alias: SQL alias for JSON element (default: 'item')
            
        Returns:
            COALESCE SQL expression string
            
        Example:
            ```sql
            COALESCE(item->>'value_text', item->>'answer', item->>'text', '')
            ```
        """
        expressions = [f"{element_alias}->>'{key}'" for key in value_keys]
        expressions.append("''")  # Fallback to empty string
        return f"COALESCE({', '.join(expressions)})"
    
    def _build_match_conditions(self, match_keys: List[str], pattern: str, element_alias: str = "item") -> str:
        """
        Build WHERE conditions for pattern matching against JSON keys.
        
        Args:
            match_keys: List of JSON keys to match against
            pattern: Pattern to search for (already escaped)
            element_alias: SQL alias for JSON element (default: 'item')
            
        Returns:
            WHERE condition SQL string
            
        Example:
            ```sql
            LOWER(item->>'question_title') LIKE LOWER('%pattern%')
            OR LOWER(item->>'title') LIKE LOWER('%pattern%')
            ```
        """
        conditions = []
        for key in match_keys:
            conditions.append(f"LOWER({element_alias}->>'{key}') LIKE LOWER('%{pattern}%')")
        return "\n                       OR ".join(conditions)
    
    def _build_extended_value_coalesce(self, extended_value_keys: List[str], element_alias: str = "elem") -> str:
        """
        Build extended COALESCE for strategies that need more value key options.
        
        Args:
            extended_value_keys: Extended list of value keys to try
            element_alias: SQL alias for JSON element (default: 'elem')
            
        Returns:
            Extended COALESCE SQL expression
        """
        return self._build_value_coalesce(extended_value_keys, element_alias)
    
    def _build_extended_match_conditions(self, extended_match_keys: List[str], pattern: str, element_alias: str = "elem") -> str:
        """
        Build extended WHERE conditions for strategies that need more matching options.
        
        Args:
            extended_match_keys: Extended list of keys to match against
            pattern: Pattern to search for (already escaped)
            element_alias: SQL alias for JSON element (default: 'elem')
            
        Returns:
            Extended WHERE conditions SQL string
        """
        return self._build_match_conditions(extended_match_keys, pattern, element_alias)
