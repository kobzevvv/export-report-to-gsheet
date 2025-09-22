#!/usr/bin/env python3
"""
PHASE 1 BASELINE TESTS: Comprehensive test suite for existing JSON unnesting functionality
This ensures we don't lose any functionality during refactoring.
"""

import pytest
from unittest.mock import MagicMock, patch
import json
import re
from json_unnesting import JsonUnnestingParser, JsonUnnestingTransformer, process_query_with_json_unnesting

class TestCurrentFunctionalityBaseline:
    """
    Comprehensive baseline tests to ensure refactoring doesn't break existing functionality
    """
    
    def setup_method(self):
        """Setup for each test method"""
        self.parser = JsonUnnestingParser()
        self.transformer = JsonUnnestingTransformer()
        
        # Sample data matching current system patterns
        self.sample_json_structures = {
            "nested_list": {
                "list": [
                    {"question_title": "Full Name", "value_text": "John Doe"},
                    {"question_title": "Email Address", "value_text": "john@example.com"},
                    {"question_title": "Years of Experience", "value_text": "5"}
                ]
            },
            "direct_array": [
                {"question_title": "Skills", "value": "Python, SQL"},
                {"title": "Location", "answer": "New York"}
            ],
            "mixed_keys": [
                {"question": "Availability", "response": "Immediately"},
                {"name": "Salary", "value_text": "$80000"}
            ]
        }

    def test_parser_with_explicit_field_list(self):
        """Test parser with explicit field list (current functionality)"""
        sql = '''SELECT * FROM candidates 
                {{fields_as_columns_from(answers_json, question_title, value_text, "Full Name", "Email Address", "Years of Experience")}}'''
        
        parsed = self.parser.parse(sql)
        assert len(parsed["unnesting_requests"]) == 1
        
        req = parsed["unnesting_requests"][0]
        assert req["json_column"] == "answers_json"
        assert req["name_key"] == "question_title"  
        assert req["value_key"] == "value_text"
        assert req["field_titles"] == ["Full Name", "Email Address", "Years of Experience"]

    def test_parser_field_list_parsing_quoted_strings(self):
        """Test field list parsing with different quote styles"""
        test_cases = [
            ('"Field 1", "Field 2", "Field 3"', ["Field 1", "Field 2", "Field 3"]),
            ("'Field A', 'Field B', 'Field C'", ["Field A", "Field B", "Field C"]),
            ('"Mixed Field", \'Another Field\', "Third Field"', ["Mixed Field", "Another Field", "Third Field"]),
            ('"Field with spaces", "Field-with-dashes", "Field_with_underscores"', 
             ["Field with spaces", "Field-with-dashes", "Field_with_underscores"])
        ]
        
        for field_list_str, expected_fields in test_cases:
            parsed_fields = self.parser._parse_field_list(field_list_str)
            assert parsed_fields == expected_fields, f"Failed for: {field_list_str}"

    def test_transformer_generates_5_extraction_strategies(self):
        """Test that transformer generates all 5 extraction strategies in COALESCE"""
        sql = "SELECT * FROM candidates"
        unnesting_requests = [{
            "json_column": "answers_json",
            "name_key": "question_title",
            "value_key": "value_text",
            "field_titles": ["Full Name"]
        }]
        
        transformed = self.transformer.transform(sql, unnesting_requests)
        
        # Verify all 5 extraction strategies are present
        assert "-- Try 1: Look in nested 'list' array structure" in transformed
        assert "-- Try 2: Direct field access (skipped for pattern matching approach)" in transformed
        assert "-- Try 3: Look in array elements for matching title" in transformed
        assert "-- Try 4: Look for field_title as a direct string value" in transformed
        assert "-- Try 5: Try to find the field_title anywhere in the JSON" in transformed
        
        # Verify COALESCE structure
        assert transformed.count("COALESCE(") >= 2  # At least main COALESCE and one inner COALESCE
        assert "WITH base_data AS" in transformed
        assert "SELECT * FROM base_data" in transformed

    def test_transformer_strategy1_nested_list_structure(self):
        """Test Strategy 1: Nested 'list' array structure SQL generation"""
        sql = "SELECT * FROM candidates"
        unnesting_requests = [{
            "json_column": "answers_json",
            "name_key": "question_title", 
            "value_key": "value_text",
            "field_titles": ["Full Name"]
        }]
        
        transformed = self.transformer.transform(sql, unnesting_requests)
        
        # Strategy 1 specific assertions
        assert "answers_json ? 'list'" in transformed
        assert "jsonb_typeof(answers_json->'list') = 'array'" in transformed
        assert "answers_json->'list'" in transformed
        assert "jsonb_array_elements(" in transformed
        assert "item->>'value_text'" in transformed
        assert "item->>'question_title') LIKE LOWER('%Full Name%')" in transformed

    def test_transformer_strategy3_flexible_array_matching(self):
        """Test Strategy 3: Flexible array matching SQL generation"""
        sql = "SELECT * FROM candidates"
        unnesting_requests = [{
            "json_column": "data_json",
            "name_key": "title",
            "value_key": "answer", 
            "field_titles": ["Skills"]
        }]
        
        transformed = self.transformer.transform(sql, unnesting_requests)
        
        # Strategy 3 specific assertions
        assert "jsonb_typeof(data_json) = 'array'" in transformed
        assert "jsonb_build_array(data_json)" in transformed
        assert "elem->>'value_text'" in transformed
        assert "elem->>'response'" in transformed
        assert "elem->>'description'" in transformed
        assert "elem->>'comment'" in transformed
        assert "elem->>'label'" in transformed
        assert "elem->>'key'" in transformed

    def test_transformer_safe_column_name_generation(self):
        """Test safe column name generation for PostgreSQL"""
        test_cases = [
            ("Full Name", 0, "full_name"),
            ("Email Address!", 1, "email_address"),  # No trailing underscore
            ("Years of Experience (required)", 2, "years_of_experience__required"),  # Parentheses become double underscores
            ("", 3, "field_3"),
            ("123StartWithNumber", 4, "field_123startwithnumber"),
            ("Very Long Column Name That Exceeds Normal Limits And Should Be Truncated", 5, 
             "very_long_column_name_that_exceeds_normal_limit_5")  # Should be truncated (note: "limits" -> "limit")
        ]
        
        for field_title, index, expected_base in test_cases:
            safe_name = self.transformer._make_safe_column_name(field_title, index)
            
            # Basic validations
            assert len(safe_name) <= 63, f"Column name too long: {safe_name}"
            assert re.match(r'^[a-z_][a-z0-9_]*$', safe_name), f"Invalid column name: {safe_name}"
            assert not safe_name[0].isdigit() if safe_name else True, f"Column starts with digit: {safe_name}"
            
            if field_title:  # Non-empty field titles should contain some of the original
                assert expected_base in safe_name or safe_name.startswith("field_")

    def test_transformer_with_where_clause_preservation(self):
        """Test that WHERE clauses are properly preserved"""
        sql = "SELECT * FROM candidates WHERE position = 'Engineer' AND active = true"
        unnesting_requests = [{
            "json_column": "skills_json",
            "name_key": "skill_name", 
            "value_key": "skill_level",
            "field_titles": ["Python", "SQL"]
        }]
        
        transformed = self.transformer.transform(sql, unnesting_requests)
        
        # WHERE clause should be preserved in base_data CTE
        assert "WHERE position = 'Engineer' AND active = true" in transformed
        assert "WITH base_data AS" in transformed

    def test_transformer_multiple_field_columns(self):
        """Test transformer with multiple field columns"""
        sql = "SELECT * FROM survey_responses"
        unnesting_requests = [{
            "json_column": "answers",
            "name_key": "question",
            "value_key": "response",
            "field_titles": ["Name", "Email", "Age", "Comments"]
        }]
        
        transformed = self.transformer.transform(sql, unnesting_requests)
        
        # Should generate 4 column expressions (one for each field)
        coalesce_count = transformed.count("COALESCE(")
        assert coalesce_count >= 4, f"Expected at least 4 COALESCE expressions, found {coalesce_count}"
        
        # Each field should generate a safe column name
        assert '"name"' in transformed or '"name_' in transformed
        assert '"email"' in transformed or '"email_' in transformed  
        assert '"age"' in transformed or '"age_' in transformed
        assert '"comments"' in transformed or '"comments_' in transformed

    def test_transformer_pattern_escaping(self):
        """Test that field titles are properly escaped in SQL patterns"""
        sql = "SELECT * FROM data"
        unnesting_requests = [{
            "json_column": "json_col",
            "name_key": "key",
            "value_key": "val", 
            "field_titles": ["Field with 'quotes'", "Field with \"double quotes\""]
        }]
        
        transformed = self.transformer.transform(sql, unnesting_requests)
        
        # Single quotes should be escaped to double single quotes
        assert "Field with ''quotes''" in transformed
        # Double quotes in field titles should be handled
        assert "Field with" in transformed

    def test_transformer_empty_field_titles(self):
        """Test transformer behavior with empty field titles list"""
        sql = "SELECT * FROM table"
        unnesting_requests = [{
            "json_column": "json_col",
            "name_key": "key",
            "value_key": "val",
            "field_titles": []
        }]
        
        transformed = self.transformer.transform(sql, unnesting_requests)
        
        # Should return clean SQL without template syntax but still uses CTE structure
        assert "{{" not in transformed
        assert "}}" not in transformed
        assert "WITH base_data AS" in transformed  # Still generates CTE even with empty fields
        assert "SELECT * FROM base_data" in transformed

    def test_transformer_no_unnesting_requests(self):
        """Test transformer with no unnesting requests"""
        sql = "SELECT * FROM table {{fields_as_columns_from(col, k, v, \"field\")}}"
        unnesting_requests = []
        
        transformed = self.transformer.transform(sql, unnesting_requests)
        
        # Should clean template syntax and return simple SQL
        expected = "SELECT * FROM table"
        assert transformed.strip() == expected

    @patch('json_unnesting.psycopg')
    def test_process_query_integration_with_unnesting(self, mock_psycopg):
        """Integration test: full process with JSON unnesting"""
        # Setup mock database response
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "id": 1, 
                "name": "John Doe",
                "full_name": "John Doe",  # Generated column
                "email_address": "john@example.com"  # Generated column
            }
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_psycopg.connect.return_value = mock_conn
        
        # Mock HAS_PSYCOPG
        import json_unnesting
        original_has_psycopg = json_unnesting.HAS_PSYCOPG
        json_unnesting.HAS_PSYCOPG = True
        
        try:
            sql = '''SELECT * FROM candidates 
                    {{fields_as_columns_from(answers_json, question_title, value_text, "Full Name", "Email Address")}}'''
            
            result = process_query_with_json_unnesting(sql, "test_db_url")
            
            # Verify database interactions
            assert mock_psycopg.connect.called
            assert mock_cursor.execute.call_count == 3  # SET statements + query
            
            # Verify transformed SQL was executed
            executed_calls = mock_cursor.execute.call_args_list
            final_sql = executed_calls[-1][0][0]  # Last call, first argument
            assert "WITH base_data AS" in final_sql
            assert "COALESCE(" in final_sql
            
            # Verify results
            assert len(result) == 1
            assert result[0]["id"] == 1
            
        finally:
            json_unnesting.HAS_PSYCOPG = original_has_psycopg

    def test_process_query_without_psycopg(self):
        """Test process_query when psycopg is not available"""
        # Temporarily disable psycopg
        import json_unnesting
        original_has_psycopg = json_unnesting.HAS_PSYCOPG
        json_unnesting.HAS_PSYCOPG = False
        
        try:
            sql = "SELECT * FROM table"
            result = process_query_with_json_unnesting(sql, "fake_url")
            
            # Should return empty list when psycopg not available
            assert result == []
        finally:
            json_unnesting.HAS_PSYCOPG = original_has_psycopg

    def test_transformer_validation_missing_keys(self):
        """Test transformer validation with missing required keys"""
        sql = "SELECT * FROM table"
        invalid_request = {"json_column": "col"}  # Missing required keys
        
        with pytest.raises(ValueError, match="Invalid unnesting request: missing required keys"):
            self.transformer.transform(sql, [invalid_request])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
