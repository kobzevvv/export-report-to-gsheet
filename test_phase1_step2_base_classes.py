#!/usr/bin/env python3
"""
Tests for Phase 1 Step 2: Base Strategy Interface and Context Classes

Tests the foundational classes that all concrete strategies will build upon.
"""

import pytest
from json_extraction.strategies.base_strategy import (
    JsonExtractionContext, IJsonExtractionStrategy, BaseJsonExtractionStrategy
)


class TestJsonExtractionContext:
    """Test the context object that carries extraction parameters"""
    
    def test_basic_context_creation(self):
        """Test creating context with required parameters"""
        context = JsonExtractionContext(
            json_column="answers_json",
            pattern="Full Name",
            field_title="Full Name",
            safe_column_name="full_name"
        )
        
        assert context.json_column == "answers_json"
        assert context.pattern == "Full Name"  
        assert context.field_title == "Full Name"
        assert context.safe_column_name == "full_name"
    
    def test_default_key_sets(self):
        """Test that default value_keys and match_keys are set correctly"""
        context = JsonExtractionContext(
            json_column="json_col",
            pattern="pattern",
            field_title="Field",
            safe_column_name="field"
        )
        
        # Check default value keys
        expected_value_keys = ["value_text", "answer", "text", "value", "response"]
        assert context.value_keys == expected_value_keys
        
        # Check default match keys
        expected_match_keys = ["question_title", "title", "question", "name"]
        assert context.match_keys == expected_match_keys
    
    def test_custom_key_sets(self):
        """Test providing custom value_keys and match_keys"""
        custom_value_keys = ["custom_value", "data", "content"]
        custom_match_keys = ["custom_title", "label", "identifier"]
        
        context = JsonExtractionContext(
            json_column="json_col",
            pattern="pattern", 
            field_title="Field",
            safe_column_name="field",
            value_keys=custom_value_keys,
            match_keys=custom_match_keys
        )
        
        assert context.value_keys == custom_value_keys
        assert context.match_keys == custom_match_keys


class ConcreteTestStrategy(BaseJsonExtractionStrategy):
    """Concrete implementation for testing BaseJsonExtractionStrategy"""
    
    def generate_sql_expression(self, context: JsonExtractionContext) -> str:
        # Simple test implementation
        return f"SELECT '{context.field_title}' as test_field"
    
    def get_strategy_name(self) -> str:
        return "TestStrategy"
    
    def is_applicable(self, context: JsonExtractionContext) -> bool:
        return True


class TestBaseJsonExtractionStrategy:
    """Test the base strategy class and its helper methods"""
    
    def setup_method(self):
        """Setup for each test"""
        self.strategy = ConcreteTestStrategy()
        self.context = JsonExtractionContext(
            json_column="test_json",
            pattern="Test Field",
            field_title="Test Field",
            safe_column_name="test_field"
        )
    
    def test_build_value_coalesce_default(self):
        """Test building COALESCE expression with default parameters"""
        value_keys = ["value_text", "answer", "text"]
        result = self.strategy._build_value_coalesce(value_keys)
        
        expected = "COALESCE(item->>'value_text', item->>'answer', item->>'text', '')"
        assert result == expected
    
    def test_build_value_coalesce_custom_alias(self):
        """Test building COALESCE expression with custom element alias"""
        value_keys = ["value", "data"]
        result = self.strategy._build_value_coalesce(value_keys, "custom_elem")
        
        expected = "COALESCE(custom_elem->>'value', custom_elem->>'data', '')"
        assert result == expected
    
    def test_build_match_conditions_default(self):
        """Test building WHERE conditions with default parameters"""
        match_keys = ["question_title", "title"]
        pattern = "Test Pattern"
        result = self.strategy._build_match_conditions(match_keys, pattern)
        
        expected = ("LOWER(item->>'question_title') LIKE LOWER('%Test Pattern%')\n"
                   "                       OR LOWER(item->>'title') LIKE LOWER('%Test Pattern%')")
        assert result == expected
    
    def test_build_match_conditions_custom_alias(self):
        """Test building WHERE conditions with custom element alias"""
        match_keys = ["name", "label"]
        pattern = "Custom"
        result = self.strategy._build_match_conditions(match_keys, pattern, "custom_item")
        
        expected = ("LOWER(custom_item->>'name') LIKE LOWER('%Custom%')\n"
                   "                       OR LOWER(custom_item->>'label') LIKE LOWER('%Custom%')")
        assert result == expected
    
    def test_build_extended_value_coalesce(self):
        """Test extended value COALESCE building"""
        extended_keys = ["value_text", "value", "answer", "response", "description"]
        result = self.strategy._build_extended_value_coalesce(extended_keys)
        
        expected = "COALESCE(elem->>'value_text', elem->>'value', elem->>'answer', elem->>'response', elem->>'description', '')"
        assert result == expected
    
    def test_build_extended_match_conditions(self):
        """Test extended match conditions building"""
        extended_keys = ["question_title", "title", "question", "name", "label", "key"]
        pattern = "Extended"
        result = self.strategy._build_extended_match_conditions(extended_keys, pattern)
        
        # Should use default alias 'elem' for extended methods
        assert "LOWER(elem->>'question_title') LIKE LOWER('%Extended%')" in result
        assert "LOWER(elem->>'label') LIKE LOWER('%Extended%')" in result
        assert "LOWER(elem->>'key') LIKE LOWER('%Extended%')" in result
    
    def test_concrete_strategy_implementation(self):
        """Test that concrete strategy works correctly"""
        result = self.strategy.generate_sql_expression(self.context)
        assert result == "SELECT 'Test Field' as test_field"
        
        assert self.strategy.get_strategy_name() == "TestStrategy"
        assert self.strategy.is_applicable(self.context) is True


class TestIJsonExtractionStrategy:
    """Test the strategy interface requirements"""
    
    def test_interface_is_abstract(self):
        """Test that IJsonExtractionStrategy cannot be instantiated directly"""
        with pytest.raises(TypeError):
            # Should raise TypeError because abstract methods are not implemented
            IJsonExtractionStrategy()
    
    def test_concrete_implementation_requires_all_methods(self):
        """Test that concrete implementations must implement all abstract methods"""
        
        class IncompleteStrategy(IJsonExtractionStrategy):
            # Missing required methods
            pass
        
        with pytest.raises(TypeError):
            IncompleteStrategy()
    
    def test_complete_implementation_works(self):
        """Test that complete implementation of interface works"""
        
        class CompleteStrategy(IJsonExtractionStrategy):
            def generate_sql_expression(self, context: JsonExtractionContext) -> str:
                return "SELECT 1"
            
            def get_strategy_name(self) -> str:
                return "Complete"
            
            def is_applicable(self, context: JsonExtractionContext) -> bool:
                return True
        
        # Should not raise any errors
        strategy = CompleteStrategy()
        context = JsonExtractionContext("col", "pattern", "title", "safe_name")
        
        assert strategy.generate_sql_expression(context) == "SELECT 1"
        assert strategy.get_strategy_name() == "Complete"
        assert strategy.is_applicable(context) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
