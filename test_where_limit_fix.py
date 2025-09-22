#!/usr/bin/env python3
"""Test the WHERE/LIMIT clause fix specifically"""

from json_unnesting import JsonUnnestingParser, JsonUnnestingTransformer

test_query = """SELECT 
candidate_email,
weighted_values,
{{fields_as_columns_from(answers_json, question_title, value_text, "Test Field")}},
first_answer_datetime
FROM public_marts.candidates
WHERE position_name ILIKE '%додо%'
LIMIT 1"""

print("=== Testing WHERE/LIMIT Fix ===")
print("Original query:")
print(test_query)

parser = JsonUnnestingParser()
transformer = JsonUnnestingTransformer()

parse_result = parser.parse(test_query)
transformed_sql = transformer.transform(test_query, parse_result.get("unnesting_requests", []))

print("\n=== Transformed SQL ===")
print(transformed_sql)

print("\n=== Analysis ===")

# Check if LIMIT is in the right place (at the end, not in WHERE clause)
cte_section = transformed_sql[transformed_sql.find("WITH"):transformed_sql.find("SELECT * FROM base_data")]
final_section = transformed_sql[transformed_sql.find("SELECT * FROM base_data"):]

print("CTE section contains LIMIT:", "LIMIT" in cte_section)
print("Final section contains LIMIT:", "LIMIT" in final_section)

if "LIMIT" in cte_section:
    print("❌ PROBLEM: LIMIT is still in the wrong place!")
elif "LIMIT" in final_section:
    print("✅ GOOD: LIMIT is in the correct position")
else:
    print("⚠️ LIMIT clause missing entirely")

# Check WHERE clause structure
if "WHERE position_name ILIKE '%додо%'" in cte_section and "WHERE position_name ILIKE '%додо%'\nLIMIT" not in cte_section:
    print("✅ GOOD: WHERE clause is clean (no LIMIT included)")
elif "WHERE position_name ILIKE '%додо%'\nLIMIT" in cte_section:
    print("❌ PROBLEM: WHERE clause still contains LIMIT")
else:
    print("⚠️ WHERE clause structure unclear")

print(f"\nFinal query structure check:")
print(f"- Has CTE: {'WITH base_data AS' in transformed_sql}")
print(f"- Has clean WHERE: {'WHERE position_name ILIKE' in transformed_sql}")
print(f"- Has final LIMIT: {transformed_sql.strip().endswith('LIMIT 1')}")
