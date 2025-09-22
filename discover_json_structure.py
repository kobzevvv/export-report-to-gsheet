#!/usr/bin/env python3
"""
Helper script to discover the actual JSON structure in your database.
This will help you identify the correct field names for the fields_as_columns_from syntax.
"""

import os
import psycopg
from psycopg.rows import dict_row

def discover_json_structure(database_url: str, table_name: str = 'public_marts.candidates', limit: int = 5):
    """Discover the structure of JSON data in the database"""

    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
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
        print("=" * 50)

        for i, row in enumerate(rows):
            json_data = row['answers_json']
            print(f"\n📋 Sample {i+1}:")
            print("-" * 30)

            if isinstance(json_data, str):
                print("JSON is stored as string, parsing...")
                try:
                    import json
                    json_data = json.loads(json_data)
                except:
                    print("❌ Could not parse JSON string")
                    continue

            # Analyze structure
            if isinstance(json_data, list):
                print(f"✅ JSON is an array with {len(json_data)} items")
                if len(json_data) > 0:
                    first_item = json_data[0]
                    if isinstance(first_item, dict):
                        print("📋 First item keys:", list(first_item.keys()))

                        # Show sample values for common patterns
                        for key in first_item.keys():
                            value = first_item[key]
                            if isinstance(value, str) and len(value) < 50:
                                print(f"   '{key}': '{value}'")
                            else:
                                print(f"   '{key}': {type(value).__name__}")
                    else:
                        print(f"First item type: {type(first_item)}")
            elif isinstance(json_data, dict):
                print(f"✅ JSON is an object with keys: {list(json_data.keys())}")

                # Show sample values
                for key in json_data.keys():
                    value = json_data[key]
                    if isinstance(value, str) and len(value) < 50:
                        print(f"   '{key}': '{value}'")
                    else:
                        print(f"   '{key}': {type(value).__name__}")
            else:
                print(f"❌ Unexpected JSON type: {type(json_data)}")

    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        print("💡 Make sure your DATABASE_URL is correct and accessible")

def main():
    database_url = os.getenv('DATABASE_URL')
    table_name = os.getenv('TABLE_NAME', 'public_marts.candidates')

    print("🔍 JSON Structure Discovery Tool")
    print("=" * 50)
    print(f"📊 Analyzing table: {table_name}")
    print(f"🗄️  Database: {database_url[:50]}..." if database_url else "❌ No DATABASE_URL")

    discover_json_structure(database_url, table_name)

    print("\n" + "=" * 50)
    print("📝 Next Steps:")
    print("1. Run this script to see your JSON structure")
    print("2. Identify the correct field names")
    print("3. Update your fields_as_columns_from syntax:")
    print("   OLD: {{fields_as_columns_from(answers_json, question_title, value_text, \"Field 1\", \"Field 2\")}}")
    print("   NEW: {{fields_as_columns_from(answers_json, [correct_title_key], [correct_value_key], \"Field 1\", \"Field 2\")}}")

if __name__ == "__main__":
    main()
