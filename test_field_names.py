#!/usr/bin/env python3
"""
Test script to try different field name combinations for JSON unnesting.
Run this to find the correct field names for your JSON data.
"""

import os
from json_unnesting import JsonUnnestingParser, JsonUnnestingTransformer

def test_field_combinations():
    """Test different field name combinations to find what works"""

    # Your SQL with the new syntax
    base_sql = '''SELECT *, {{fields_as_columns_from(answers_json, [title_key], [value_key], "С какими аспектами управленческой отчётности есть опыт работы?", "Ваш Telegram никнейм")}} FROM public_marts.candidates WHERE position_name ILIKE '%додо%' '''

    # Common field name combinations to try
    field_combinations = [
        ("question_title", "value_text"),      # Original assumption
        ("title", "value"),                    # Common alternative
        ("title", "text"),                     # Another common alternative
        ("name", "value"),                     # Another possibility
        ("question", "answer"),                # Another possibility
        ("text", "value"),                     # Another possibility
    ]

    print("🔍 Testing Field Name Combinations")
    print("=" * 60)

    for title_key, value_key in field_combinations:
        print(f"\n🧪 Testing: title_key='{title_key}', value_key='{value_key}'")
        print("-" * 50)

        # Replace placeholders
        test_sql = base_sql.replace('[title_key]', title_key).replace('[value_key]', value_key)

        try:
            # Parse and transform
            parser = JsonUnnestingParser()
            result = parser.parse(test_sql)

            if result['unnesting_requests']:
                transformer = JsonUnnestingTransformer()
                transformed_sql = transformer.transform(test_sql, result['unnesting_requests'])

                print("✅ TRANSFORMATION SUCCESSFUL!")
                print("🔄 Transformed SQL:")
                print(transformed_sql)
                print("\n💡 Try this SQL directly in your database to test if it works")
            else:
                print("❌ No unnesting requests found")

        except Exception as e:
            print(f"❌ TRANSFORMATION FAILED: {e}")

    print("\n" + "=" * 60)
    print("📝 Instructions:")
    print("1. Run this script to see which field names work")
    print("2. Find the combination that doesn't produce SQL errors")
    print("3. Update your Google Sheet query with the correct field names")
    print("4. Test the updated query in your Google Sheet")

def main():
    print("🧪 JSON Field Name Testing Tool")
    print("=" * 50)

    test_field_combinations()

if __name__ == "__main__":
    main()
