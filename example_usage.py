#!/usr/bin/env python3
"""
Example showing how to update your existing queries to use JSON unnesting.

BEFORE (without JSON unnesting):
curl "https://your-function-url?sql=SELECT%20*%20FROM%20public_marts.candidates%20WHERE%20position_name%20ILIKE%20%27%25flutter%25%27&spreadsheet_id=your_spreadsheet_id&sheet_name=Data"

AFTER (with JSON unnesting):
curl "https://your-function-url?sql=SELECT%20*%20FROM%20public_marts.candidates%20WHERE%20position_name%20ILIKE%20%27%25flutter%25%27%20%7B%7Ball_fields_as_columns_from(answers_json%2C%20question_title%2C%20value_text)%7D%7D&spreadsheet_id=your_spreadsheet_id&sheet_name=Data"

Note: URL encode the {{ and }} as %7B%7B and %7D%7D respectively.
"""

print("JSON Unnesting Feature - Ready for Cloud Functions!")
print("=" * 50)
print()
print("✅ Your Cloud Function is now ready to handle JSON unnesting!")
print("✅ Just update your SQL queries to include the custom syntax")
print("✅ No code changes needed - it works automatically!")
print()
print("Example query with JSON unnesting:")
print("SELECT *, {{all_fields_as_columns_from(answers_json, question_title, value_text)}}")
print("FROM public_marts.candidates")
print("WHERE position_name ILIKE '%flutter%'")
print()
print("The function will automatically:")
print("1. Parse your query for {{...}} syntax")
print("2. Transform it to use PostgreSQL JSON functions")
print("3. Execute the transformed query")
print("4. Export flattened results to Google Sheets")


