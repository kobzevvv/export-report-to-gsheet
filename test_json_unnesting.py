import pytest
from unittest.mock import MagicMock, patch
import json
from cloud_function.json_unnesting import JsonUnnestingParser, JsonUnnestingTransformer, process_query_with_json_unnesting

# Sample JSON data for testing (based on user's example)
SAMPLE_ANSWERS_JSON = {
    "list": [
        {
            "value": "test_value_1",
            "question": "q1",
            "value_text": "value_text_1",
            "question_title": "Question Title 1"
        },
        {
            "value": "test_value_2",
            "question": "q2",
            "value_text": "value_text_2",
            "question_title": "Question Title 2"
        }
    ]
}

class TestJsonUnnestingParser:
    def test_parse_custom_syntax_basic(self):
        """Test parsing of basic custom syntax {{all_fields_as_columns_from(column, key1, key2)}}"""
        parser = JsonUnnestingParser()
        sql = "SELECT * FROM table {{all_fields_as_columns_from(answers_json, question_title, value_text)}}"
        parsed = parser.parse(sql)

        assert len(parsed["unnesting_requests"]) == 1
        req = parsed["unnesting_requests"][0]
        assert req["json_column"] == "answers_json"
        assert req["name_key"] == "question_title"
        assert req["value_key"] == "value_text"

    def test_parse_custom_syntax_with_brackets(self):
        """Test parsing with double brackets syntax"""
        parser = JsonUnnestingParser()
        sql = "SELECT *, {{all_fields_as_columns_from(answers_json, question_title, value_text)}} FROM table"
        parsed = parser.parse(sql)

        assert len(parsed["unnesting_requests"]) == 1
        req = parsed["unnesting_requests"][0]
        assert req["json_column"] == "answers_json"

    def test_parse_multiple_requests(self):
        """Test parsing multiple unnesting requests in one query"""
        parser = JsonUnnestingParser()
        sql = "SELECT * FROM table {{all_fields_as_columns_from(col1, k1, v1)}} {{all_fields_as_columns_from(col2, k2, v2)}}"
        parsed = parser.parse(sql)

        assert len(parsed["unnesting_requests"]) == 2
        assert parsed["unnesting_requests"][0]["json_column"] == "col1"
        assert parsed["unnesting_requests"][1]["json_column"] == "col2"

    def test_parse_no_custom_syntax(self):
        """Test parsing query without custom syntax returns empty requests"""
        parser = JsonUnnestingParser()
        sql = "SELECT * FROM table WHERE id = 1"
        parsed = parser.parse(sql)

        assert len(parsed["unnesting_requests"]) == 0

class TestJsonUnnestingTransformer:
    def test_transform_basic_query(self):
        """Test transforming a basic query with unnesting"""
        transformer = JsonUnnestingTransformer()
        sql = "SELECT * FROM public_marts.candidates {{all_fields_as_columns_from(answers_json, question_title, value_text)}}"
        unnesting_requests = [{"json_column": "answers_json", "name_key": "question_title", "value_key": "value_text"}]

        transformed = transformer.transform(sql, unnesting_requests)

        # Should contain CTE for unnesting
        assert "WITH" in transformed
        assert "unnested_answers_json" in transformed
        assert "jsonb_array_elements" in transformed
        assert "question_title" in transformed

    def test_transform_with_where_clause(self):
        """Test transforming query with WHERE clause"""
        transformer = JsonUnnestingTransformer()
        sql = "SELECT * FROM public_marts.candidates WHERE position_name ILIKE '%flutter%' {{all_fields_as_columns_from(answers_json, question_title, value_text)}}"
        unnesting_requests = [{"json_column": "answers_json", "name_key": "question_title", "value_key": "value_text"}]

        transformed = transformer.transform(sql, unnesting_requests)

        # WHERE clause should not be in transformed SQL since we removed it
        assert "WHERE position_name ILIKE '%flutter%'" not in transformed
        assert "unnested_answers_json" in transformed

class TestProcessQueryWithJsonUnnesting:
    @patch('cloud_function.json_unnesting.psycopg')
    def test_process_query_integration(self, mock_psycopg):
        """Integration test for processing query with JSON unnesting"""
        # Set HAS_PSYCOPG to True for this test
        from cloud_function import json_unnesting
        json_unnesting.HAS_PSYCOPG = True

        # Mock database connection and cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"id": 1, "answers_json_question_title_1": "Question Title 1", "answers_json_value_text_1": "value_text_1"},
            {"id": 1, "answers_json_question_title_2": "Question Title 2", "answers_json_value_text_2": "value_text_2"}
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_psycopg.connect.return_value = mock_conn

        sql = "SELECT * FROM public_marts.candidates {{all_fields_as_columns_from(answers_json, question_title, value_text)}}"
        result = process_query_with_json_unnesting(sql, "fake_db_url")

        # Verify that the transformed query was executed
        assert mock_cursor.execute.call_count == 3  # SET statements + our query
        calls = mock_cursor.execute.call_args_list
        transformed_call = calls[-1]  # Last call should be our transformed query
        executed_sql = transformed_call[0][0]
        assert "WITH" in executed_sql
        assert "unnested_answers_json" in executed_sql

        # Verify result structure
        assert len(result) == 2
        assert "answers_json_question_title_1" in result[0]

    def test_process_query_no_unnesting(self):
        """Test processing query without unnesting requests"""
        sql = "SELECT * FROM public_marts.candidates WHERE id = 1"
        result = process_query_with_json_unnesting(sql, "fake_db_url")

        # Should return empty list when no DB connection is actually made
        assert result == []

class TestErrorHandling:
    def test_invalid_json_column(self):
        """Test handling of invalid JSON column in unnesting request"""
        transformer = JsonUnnestingTransformer()
        sql = "SELECT * FROM table"
        unnesting_requests = [{"json_column": "invalid_col"}]  # Missing required keys

        # Should handle gracefully or raise appropriate error
        with pytest.raises(ValueError):
            transformer.transform(sql, unnesting_requests)

if __name__ == "__main__":
    pytest.main()
