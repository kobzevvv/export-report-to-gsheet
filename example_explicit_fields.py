#!/usr/bin/env python3
"""
Example usage of the simplified fields_as_columns_from() function.

This demonstrates the explicit field approach:
- No auto-discovery needed
- Explicit list of field titles to extract
- Fields are extracted in the same order as specified
- Simple and straightforward
"""

import os
from json_unnesting import process_query_with_json_unnesting

def main():
    # Example database URL - replace with your actual database connection
    database_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/dbname')
    
    print("=== Explicit Fields Example ===")
    
    # Example SQL with the new simplified syntax
    sql_with_explicit_fields = '''
    WITH user_query_without_macro AS (
        SELECT id, name, answers_json
        FROM survey_responses 
        WHERE survey_id = 123
    )
    
    SELECT 
        id, 
        name,
        {{fields_as_columns_from(answers_json, question_title, value_text, "С какими аспектами управленческой отчётности есть опыт работы?", "Ваш Telegram никнейм")}}
    FROM user_query_without_macro
    '''
    
    try:
        # Process the query with explicit fields
        results = process_query_with_json_unnesting(sql_with_explicit_fields, database_url)
        
        print(f"Query executed successfully!")
        print(f"Returned {len(results)} rows")
        
        if results:
            print("\nColumns in results:")
            for column_name in results[0].keys():
                print(f"  - {column_name}")
                
            print("\nFirst row sample:")
            first_row = results[0]
            for key, value in first_row.items():
                # Show first 100 chars of each value
                display_value = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                print(f"  {key}: {display_value}")
                
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your database connection is configured correctly.")

def show_transformation_example():
    """Show how the SQL transformation works"""
    print("\n=== SQL Transformation Example ===")
    
    original_sql = '''
    SELECT id, name,
    {{fields_as_columns_from(answers_json, question_title, value_text, "С какими аспектами управленческой отчётности есть опыт работы?", "Ваш Telegram никнейм")}}
    FROM user_survey_data
    '''
    
    print("Original SQL:")
    print(original_sql)
    
    print("\nThis gets transformed to something like:")
    print('''
    WITH base_data AS (
        SELECT *, 
        COALESCE((
            SELECT elem->>"value_text"
            FROM jsonb_array_elements(answers_json) elem
            WHERE elem->>"question_title" = "С какими аспектами управленческой отчётности есть опыт работы?"
            LIMIT 1
        ), '') AS "с_какими_аспектами_управленческой_отчётности_есть_опыт_работы_0",
        COALESCE((
            SELECT elem->>"value_text"
            FROM jsonb_array_elements(answers_json) elem
            WHERE elem->>"question_title" = "Ваш Telegram никнейм"
            LIMIT 1
        ), '') AS "ваш_telegram_никнейм_1"
        FROM user_survey_data
    )
    SELECT * FROM base_data
    ''')

def test_parser():
    """Test the parser with different field combinations"""
    from json_unnesting import JsonUnnestingParser
    
    print("\n=== Parser Test ===")
    
    parser = JsonUnnestingParser()
    
    test_sql = '''
    SELECT {{fields_as_columns_from(answers_json, question_title, value_text, "Field 1", "Field 2", "С какими аспектами управленческой отчётности есть опыт работы?")}}
    FROM table
    '''
    
    result = parser.parse(test_sql)
    print("Parsed result:")
    print(f"  Found {len(result['unnesting_requests'])} requests")
    
    if result['unnesting_requests']:
        req = result['unnesting_requests'][0]
        print(f"  JSON column: {req['json_column']}")
        print(f"  Name key: {req['name_key']}")
        print(f"  Value key: {req['value_key']}")
        print(f"  Field titles: {req['field_titles']}")

if __name__ == "__main__":
    print("Simplified JSON Field Extraction Example")
    print("=" * 50)
    
    # Test different parts of the functionality
    main()
    show_transformation_example()
    test_parser()
    
    print("\n" + "=" * 50)
    print("Usage Summary:")
    print("Replace: {{all_fields_as_columns_from(json_col, name_key, value_key)}}")
    print("With:    {{fields_as_columns_from(json_col, name_key, value_key, \"Field 1\", \"Field 2\")}}")
    print("\nBenefits:")
    print("  ✓ Simple and explicit")
    print("  ✓ Fields in specified order")
    print("  ✓ No complex auto-discovery")
    print("  ✓ Works with Russian text")
