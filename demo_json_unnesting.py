#!/usr/bin/env python3
"""
Demonstration of the JSON unnesting feature for Google Sheets export.

This feature allows you to unnest JSON fields in your database queries
and export the flattened data to Google Sheets.

Usage:
1. Include {{all_fields_as_columns_from(json_column, name_key, value_key)}} in your SQL
2. The system will automatically transform it into a CTE that unnests the JSON
3. Results are exported to Google Sheets as usual

Example SQL:
SELECT *, {{all_fields_as_columns_from(answers_json, question_title, value_text)}}
FROM public_marts.candidates
WHERE position_name ILIKE '%flutter%'
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from cloud_function.json_unnesting import JsonUnnestingParser, JsonUnnestingTransformer

def demo():
    print("=" * 60)
    print("JSON Unnesting Feature Demo")
    print("=" * 60)

    # Example 1: Basic unnesting
    print("\n1. Basic JSON Unnesting:")
    print("-" * 30)

    sql1 = """
    SELECT *
    FROM public_marts.candidates
    {{all_fields_as_columns_from(answers_json, question_title, value_text)}}
    """

    parser = JsonUnnestingParser()
    transformer = JsonUnnestingTransformer()

    parsed = parser.parse(sql1)
    print(f"Parsed requests: {parsed['unnesting_requests']}")

    if parsed['unnesting_requests']:
        transformed = transformer.transform(sql1, parsed['unnesting_requests'])
        print("Transformed SQL:")
        print(transformed)

    # Example 2: With WHERE clause
    print("\n2. JSON Unnesting with WHERE Clause:")
    print("-" * 30)

    sql2 = """
    SELECT *
    FROM public_marts.candidates
    WHERE position_name ILIKE '%flutter%'
    {{all_fields_as_columns_from(answers_json, question_title, value_text)}}
    """

    parsed2 = parser.parse(sql2)
    print(f"Parsed requests: {parsed2['unnesting_requests']}")

    if parsed2['unnesting_requests']:
        transformed2 = transformer.transform(sql2, parsed2['unnesting_requests'])
        print("Transformed SQL:")
        print(transformed2)

    # Example 3: Multiple JSON fields
    print("\n3. Multiple JSON Fields:")
    print("-" * 30)

    sql3 = """
    SELECT *
    FROM public_marts.candidates
    {{all_fields_as_columns_from(answers_json, question_title, value_text)}}
    {{all_fields_as_columns_from(other_json, field_name, field_value)}}
    """

    parsed3 = parser.parse(sql3)
    print(f"Parsed requests: {parsed3['unnesting_requests']}")

    if parsed3['unnesting_requests']:
        transformed3 = transformer.transform(sql3, parsed3['unnesting_requests'])
        print("Transformed SQL:")
        print(transformed3)

    print("\n" + "=" * 60)
    print("How it works:")
    print("1. The parser identifies {{all_fields_as_columns_from(...)}} syntax")
    print("2. The transformer converts it to SQL CTEs with jsonb_array_elements")
    print("3. The result is a flattened table with columns for each JSON key-value pair")
    print("4. Data is exported to Google Sheets with the flattened structure")
    print("=" * 60)

if __name__ == "__main__":
    demo()
