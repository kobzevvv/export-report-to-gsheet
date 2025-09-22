#!/usr/bin/env python3
"""
Quick test to verify all 5 strategies work correctly
"""

import pytest
from json_extraction.strategies.base_strategy import JsonExtractionContext
from json_extraction.strategies.nested_list_strategy import NestedListExtractionStrategy
from json_extraction.strategies.direct_field_strategy import DirectFieldExtractionStrategy
from json_extraction.strategies.flexible_array_strategy import FlexibleArrayExtractionStrategy
from json_extraction.strategies.direct_string_strategy import DirectStringValueExtractionStrategy
from json_extraction.strategies.wildcard_search_strategy import WildcardSearchExtractionStrategy


class TestAllStrategiesWork:
    """Quick verification that all 5 strategies generate valid SQL"""
    
    def setup_method(self):
        """Setup test context"""
        self.context = JsonExtractionContext(
            json_column="test_json",
            pattern="Test Field",
            field_title="Test Field",
            safe_column_name="test_field"
        )
        
        self.strategies = [
            NestedListExtractionStrategy(),
            DirectFieldExtractionStrategy(),
            FlexibleArrayExtractionStrategy(),
            DirectStringValueExtractionStrategy(),
            WildcardSearchExtractionStrategy()
        ]
    
    def test_all_strategies_generate_sql(self):
        """Test that all strategies generate valid SQL expressions"""
        for i, strategy in enumerate(self.strategies, 1):
            sql = strategy.generate_sql_expression(self.context)
            strategy_name = strategy.get_strategy_name()
            
            print(f"\n--- Strategy {i}: {strategy_name} ---")
            print(sql[:100] + "..." if len(sql) > 100 else sql)
            
            # Basic validation
            assert sql is not None, f"Strategy {i} returned None"
            assert len(sql.strip()) > 0, f"Strategy {i} returned empty SQL"
            
            # Strategy-specific validation
            if i == 2:  # DirectFieldExtractionStrategy
                assert sql == "NULL", "Strategy 2 should return NULL (disabled)"
            else:
                assert "(" in sql, f"Strategy {i} should contain subquery parentheses"
                assert "LIMIT 1" in sql or "NULL" == sql, f"Strategy {i} should have LIMIT 1 or be NULL"
    
    def test_all_strategies_have_metadata(self):
        """Test that all strategies have required metadata"""
        expected_names = [
            "NestedListExtraction",
            "DirectFieldAccess", 
            "FlexibleArrayMatching",
            "DirectStringValue",
            "WildcardSearch"
        ]
        
        for strategy, expected_name in zip(self.strategies, expected_names):
            assert strategy.get_strategy_name() == expected_name
            assert len(strategy.get_description()) > 50  # Reasonable description length
            assert isinstance(strategy.is_applicable(self.context), bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to show print statements
