#!/usr/bin/env python3
"""Help fix the SELECT * EXCEPT syntax issue"""

print("=== PostgreSQL vs BigQuery Syntax Issue ===\n")

print("❌ PROBLEM: You're using BigQuery syntax on PostgreSQL database")
print("Your query: SELECT * except(candidate_last_name, position_id, ...)")
print("Database: PostgreSQL (doesn't support EXCEPT in SELECT)")
print()

print("✅ SOLUTION: Use explicit column selection")
print()

# Show the columns they want to exclude
excluded_columns = [
    "candidate_last_name", 
    "position_id", 
    "candidate_first_name", 
    "candidate_phone", 
    "first_answer_datetime", 
    "position_name"
]

print("Columns you want to EXCLUDE:")
for col in excluded_columns:
    print(f"  - {col}")

print()
print("Instead, you should explicitly SELECT only the columns you want:")
print()

# Based on their previous working query, suggest the explicit columns
suggested_columns = [
    "candidate_email",
    "weighted_values", 
    "interview_shared_link",
    "candidate_status",
    "factual_values",
    "all_metrics_weighted",
    "metrics_json_avg",
    "candidate_salary",
    "candidate_salary_currency", 
    "candidate_linkedin_url",
    "typeform_last_submitted_at",
    "answers_json"
]

print("SUGGESTED FIX - Replace your query with:")
print()
print("SELECT")
for i, col in enumerate(suggested_columns):
    comma = "," if i < len(suggested_columns) - 1 else ""
    print(f"  {col}{comma}")

print("  {{fields_as_columns_from(answers_json, question_title, value_text,")
print("    \"Город проживания\",")
print("    \"Ваше имя\",")
print("    \"Ожидаемая месячная заработная в рублях до вычета НДФЛ\",")
print("    \"Максимальный бюджет по окладу на позицию: 100 000 руб.\",")
print("    \"Ссылка на резюме\",")
print("    \"Опыт работы в управленческих финансах\",")
print("    \"С какими аспектами управленческой отчётности есть опыт работы?\",")
print("    \"С какими регулярными процессами есть опыт?\",")
print("    \"В каких проектных задачах участвовали?\",")
print("    \"С какими инструментами бюджетирования работали?\",")
print("    \"Какие элементы налогового учёта знакомы на практике?\",")
print("    \"Ваш Telegram никнейм\"")
print("  )}}")
print("FROM public_marts.candidates")  
print("WHERE position_name ILIKE '%додо%'")

print()
print("KEY DIFFERENCES:")
print("❌ BigQuery:     SELECT * EXCEPT(column1, column2)")
print("✅ PostgreSQL:   SELECT column1, column2, column3 (explicit list)")
print()
print("This will give you:")
print("1. ✅ Only the columns you want (no excluded columns)")
print("2. ✅ Correct column ordering") 
print("3. ✅ Working JSON field extraction")
print("4. ✅ Actual data values (not empty)")

print()
print("NOTE: You can always add/remove columns from the explicit list as needed!")


