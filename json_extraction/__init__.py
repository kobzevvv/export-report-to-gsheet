"""
JSON Extraction Module - Strategy Pattern Implementation for JSON Field Extraction

This module provides a clean, extensible architecture for extracting fields from complex JSON structures
using multiple fallback strategies.
"""

from .strategies.base_strategy import IJsonExtractionStrategy, JsonExtractionContext
# from .column_expression_generator import ColumnExpressionGenerator  # TODO: Create this in Step 8

__all__ = [
    'IJsonExtractionStrategy',
    'JsonExtractionContext'
    # 'ColumnExtractionGenerator'  # TODO: Add back in Step 8
]
