#!/usr/bin/env python3
"""
Simple script to check your JSON structure and suggest the correct field names.
Run this to see what fields actually exist in your JSON data.
"""

import os
import psycopg
from psycopg.rows import dict_row

def check_json_structure(database_url: str, table_name: str = 'public_marts.candidates', limit: int = 3):
    """Check the structure of JSON data in your database"""

    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("💡 Set it with: export DATABASE_URL='your_database_url'")
        return

    try:
        conn = psycopg.connect(database_url, connect_timeout=15, row_factory=dict_row)
        with conn.cursor() as cur:
            cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
            cur.execute("SET LOCAL statement_timeout = '30s'")

            # Get sample JSON data
            query = f"""
            SELECT answers_json
            FROM {table_name}
            WHERE answers_json IS NOT NULL
            LIMIT {limit}
            """
            cur.execute(query)
            rows = cur.fetchall()

        conn.close()

        if not rows:
            print("❌ No JSON data found in the specified table")
            return

        print(f"🔍 Found {len(rows)} sample JSON records")
        print("=" * 60)

        for i, row in enumerate(rows):
            json_data = row['answers_json']
            print(f"\n📋 Sample {i+1}:")
            print("-" * 40)

            # Handle string JSON
            if isinstance(json_data, str):
                try:
                    import json
                    json_data = json.loads(json_data)
                    print("✅ JSON parsed from string")
                except:
                    print("❌ Could not parse JSON string")
                    continue

            # Analyze structure
            if isinstance(json_data, list) and len(json_data) > 0:
                print(f"✅ JSON is an array with {len(json_data)} items")
                first_item = json_data[0]

                if isinstance(first_item, dict):
                    print("📋 Keys in first item:")
                    for key, value in first_item.items():
                        if isinstance(value, str) and len(value) < 100:
                            print(f"   '{key}': '{value}'")
                        else:
                            print(f"   '{key}': {type(value).__name__} (length: {len(str(value)) if value else 0})")

                    # Check if any keys look like field titles
                    print("\n🔍 Potential field titles found:")
                    for key, value in first_item.items():
                        if isinstance(value, str) and (value.startswith(("С ", "Ваш", "Как", "Что")) or len(value) > 10):
                            print(f"   '{key}' contains: '{value}'")
                else:
                    print(f"❌ First item is not a dictionary: {type(first_item)}")

            elif isinstance(json_data, dict):
                print("✅ JSON is an object")
                print("📋 Keys found:")
                for key, value in json_data.items():
                    if isinstance(value, str) and len(value) < 100:
                        print(f"   '{key}': '{value}'")
                    else:
                        print(f"   '{key}': {type(value).__name__}")

            else:
                print(f"❌ Unexpected JSON type: {type(json_data)}")

        print("\n" + "=" * 60)
        print("📝 Next Steps:")
        print("1. Look at the keys and values above")
        print("2. Identify which keys contain your field titles")
        print("3. Update your fields_as_columns_from syntax:")
        print("   Example: {{fields_as_columns_from(answers_json, 'title', 'value', 'Field 1', 'Field 2')}}")
        print("   Use the actual key names from your JSON structure")

    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        print("💡 Make sure your DATABASE_URL is correct and accessible")

def main():
    database_url = os.getenv('DATABASE_URL')
    table_name = os.getenv('TABLE_NAME', 'public_marts.candidates')

    print("🔍 JSON Structure Checker")
    print("=" * 50)
    print(f"📊 Analyzing table: {table_name}")

    check_json_structure(database_url, table_name)

if __name__ == "__main__":
    main()
