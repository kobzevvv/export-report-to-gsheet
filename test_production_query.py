#!/usr/bin/env python3
"""Test the production function with your specific query"""

import urllib.parse

# Your exact query
test_query = """SELECT 
candidate_email,
weighted_values,
interview_shared_link,

{{fields_as_columns_from(answers_json, question_title, value_text, 
"Город проживания", 
"Ваше имя")}},

first_answer_datetime

FROM public_marts.candidates
WHERE position_name ILIKE '%додо%'
LIMIT 1"""

# URL encode the query
encoded_query = urllib.parse.quote(test_query)

# Create the test URL - using the PUBLIC test sheet (not your private one)
test_url = f"https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app?sql={encoded_query}&spreadsheet_id=12fFS6Z_9vkba66850fTnmty1VdXcBi_Anyu8Xni6r7w&sheet_name=Test%20Data&starting_cell=A1&include_headers=true"

print("Testing your query with the PUBLIC test sheet:")
print("URL:", test_url[:100] + "...")
print("\nYou can test this by running:")
print(f'curl -s "{test_url}"')

# Also show what the URL would look like for your private sheet
your_sheet_id = "1s00INXh5PbIAaG6XvhO9oW88e9gmn5V95rvrN0F9G8A"
your_url = f"https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app?sql={encoded_query}&spreadsheet_id={your_sheet_id}&sheet_name=Test%20Data&starting_cell=A1&include_headers=true"

print(f"\nAnd this is the URL for your private sheet:")
print(f"curl -s \"{your_url}\"")

print(f"\nThe key difference is the spreadsheet_id:")
print(f"- Test sheet (working): 12fFS6Z_9vkba66850fTnmty1VdXcBi_Anyu8Xni6r7w")
print(f"- Your sheet (error):   {your_sheet_id}")
