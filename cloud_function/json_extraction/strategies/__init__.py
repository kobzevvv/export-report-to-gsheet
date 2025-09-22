"""
JSON Extraction Strategies

Individual strategy implementations for different JSON structure patterns.
"""

from .base_strategy import IJsonExtractionStrategy, JsonExtractionContext

__all__ = ['IJsonExtractionStrategy', 'JsonExtractionContext']
