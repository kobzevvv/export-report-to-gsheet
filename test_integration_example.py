#!/usr/bin/env python3
"""
Integration test example for JSON unnesting feature.
This demonstrates how the feature works end-to-end.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from cloud_function.json_unnesting import JsonUnnestingParser, JsonUnnestingTransformer

def test_integration_example():
    """Demonstrate the JSON unnesting functionality"""

    # Sample SQL with custom syntax
    sql = """
    SELECT *
    FROM public_marts.candidates
    WHERE position_name ILIKE '%flutter%'
    {{all_fields_as_columns_from(answers_json, question_title, value_text)}}
    """

    print("Original SQL:")
    print(sql)
    print("\n" + "="*50 + "\n")

    # Parse the query
    parser = JsonUnnestingParser()
    parsed = parser.parse(sql)
    print(f"Parsed unnesting requests: {parsed['unnesting_requests']}")

    # Transform the query
    transformer = JsonUnnestingTransformer()
    if parsed['unnesting_requests']:
        transformed_sql = transformer.transform(sql, parsed['unnesting_requests'])
        print("Transformed SQL:")
        print(transformed_sql)
    else:
        print("No transformation needed")

if __name__ == "__main__":
    test_integration_example()
