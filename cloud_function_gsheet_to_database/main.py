import json
import os
import re
import time
import typing
from datetime import datetime, timezone
from urllib.parse import parse_qs

import functions_framework
from googleapiclient.discovery import build
from google.auth import default as google_auth_default
import psycopg


def _iso_now() -> str:
	return datetime.now(timezone.utc).isoformat()


def _build_sheets_client():
	credentials, _ = google_auth_default(scopes=["https://www.googleapis.com/auth/spreadsheets"])
	return build("sheets", "v4", credentials=credentials)


def _read_range(sheets_api, spreadsheet_id: str, a1_notation: str) -> typing.List[typing.List[str]]:
	resp = sheets_api.spreadsheets().values().get(
		spreadsheetId=spreadsheet_id,
		range=a1_notation,
	).execute()
	return resp.get("values", [])


def _get_sheet_names(sheets_api, spreadsheet_id: str) -> typing.List[str]:
	"""Get list of sheet names in the spreadsheet."""
	resp = sheets_api.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
	return [sheet['properties']['title'] for sheet in resp['sheets']]


def _parse_export_fields(export_fields_param: str) -> typing.List[str]:
	"""Parse export_fields parameter into list of field names."""
	fields = []
	for field in export_fields_param.split(","):
		field = field.strip()
		if field:
			fields.append(field)
	return fields


def _find_header_row_and_field_indexes(values: typing.List[typing.List[str]], id_field: str, export_fields: typing.List[str]) -> typing.Tuple[int, typing.Dict[str, int], typing.List[str]]:
	"""Returns (header_row_index, {field_name_lower: column_index}, missing_fields)."""
	all_required_fields = [id_field] + export_fields
	
	for row_index, row in enumerate(values):
		if not row:
			continue
		lower_row = [str(cell).strip().lower() for cell in row]
		found_indexes = {}
		missing = []
		
		for field_name in all_required_fields:
			field_lower = field_name.lower()
			if field_lower in lower_row:
				found_indexes[field_lower] = lower_row.index(field_lower)
			else:
				missing.append(field_name)
		
		# If we found at least the ID field, use this as header row
		if id_field.lower() in found_indexes:
			return row_index, found_indexes, missing
	
	# No valid header row found
	return -1, {}, all_required_fields


def _validate_sql_identifier(name: str) -> None:
	if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name or ""):
		raise ValueError(f"Invalid SQL identifier: {name}")


def _require_token_if_configured(token_param: typing.Optional[str]):
	configured = os.getenv("PUBLIC_TRIGGER_TOKEN")
	if configured:
		if not token_param or token_param != configured:
			raise PermissionError("Unauthorized: invalid token")


@functions_framework.http
def gsheet_to_database(request):
	start_time = time.time()
	try:
		args = request.args or {}
		spreadsheet_id = args.get("spreadsheet_id")
		sheet_name = args.get("sheet_name")
		id_field = args.get("id_field")
		export_fields_param = args.get("export_fields")
		target_schema = args.get("target_schema")
		target_table = args.get("target_table")
		sheet_range = args.get("sheet_range")
		token = args.get("token")

		# Validate required params
		if not spreadsheet_id:
			return ("Missing required param: spreadsheet_id", 400)
		if not sheet_name:
			return ("Missing required param: sheet_name", 400)
		if not id_field:
			return ("Missing required param: id_field", 400)
		if not export_fields_param:
			return ("Missing required param: export_fields", 400)
		if not target_schema:
			return ("Missing required param: target_schema", 400)
		if not target_table:
			return ("Missing required param: target_table", 400)

		# Auth check if configured
		_require_token_if_configured(token)

		# Parse export fields
		export_fields = _parse_export_fields(export_fields_param)
		if not export_fields:
			return ("No valid export fields specified", 400)

		# Validate SQL identifiers
		_validate_sql_identifier(target_schema)
		_validate_sql_identifier(target_table)

		# Read from Google Sheets
		sheets_api = _build_sheets_client()
		
		# Get available sheet names for better error messages
		try:
			available_sheets = _get_sheet_names(sheets_api, spreadsheet_id)
		except Exception as e:
			return (
				json.dumps({"error": f"Failed to access spreadsheet: {str(e)}"}),
				400,
				{"Content-Type": "application/json"}
			)
		
		if sheet_name not in available_sheets:
			return (
				json.dumps({
					"error": f"Sheet '{sheet_name}' not found",
					"available_sheets": available_sheets
				}),
				400,
				{"Content-Type": "application/json"}
			)
		
		if not sheet_range:
			sheet_range = f"{sheet_name}!A1:Z1000"
		
		values = _read_range(sheets_api, spreadsheet_id, sheet_range)
		if not values:
			return (
				json.dumps({"status": "ok", "inserted_rows": 0, "note": "Sheet range is empty"}),
				200,
				{"Content-Type": "application/json"},
			)

		# Find headers and get field indexes
		header_row_index, found_indexes, missing_fields = _find_header_row_and_field_indexes(values, id_field, export_fields)
		
		if header_row_index == -1:
			return (f"No header row found with required id_field: {id_field}", 400)

		# Check if id_field was found
		id_field_lower = id_field.lower()
		if id_field_lower not in found_indexes:
			return (f"Required id_field '{id_field}' not found in sheet headers", 400)

		# Build data rows for fixed 3-column structure: entity_id, data, loaded_at_utc
		data_rows = []
		loaded_at = datetime.now(timezone.utc)
		
		for row in values[header_row_index + 1:]:
			if not row or all(not str(cell).strip() for cell in row):
				continue  # Skip empty rows
			
			# Get entity ID value
			id_col_idx = found_indexes[id_field_lower]
			entity_id = str(row[id_col_idx]).strip() if id_col_idx < len(row) else ""
			
			if not entity_id:
				continue  # Skip rows with empty ID
			
			# Build JSON data object with export fields
			data_object = {}
			for field in export_fields:
				field_lower = field.lower()
				if field_lower in found_indexes:
					col_idx = found_indexes[field_lower]
					value = str(row[col_idx]).strip() if col_idx < len(row) else ""
					data_object[field] = value
				else:
					data_object[field] = ""  # Missing field gets empty string
			
			# Convert to JSON string
			data_json = json.dumps(data_object)
			
			# Create row tuple: (entity_id, data, loaded_at_utc)
			data_rows.append((entity_id, data_json, loaded_at))

		if not data_rows:
			note = "No data rows found after header"
			if missing_fields:
				note += f". Missing fields: {', '.join(missing_fields)}"
			return (
				json.dumps({"status": "ok", "inserted_rows": 0, "note": note}),
				200,
				{"Content-Type": "application/json"},
			)

		# Connect to Neon Postgres and load data
		database_url = os.getenv("NEON_DATABASE_URL")
		if not database_url:
			return ("NEON_DATABASE_URL is not configured", 500)

		conn = psycopg.connect(database_url, connect_timeout=15, row_factory=dict_row)
		try:
			with conn.cursor() as cur:
				cur.execute("SET LOCAL statement_timeout = '60s'")

				# Create schema if not exists
				cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{target_schema}"')

				# Fixed 3-column table structure
				fqtn = f'"{target_schema}"."{target_table}"'

				# Check if table exists and has correct structure
				cur.execute("""
					SELECT column_name, data_type
					FROM information_schema.columns
					WHERE table_schema = %s AND table_name = %s
					ORDER BY ordinal_position
				""", (target_schema, target_table))

				columns = cur.fetchall()
				expected_columns = [
					('entity_id', 'text'),
					('data', 'jsonb'),
					('loaded_at_utc', 'timestamp with time zone')
				]

				table_exists_correctly = False
				if columns:
					# Check if columns match expected structure
					if len(columns) == 3:
						table_exists_correctly = all(
							col['column_name'] == expected[0] and col['data_type'] == expected[1]
							for col, expected in zip(columns, expected_columns)
						)

				if not table_exists_correctly:
					# Drop and recreate table if structure is wrong or doesn't exist
					cur.execute(f"DROP TABLE IF EXISTS {fqtn}")
					cur.execute(f'''CREATE TABLE {fqtn} (
						"entity_id" text NOT NULL,
						"data" jsonb NOT NULL,
						"loaded_at_utc" timestamptz NOT NULL
					)''')
					# Insert all data
					insert_sql = f'INSERT INTO {fqtn} ("entity_id", "data", "loaded_at_utc") VALUES (%s, %s, %s)'
					cur.executemany(insert_sql, data_rows)
				else:
					# Table exists with correct structure - use UPSERT to append/update
					upsert_sql = f'''
						INSERT INTO {fqtn} ("entity_id", "data", "loaded_at_utc")
						VALUES (%s, %s, %s)
						ON CONFLICT ("entity_id")
						DO UPDATE SET
							"data" = EXCLUDED."data",
							"loaded_at_utc" = EXCLUDED."loaded_at_utc"
					'''
					cur.executemany(upsert_sql, data_rows)
			
			conn.commit()
		finally:
			conn.close()

		# Prepare status message
		inserted_rows = len(data_rows)
		duration_ms = int((time.time() - start_time) * 1000)
		
		return (
			json.dumps({
				"status": "ok",
				"inserted_rows": inserted_rows,
				"duration_ms": duration_ms,
				"target_table": f"{target_schema}.{target_table}",
				"missing_fields": missing_fields,
				"id_field": id_field,
				"export_fields": export_fields,
			}),
			200,
			{"Content-Type": "application/json"},
		)

	except PermissionError as e:
		return (str(e), 401)
	except Exception as e:
		# Error handling (no Sheet cell updates)
		return (f"Error: {type(e).__name__}: {e}", 500)