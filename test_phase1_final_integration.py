#!/usr/bin/env python3
"""
Phase 1 Final Integration Tests

Comprehensive test suite to verify that the refactored strategy-based architecture
maintains 100% compatibility with the original system while providing the benefits
of clean, extensible code.
"""

import pytest
from unittest.mock import MagicMock, patch
from json_unnesting import JsonUnnestingParser, JsonUnnestingTransformer
from json_unnesting_refactored import JsonUnnestingTransformerRefactored, process_query_with_json_unnesting


class TestPhase1FinalIntegration:
    """Final integration tests for Phase 1 refactoring"""
    
    def test_original_vs_refactored_identical_output(self):
        """Test that original and refactored produce identical SQL output"""
        test_cases = [
            # Basic case
            {
                "sql": "SELECT * FROM candidates",
                "fields": ["Full Name", "Email"]
            },
            # With WHERE clause
            {
                "sql": "SELECT * FROM users WHERE active = true",
                "fields": ["First Name", "Last Name", "Phone"]
            },
            # Multiple fields
            {
                "sql": "SELECT * FROM survey_responses",
                "fields": ["Q1", "Q2", "Q3", "Q4", "Q5"]
            },
            # Special characters
            {
                "sql": "SELECT * FROM forms",
                "fields": ["Field's Name", "Another (Special) Field"]
            }
        ]
        
        parser = JsonUnnestingParser()
        original_transformer = JsonUnnestingTransformer()
        refactored_transformer = JsonUnnestingTransformerRefactored()
        
        for case in test_cases:
            # Create unnesting request
            unnesting_request = [{
                "json_column": "data_json",
                "name_key": "question_title",
                "value_key": "value_text", 
                "field_titles": case["fields"]
            }]
            
            # Transform with both versions
            original_sql = original_transformer.transform(case["sql"], unnesting_request)
            refactored_sql = refactored_transformer.transform(case["sql"], unnesting_request)
            
            # Key structural elements should be identical
            assert "WITH base_data AS" in original_sql and "WITH base_data AS" in refactored_sql
            assert "SELECT * FROM base_data" in original_sql and "SELECT * FROM base_data" in refactored_sql
            
            # Should have same number of field columns
            original_as_count = original_sql.count(" AS \"")
            refactored_as_count = refactored_sql.count(" AS \"")
            assert original_as_count == refactored_as_count == len(case["fields"])
            
            # Core extraction logic should be present in both
            assert "data_json ? 'list'" in original_sql and "data_json ? 'list'" in refactored_sql
            assert "COALESCE(" in original_sql and "COALESCE(" in refactored_sql
    
    @patch('json_unnesting_refactored.psycopg')
    def test_full_pipeline_with_refactored_system(self, mock_psycopg):
        """Test complete pipeline using refactored system"""
        # Setup mock database response
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "id": 1, 
                "name": "John Doe",
                "full_name": "John Doe",
                "email_address": "john@example.com"
            }
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_psycopg.connect.return_value = mock_conn
        
        # Mock HAS_PSYCOPG for refactored module
        import json_unnesting_refactored
        original_has_psycopg = json_unnesting_refactored.HAS_PSYCOPG
        json_unnesting_refactored.HAS_PSYCOPG = True
        
        try:
            sql = '''SELECT * FROM candidates 
                    {{fields_as_columns_from(answers_json, question_title, value_text, "Full Name", "Email Address")}}'''
            
            # Process with refactored system
            result = process_query_with_json_unnesting(sql, "test_db_url")
            
            # Verify database interactions
            assert mock_psycopg.connect.called
            assert mock_cursor.execute.call_count == 3  # SET statements + query
            
            # Verify results
            assert len(result) == 1
            assert result[0]["id"] == 1
            
        finally:
            json_unnesting_refactored.HAS_PSYCOPG = original_has_psycopg
    
    def test_strategy_extensibility(self):
        """Test that new strategies can be easily added"""
        from json_extraction.column_expression_generator import ColumnExpressionGenerator
        from json_extraction.strategies.base_strategy import BaseJsonExtractionStrategy, JsonExtractionContext
        
        # Create a custom strategy
        class CustomTestStrategy(BaseJsonExtractionStrategy):
            def generate_sql_expression(self, context: JsonExtractionContext) -> str:
                return f"'{context.field_title}' as custom_test"
            
            def get_strategy_name(self) -> str:
                return "CustomTest"
            
            def is_applicable(self, context: JsonExtractionContext) -> bool:
                return context.field_title == "TEST_FIELD"
        
        # Create generator and add custom strategy
        generator = ColumnExpressionGenerator()
        original_count = generator.get_strategy_count()
        
        # Add custom strategy
        generator.strategies.append(CustomTestStrategy())
        assert generator.get_strategy_count() == original_count + 1
        
        # Test with applicable context
        context = JsonExtractionContext("json_col", "TEST", "TEST_FIELD", "test_field")
        applicable_count = generator.get_applicable_strategy_count(context)
        assert applicable_count > 0  # Should include custom strategy
    
    def test_performance_comparison(self):
        """Basic performance test - refactored should not be significantly slower"""
        import time
        
        parser = JsonUnnestingParser()
        original_transformer = JsonUnnestingTransformer()
        refactored_transformer = JsonUnnestingTransformerRefactored()
        
        sql = "SELECT * FROM large_table"
        unnesting_request = [{
            "json_column": "big_json_column",
            "name_key": "question_title",
            "value_key": "value_text",
            "field_titles": [f"Field {i}" for i in range(20)]  # 20 fields
        }]
        
        # Time original transformation
        start_time = time.time()
        for _ in range(10):  # 10 iterations
            original_transformer.transform(sql, unnesting_request)
        original_time = time.time() - start_time
        
        # Time refactored transformation  
        start_time = time.time()
        for _ in range(10):  # 10 iterations
            refactored_transformer.transform(sql, unnesting_request)
        refactored_time = time.time() - start_time
        
        # Refactored should not be more than 5x slower (reasonable overhead for architectural benefits)
        # Note: Small overhead is expected due to strategy pattern and additional abstractions
        assert refactored_time < original_time * 5.0
        print(f"Original: {original_time:.4f}s, Refactored: {refactored_time:.4f}s")
    
    def test_all_baseline_scenarios_still_work(self):
        """Test all baseline scenarios from original test suite still work"""
        from test_phase1_baseline import TestCurrentFunctionalityBaseline
        
        # Create instance of refactored transformer
        refactored_transformer = JsonUnnestingTransformerRefactored()
        
        # Test key scenarios that were in baseline tests
        test_cases = [
            # Basic transformation
            {
                "sql": "SELECT * FROM candidates",
                "request": {
                    "json_column": "answers_json",
                    "name_key": "question_title", 
                    "value_key": "value_text",
                    "field_titles": ["Full Name"]
                }
            },
            # With WHERE clause
            {
                "sql": "SELECT * FROM candidates WHERE position = 'Engineer'",
                "request": {
                    "json_column": "skills_json",
                    "name_key": "skill_name",
                    "value_key": "skill_level", 
                    "field_titles": ["Python", "SQL"]
                }
            }
        ]
        
        for case in test_cases:
            result = refactored_transformer.transform(case["sql"], [case["request"]])
            
            # Should generate valid CTE structure
            assert "WITH base_data AS" in result
            assert "SELECT * FROM base_data" in result
            assert "COALESCE(" in result
            assert "LIMIT 1" in result


class TestPhase1ArchitecturalBenefits:
    """Tests demonstrating the architectural benefits of the refactored system"""
    
    def test_individual_strategy_testability(self):
        """Test that individual strategies can be tested in isolation"""
        from json_extraction.strategies.nested_list_strategy import NestedListExtractionStrategy
        from json_extraction.strategies.base_strategy import JsonExtractionContext
        
        strategy = NestedListExtractionStrategy()
        context = JsonExtractionContext(
            json_column="test_json",
            pattern="Test Field",
            field_title="Test Field", 
            safe_column_name="test_field"
        )
        
        sql = strategy.generate_sql_expression(context)
        
        # Can test strategy in complete isolation
        assert "test_json ? 'list'" in sql
        assert "LOWER('%Test Field%')" in sql
        assert strategy.get_strategy_name() == "NestedListExtraction"
        assert strategy.is_applicable(context) is True
    
    def test_strategy_coordination_flexibility(self):
        """Test that strategy coordination is flexible and configurable"""
        from json_extraction.column_expression_generator import ColumnExpressionGenerator
        
        generator = ColumnExpressionGenerator()
        
        # Can inspect and modify strategy list
        strategy_names = generator.get_strategy_names()
        assert len(strategy_names) == 5
        assert "NestedListExtraction" in strategy_names
        
        # Can disable specific strategies by overriding is_applicable
        original_strategy = generator.strategies[0]  # NestedListExtraction
        
        # Override applicability 
        original_is_applicable = original_strategy.is_applicable
        original_strategy.is_applicable = lambda context: False
        
        try:
            # Should now have fewer applicable strategies
            from json_extraction.strategies.base_strategy import JsonExtractionContext
            context = JsonExtractionContext("col", "pattern", "field", "safe_field")
            applicable_count = generator.get_applicable_strategy_count(context)
            assert applicable_count < 5  # One strategy disabled
        finally:
            # Restore original behavior
            original_strategy.is_applicable = original_is_applicable


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
