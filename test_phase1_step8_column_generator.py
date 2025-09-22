#!/usr/bin/env python3
"""
Tests for Phase 1 Step 8: ColumnExpressionGenerator

Tests the strategy coordinator that generates complete COALESCE expressions.
"""

import pytest
from json_extraction.column_expression_generator import ColumnExpressionGenerator
from json_extraction.strategies.base_strategy import JsonExtractionContext


class TestColumnExpressionGenerator:
    """Test the column expression generator that coordinates all strategies"""
    
    def setup_method(self):
        """Setup for each test"""
        self.generator = ColumnExpressionGenerator()
    
    def test_generator_initialization(self):
        """Test that generator initializes with all 5 strategies"""
        assert self.generator.get_strategy_count() == 5
        
        strategy_names = self.generator.get_strategy_names()
        expected_names = [
            "NestedListExtraction",
            "DirectFieldAccess",
            "FlexibleArrayMatching", 
            "DirectStringValue",
            "WildcardSearch"
        ]
        
        assert strategy_names == expected_names
    
    def test_generate_column_expression_basic(self):
        """Test basic column expression generation"""
        sql = self.generator.generate_column_expression(
            field_title="Full Name",
            index=0,
            json_column="answers_json"
        )
        
        # Should contain COALESCE with multiple strategies
        assert "COALESCE(" in sql
        assert "AS \"full_name\"" in sql  # Safe column name alias
        
        # Should contain elements from applicable strategies
        assert "answers_json ? 'list'" in sql  # Strategy 1 
        # Strategy 2 is disabled (not applicable), so NULL won't appear
        assert "jsonb_typeof(answers_json)" in sql  # Strategy 3+
        assert "LIMIT 1" in sql
        
        # Should end with empty string fallback
        assert ", ''" in sql
    
    def test_pattern_creation(self):
        """Test pattern creation from field titles"""
        # Test normal field title
        pattern1 = self.generator._create_pattern("Full Name")
        assert pattern1 == "Full Name"
        
        # Test field with quotes (should be escaped)
        pattern2 = self.generator._create_pattern("Field's \"Name\"")
        assert pattern2 == "Field''s \"Name\""  # Single quotes escaped
        
        # Test long field title (should be truncated)
        long_title = "This is a very long field title that exceeds thirty characters"
        pattern3 = self.generator._create_pattern(long_title)
        assert len(pattern3) == 30
        assert pattern3 == long_title[:30]
    
    def test_safe_column_name_generation(self):
        """Test safe column name generation matches original behavior"""
        test_cases = [
            ("Full Name", 0, "full_name"),
            ("Email Address!", 1, "email_address"),
            ("Years of Experience (required)", 2, "years_of_experience__required"),
            ("", 3, "field_3"),
            ("123StartWithNumber", 4, "field_123startwithnumber"),
        ]
        
        for field_title, index, expected in test_cases:
            result = self.generator._make_safe_column_name(field_title, index)
            assert result == expected, f"Failed for '{field_title}': expected {expected}, got {result}"
    
    def test_multiple_field_generation(self):
        """Test generating expressions for multiple fields"""
        field_titles = ["Name", "Email", "Phone", "Age"]
        
        for i, title in enumerate(field_titles):
            sql = self.generator.generate_column_expression(
                field_title=title,
                index=i,
                json_column="data_json"
            )
            
            # Each should have unique column alias
            safe_name = self.generator._make_safe_column_name(title, i)
            assert f'AS "{safe_name}"' in sql
            
            # Each should contain pattern matching for the specific title
            assert f"LIKE LOWER('%{title}%')" in sql
            
            # All should reference same JSON column
            assert "data_json" in sql
    
    def test_applicable_strategy_count(self):
        """Test counting applicable strategies"""
        context = JsonExtractionContext(
            json_column="test_json",
            pattern="Test",
            field_title="Test Field",
            safe_column_name="test"
        )
        
        # Currently Strategy 2 (DirectFieldAccess) is disabled
        applicable_count = self.generator.get_applicable_strategy_count(context)
        assert applicable_count == 4  # 5 total - 1 disabled = 4
    
    def test_generated_sql_structure(self):
        """Test that generated SQL has correct structure"""
        sql = self.generator.generate_column_expression(
            field_title="Test Field", 
            index=0,
            json_column="json_col"
        )
        
        # Should be properly formatted
        assert sql.strip() == sql  # No leading/trailing whitespace
        
        # Should have proper COALESCE structure
        coalesce_count = sql.count("COALESCE(")
        assert coalesce_count >= 4  # At least 4 inner COALESCE + 1 main = 5 minimum
        
        # Should have proper parentheses balance
        open_parens = sql.count("(")
        close_parens = sql.count(")")
        assert open_parens == close_parens  # Balanced parentheses
    
    def test_matches_original_output_pattern(self):
        """Test that output matches pattern from baseline tests"""
        # Use same parameters as baseline tests
        sql = self.generator.generate_column_expression(
            field_title="Full Name",
            index=0, 
            json_column="answers_json"
        )
        
        # Should match key elements from baseline Strategy 1 test
        assert "answers_json ? 'list'" in sql
        assert "jsonb_typeof(answers_json->'list') = 'array'" in sql
        assert "jsonb_array_elements(" in sql
        assert "item->>'value_text'" in sql
        assert "LOWER('%Full Name%')" in sql
        
        # Should match baseline safe column name
        assert 'AS "full_name"' in sql
    
    def test_different_json_columns(self):
        """Test generator works with different JSON column names"""
        columns = ["answers_json", "form_data", "survey_responses", "user_data"]
        
        for column in columns:
            sql = self.generator.generate_column_expression(
                field_title="Test",
                index=0,
                json_column=column
            )
            
            # Should reference the correct column throughout
            assert f"{column} ? 'list'" in sql  # Strategy 1
            assert f"jsonb_typeof({column})" in sql  # Strategies 3-5
            
            # Should not reference other column names
            for other_column in columns:
                if other_column != column:
                    assert other_column not in sql


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
