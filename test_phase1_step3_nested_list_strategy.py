#!/usr/bin/env python3
"""
Tests for Phase 1 Step 3: NestedListExtractionStrategy

Tests the first concrete strategy implementation that matches the current system's
primary extraction method for nested 'list' array structures.
"""

import pytest
from json_extraction.strategies.base_strategy import JsonExtractionContext
from json_extraction.strategies.nested_list_strategy import NestedListExtractionStrategy


class TestNestedListExtractionStrategy:
    """Test the nested list extraction strategy implementation"""
    
    def setup_method(self):
        """Setup for each test"""
        self.strategy = NestedListExtractionStrategy()
        
    def test_strategy_metadata(self):
        """Test strategy name and applicability"""
        context = JsonExtractionContext("col", "pattern", "Field", "field")
        
        assert self.strategy.get_strategy_name() == "NestedListExtraction"
        assert self.strategy.is_applicable(context) is True  # Always applicable
        assert "Nested List Extraction" in self.strategy.get_description()
    
    def test_basic_sql_generation(self):
        """Test basic SQL expression generation"""
        context = JsonExtractionContext(
            json_column="answers_json",
            pattern="Full Name", 
            field_title="Full Name",
            safe_column_name="full_name"
        )
        
        sql = self.strategy.generate_sql_expression(context)
        
        # Verify core structure
        assert "SELECT COALESCE(" in sql
        assert "FROM jsonb_array_elements(" in sql
        assert "WHERE" in sql
        assert "LIMIT 1" in sql
        
        # Verify nested list specific logic
        assert "answers_json ? 'list'" in sql
        assert "jsonb_typeof(answers_json->'list') = 'array'" in sql
        assert "answers_json->'list'" in sql
        assert "'[]'::jsonb" in sql  # Fallback empty array
    
    def test_default_value_keys_in_coalesce(self):
        """Test that default value keys are included in COALESCE"""
        context = JsonExtractionContext(
            json_column="data_json",
            pattern="Email",
            field_title="Email Address", 
            safe_column_name="email"
        )
        
        sql = self.strategy.generate_sql_expression(context)
        
        # Check for default value keys
        assert "item->>'value_text'" in sql
        assert "item->>'answer'" in sql 
        assert "item->>'text'" in sql
        assert "item->>'value'" in sql
        assert "item->>'response'" in sql
        
        # Should end with empty string fallback
        assert ", ''" in sql
    
    def test_default_match_keys_in_where(self):
        """Test that default match keys are included in WHERE conditions"""
        context = JsonExtractionContext(
            json_column="form_data",
            pattern="Phone Number",
            field_title="Phone Number",
            safe_column_name="phone"
        )
        
        sql = self.strategy.generate_sql_expression(context)
        
        # Check for default match keys in WHERE clause
        assert "LOWER(item->>'question_title') LIKE LOWER('%Phone Number%')" in sql
        assert "LOWER(item->>'title') LIKE LOWER('%Phone Number%')" in sql
        assert "LOWER(item->>'question') LIKE LOWER('%Phone Number%')" in sql
        assert "LOWER(item->>'name') LIKE LOWER('%Phone Number%')" in sql
        
        # Should use OR conditions
        assert " OR " in sql
    
    def test_custom_value_keys(self):
        """Test strategy with custom value keys"""
        custom_value_keys = ["custom_value", "data", "content", "result"]
        
        context = JsonExtractionContext(
            json_column="custom_json",
            pattern="Custom Field",
            field_title="Custom Field",
            safe_column_name="custom_field",
            value_keys=custom_value_keys
        )
        
        sql = self.strategy.generate_sql_expression(context)
        
        # Should use custom value keys instead of defaults
        assert "item->>'custom_value'" in sql
        assert "item->>'data'" in sql
        assert "item->>'content'" in sql
        assert "item->>'result'" in sql
        
        # Should not contain default keys
        assert "item->>'value_text'" not in sql
        assert "item->>'answer'" not in sql
    
    def test_custom_match_keys(self):
        """Test strategy with custom match keys"""
        custom_match_keys = ["custom_title", "label", "identifier", "field_name"]
        
        context = JsonExtractionContext(
            json_column="survey_json", 
            pattern="Age",
            field_title="Age",
            safe_column_name="age",
            match_keys=custom_match_keys
        )
        
        sql = self.strategy.generate_sql_expression(context)
        
        # Should use custom match keys
        assert "LOWER(item->>'custom_title') LIKE LOWER('%Age%')" in sql
        assert "LOWER(item->>'label') LIKE LOWER('%Age%')" in sql
        assert "LOWER(item->>'identifier') LIKE LOWER('%Age%')" in sql
        assert "LOWER(item->>'field_name') LIKE LOWER('%Age%')" in sql
        
        # Should not contain default match keys
        assert "item->>'question_title'" not in sql
        assert "item->>'title'" not in sql
    
    def test_pattern_escaping_and_handling(self):
        """Test that patterns are properly handled in SQL"""
        # Test pattern with special characters that need escaping
        context = JsonExtractionContext(
            json_column="test_json",
            pattern="Field's \"Name\"",  # Contains quotes and apostrophe
            field_title="Field's \"Name\" (Original)",
            safe_column_name="field_name"
        )
        
        sql = self.strategy.generate_sql_expression(context)
        
        # Pattern should appear in WHERE conditions
        assert "Field's \"Name\"" in sql
        assert "LOWER('%Field's \"Name\"%')" in sql
    
    def test_different_json_column_names(self):
        """Test strategy works with different JSON column names"""
        test_columns = [
            "answers_json",
            "form_data", 
            "survey_responses",
            "user_data_json",
            "complex_nested_structure"
        ]
        
        for column_name in test_columns:
            context = JsonExtractionContext(
                json_column=column_name,
                pattern="Test",
                field_title="Test Field", 
                safe_column_name="test"
            )
            
            sql = self.strategy.generate_sql_expression(context)
            
            # Column name should appear in the right places
            assert f"{column_name} ? 'list'" in sql
            assert f"jsonb_typeof({column_name}->'list')" in sql
            assert f"{column_name}->'list'" in sql
    
    def test_sql_structure_matches_original(self):
        """Test that generated SQL matches the structure from original code"""
        # Using the same parameters as in the baseline tests
        context = JsonExtractionContext(
            json_column="answers_json",
            pattern="Full Name",  # 30 char limit applied
            field_title="Full Name", 
            safe_column_name="full_name"
        )
        
        sql = self.strategy.generate_sql_expression(context)
        
        # Should match the original Strategy 1 pattern
        expected_elements = [
            "SELECT COALESCE(",
            "item->>'value_text'",
            "item->>'answer'", 
            "item->>'text'",
            "item->>'value'",
            "FROM jsonb_array_elements(",
            "CASE",
            "WHEN answers_json ? 'list' AND jsonb_typeof(answers_json->'list') = 'array'",
            "THEN answers_json->'list'",
            "ELSE '[]'::jsonb",
            "END",
            ") item",
            "WHERE LOWER(item->>'question_title') LIKE LOWER('%Full Name%')",
            "OR LOWER(item->>'title') LIKE LOWER('%Full Name%')",
            "OR LOWER(item->>'question') LIKE LOWER('%Full Name%')",
            "OR LOWER(item->>'name') LIKE LOWER('%Full Name%')",
            "LIMIT 1"
        ]
        
        for element in expected_elements:
            assert element in sql, f"Missing expected element: {element}"
    
    def test_empty_pattern_handling(self):
        """Test strategy behavior with empty pattern"""
        context = JsonExtractionContext(
            json_column="test_json",
            pattern="",  # Empty pattern
            field_title="",
            safe_column_name="empty_field"
        )
        
        sql = self.strategy.generate_sql_expression(context)
        
        # Should still generate valid SQL even with empty pattern
        assert "LIKE LOWER('%%')" in sql  # Empty pattern becomes %%
        assert "SELECT COALESCE(" in sql
        assert "LIMIT 1" in sql
    
    def test_sql_formatting_and_structure(self):
        """Test that generated SQL is properly formatted"""
        context = JsonExtractionContext(
            json_column="data_json", 
            pattern="Test",
            field_title="Test Field",
            safe_column_name="test"
        )
        
        sql = self.strategy.generate_sql_expression(context)
        
        # Should be properly formatted (no leading/trailing whitespace)
        assert sql == sql.strip()
        
        # Should have proper indentation and structure
        lines = sql.split('\n')
        assert len(lines) > 1  # Multi-line SQL
        assert lines[0].strip().startswith("(")  # Starts with opening paren
        assert lines[-1].strip().endswith(")")   # Ends with closing paren


class TestNestedListStrategyIntegration:
    """Integration tests to verify strategy works with the overall system"""
    
    def test_strategy_matches_baseline_behavior(self):
        """Test that strategy generates SQL matching current baseline behavior"""
        strategy = NestedListExtractionStrategy()
        
        # Use exact same context as baseline tests
        context = JsonExtractionContext(
            json_column="answers_json",
            pattern="Full Name",  # This matches what current system generates
            field_title="Full Name",
            safe_column_name="full_name"
        )
        
        sql = strategy.generate_sql_expression(context)
        
        # These assertions mirror the baseline test for Strategy 1
        assert "answers_json ? 'list'" in sql
        assert "jsonb_typeof(answers_json->'list') = 'array'" in sql
        assert "answers_json->'list'" in sql
        assert "jsonb_array_elements(" in sql
        assert "item->>'value_text'" in sql
        assert "item->>'question_title') LIKE LOWER('%Full Name%')" in sql


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
