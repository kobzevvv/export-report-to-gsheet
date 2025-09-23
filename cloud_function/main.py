import json
import os
import re
import time
import typing
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs

import functions_framework
import sqlparse
from googleapiclient.discovery import build
from google.auth import default as google_auth_default
import psycopg
from psycopg.rows import dict_row

# Import JSON unnesting functionality
from json_unnesting import process_query_with_json_unnesting


def _iso_now() -> str:
	return datetime.now(timezone.utc).isoformat()

# Version marker for deployment tracking
DEPLOYMENT_VERSION = "2025-09-23-v2"


def _strip_template_syntax(sql: str) -> str:
	"""Remove JSON unnesting template syntax for validation purposes"""
	# Pattern to match {{fields_as_columns_from(...)}} syntax
	template_pattern = r'\{\{fields_as_columns_from\([^}]+\)\}\}'
	clean_sql = re.sub(template_pattern, '', sql)

	# Clean up any malformed SQL after template removal
	# Fix SELECT clauses with trailing commas
	clean_sql = re.sub(r'SELECT\s*,\s*', 'SELECT ', clean_sql, flags=re.IGNORECASE)
	# Fix SELECT * followed by nothing
	clean_sql = re.sub(r'SELECT\s*\*\s*,?\s*$', 'SELECT 1', clean_sql, flags=re.IGNORECASE)

	return clean_sql.strip()

def _is_select_only(sql: str) -> bool:
	# Basic guardrail: ensure the first statement is a SELECT and no DDL/DML keywords present
	# First strip template syntax for validation
	clean_sql = _strip_template_syntax(sql)

	statements = [s for s in sqlparse.parse(clean_sql) if str(s).strip()]
	if len(statements) != 1:
		return False
	stmt = statements[0]
	# Ensure SELECT
	first_token = next((t for t in stmt.tokens if not t.is_whitespace), None)
	if not first_token or first_token.ttype is None and first_token.value.upper() != "SELECT":
		# token types vary; fallback to simple startswith check
		if not str(stmt).strip().upper().startswith("SELECT"):
			return False
	# Disallow dangerous keywords
	forbidden = ["INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "TRUNCATE", ";"]
	upper_sql = str(stmt).upper()
	return not any(f in upper_sql for f in forbidden)


def _apply_row_limit(sql: str, row_limit: int) -> str:
	# If SQL already has LIMIT (naive check), do not add another. Otherwise wrap.
	# Strip template syntax before checking for LIMIT to avoid interference
	clean_sql = _strip_template_syntax(sql)
	if re.search(r"\bLIMIT\b", clean_sql, flags=re.IGNORECASE):
		return sql
	# Wrap the original query to safely apply LIMIT
	return f"SELECT * FROM ( {sql} ) AS subquery_with_limit LIMIT {int(row_limit)}"


def _to_sheet_values(rows: typing.Iterable[dict], include_headers: bool) -> typing.List[typing.List[str]]:
	values: typing.List[typing.List[str]] = []
	iterator = iter(rows)
	first_row: typing.Optional[dict] = None
	try:
		first_row = next(iterator)
	except StopIteration:
		# no rows
		return [[]] if include_headers else []
	columns = list(first_row.keys())
	if include_headers:
		values.append(columns)
	def convert(value: typing.Any) -> str:
		if value is None:
			return ""
		if isinstance(value, (datetime,)):
			if value.tzinfo is None:
				value = value.replace(tzinfo=timezone.utc)
			return value.isoformat()
		return str(value)
	# append first row
	values.append([convert(first_row.get(c)) for c in columns])
	# remaining rows
	for r in iterator:
		values.append([convert(r.get(c)) for c in columns])
	return values


def _build_sheets_client():
	credentials, _ = google_auth_default(scopes=["https://www.googleapis.com/auth/spreadsheets"])
	return build("sheets", "v4", credentials=credentials)


def _check_google_sheets_access(sheets_api, spreadsheet_id: str) -> str:
	"""Check if the service account has access to the Google Sheet"""
	try:
		# Try to get basic sheet info - this will fail if no access
		resp = sheets_api.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
		return None  # No error, access is good
	except Exception as e:
		error_str = str(e).lower()

		if "forbidden" in error_str or "permission" in error_str:
			return f"❌ PERMISSION DENIED: The Cloud Function service account doesn't have access to this Google Sheet. Please share the sheet with the service account email (found in Cloud Console > IAM & Admin > Service Accounts) and give it 'Editor' access."

		if "not found" in error_str:
			return f"❌ SPREADSHEET NOT FOUND: The spreadsheet '{spreadsheet_id}' doesn't exist or is inaccessible."

		return f"❌ GOOGLE SHEETS API ERROR: {e}"


def _read_cell(sheets_api, spreadsheet_id: str, a1_notation: str) -> str:
	resp = sheets_api.spreadsheets().values().get(
		spreadsheetId=spreadsheet_id,
		range=a1_notation,
	).execute()
	values = resp.get("values", [])
	if not values or not values[0]:
		return ""
	return str(values[0][0])


def _update_cell(sheets_api, spreadsheet_id: str, a1_notation: str, value: str):
	sheets_api.spreadsheets().values().update(
		spreadsheetId=spreadsheet_id,
		range=a1_notation,
		valueInputOption="RAW",
		body={"values": [[value]]},
	).execute()


def _clear_range(sheets_api, spreadsheet_id: str, sheet_name: str, starting_cell: str):
	# Clear a reasonable range starting from starting_cell downwards
	# Using a more reasonable range to avoid Google Sheets API limits
	clear_range = f"{sheet_name}!{starting_cell}:Z1000"
	try:
		sheets_api.spreadsheets().values().clear(
			spreadsheetId=spreadsheet_id,
			range=clear_range,
			body={},
		).execute()
	except Exception as e:
		# Log the error but don't fail the entire operation
		print(f"Warning: Could not clear range {clear_range}: {e}")


def _write_values(sheets_api, spreadsheet_id: str, sheet_name: str, starting_cell: str, values: typing.List[typing.List[str]], value_input_option: str):
	# For large datasets, batch the writes to avoid memory issues
	BATCH_SIZE = 10000  # Adjust based on your needs
	for i in range(0, len(values), BATCH_SIZE):
		batch = values[i:i + BATCH_SIZE]
		# Calculate the correct starting cell for this batch
		if i == 0:
			current_cell = starting_cell
		else:
			# For subsequent batches, start from where the previous batch would end
			# This assumes starting_cell is like "A2", "B10", etc.
			cell_parts = starting_cell.split('!')
			sheet_part = cell_parts[0]
			cell_part = cell_parts[1] if len(cell_parts) > 1 else starting_cell

			# Simple cell calculation - you might need more sophisticated logic
			# for different starting cell formats
			batch_start_row = i + 1  # +1 because we want to start after previous batch
			current_cell = f"{sheet_part}!A{batch_start_row}"

		sheets_api.spreadsheets().values().update(
			spreadsheetId=spreadsheet_id,
			range=f"{sheet_name}!{current_cell}",
			valueInputOption=value_input_option,
			body={"values": batch},
		).execute()


def _require_token_if_configured(token_param: typing.Optional[str]):
	configured = os.getenv("PUBLIC_TRIGGER_TOKEN")
	if configured:
		if not token_param or token_param != configured:
			raise PermissionError("Unauthorized: invalid token")


def _get_enhanced_error_message(exception: Exception, request, sql: str = None) -> str:
	"""Provide user-friendly error messages for common issues"""
	error_str = str(exception)
	args = request.args or {}

	# Check for Google API authentication errors
	if "authentication" in error_str.lower() or "credentials" in error_str.lower():
		return f"❌ GOOGLE SHEETS API ERROR: Authentication failed. The Cloud Function service account doesn't have proper Google Sheets API access. Please check: 1) Service account permissions in Google Cloud Console 2) Google Sheets API is enabled 3) Service account has access to the spreadsheet"

	# Check for permission/access errors
	if "permission" in error_str.lower() or "access" in error_str.lower() or "forbidden" in error_str.lower():
		return f"❌ GOOGLE SHEETS PERMISSION ERROR: The Cloud Function doesn't have access to the Google Sheet '{args.get('spreadsheet_id', 'unknown')}'. Please ensure: 1) The service account is shared on the Google Sheet 2) Service account has 'Editor' access 3) Sheet is not 'View Only'"

	# Check for spreadsheet not found errors
	if "not found" in error_str.lower():
		return f"❌ SPREADSHEET NOT FOUND: The Google Sheet '{args.get('spreadsheet_id', 'unknown')}' was not found or is inaccessible. Please verify the spreadsheet_id parameter"

	# Check for database connection errors
	if "connection" in error_str.lower() or "database" in error_str.lower():
		return f"❌ DATABASE CONNECTION ERROR: Cannot connect to the database. Please check the NEON_DATABASE_URL environment variable"

	# Check for SQL errors
	if "sql" in error_str.lower() or "syntax" in error_str.lower():
		sql_preview = f"\n\nSQL Query: {sql[:200]}..." if sql and len(sql) > 200 else f"\n\nSQL Query: {sql}" if sql else ""
		return f"❌ SQL QUERY ERROR: The SQL query in the sheet is invalid. Please check the SQL syntax and ensure it's a SELECT statement only.{sql_preview}\n\nOriginal Error: {exception}"

	# Default error message
	return f"❌ FUNCTION ERROR: {type(exception).__name__}: {exception}"


def _get_error_status_code(exception: Exception) -> int:
	"""Return appropriate HTTP status code based on error type"""
	error_str = str(exception).lower()

	if "authentication" in error_str or "credentials" in error_str:
		return 403  # Forbidden

	if "permission" in error_str or "access" in error_str or "forbidden" in error_str:
		return 403  # Forbidden

	if "not found" in error_str:
		return 404  # Not Found

	if "connection" in error_str or "database" in error_str:
		return 503  # Service Unavailable

	if "sql" in error_str or "syntax" in error_str:
		return 400  # Bad Request

	return 500  # Internal Server Error


@functions_framework.http
def pg_query_output_to_gsheet(request):
	start_time = time.time()
	try:
		args = request.args or {}
		spreadsheet_id = args.get("spreadsheet_id")
		sheet_name = args.get("sheet_name", "Data")
		starting_cell = args.get("starting_cell", "F2")
		timestamp_cell = args.get("timestamp_cell")
		status_cell = args.get("status_cell")
		value_input_option = args.get("value_input_option", "RAW")
		include_headers = (args.get("include_headers", "true").lower() != "false")
		row_limit = int(args.get("row_limit", os.getenv("DEFAULT_ROW_LIMIT", "50000")))
		token = args.get("token")

		if not spreadsheet_id:
			return ("Missing required param: spreadsheet_id", 400)

		# Auth check if configured
		_require_token_if_configured(token)

		# Resolve SQL
		sql_inline = args.get("sql")
		sql_cell = args.get("sql_cell")
		if not sql_inline and not sql_cell:
			return ("One of sql or sql_cell is required", 400)

		sheets_api = _build_sheets_client()

		# Check Google Sheets access before proceeding
		access_error = _check_google_sheets_access(sheets_api, spreadsheet_id)
		if access_error:
			return (access_error, 403)

		if sql_cell:
			query_sql = _read_cell(sheets_api, spreadsheet_id, sql_cell)
		else:
			query_sql = sql_inline or ""

		query_sql = query_sql.strip().rstrip(";")
		if not query_sql:
			return ("SQL is empty", 400)

		if not _is_select_only(query_sql):
			return ("Only a single SELECT statement is allowed", 400)

		# Connect to Neon Postgres and execute query
		database_url = os.getenv("NEON_DATABASE_URL")
		if not database_url:
			return ("NEON_DATABASE_URL is not configured", 500)

		# Try to use JSON unnesting functionality first
		try:
			rows = process_query_with_json_unnesting(query_sql, database_url)
			# Apply row limit to results if needed
			# Check if original SQL already has LIMIT (after stripping template syntax)
			clean_sql = _strip_template_syntax(query_sql)
			has_existing_limit = bool(re.search(r"\bLIMIT\b", clean_sql, flags=re.IGNORECASE))

			if not has_existing_limit and row_limit != float('inf') and len(rows) > row_limit:
				rows = rows[:row_limit]
		except ImportError:
			# Fall back to direct execution if JSON unnesting is not available
			conn = psycopg.connect(database_url, connect_timeout=15, row_factory=dict_row)
			try:
				with conn.cursor() as cur:
					# Safety guardrails
					cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
					cur.execute("SET LOCAL statement_timeout = '60s'")

					cur.execute(query_sql)
					rows = cur.fetchall()
			finally:
				conn.close()

		# Apply row limit to results if needed
		# Check if original SQL already has LIMIT (after stripping template syntax)
		clean_sql = _strip_template_syntax(query_sql)
		has_existing_limit = bool(re.search(r"\bLIMIT\b", clean_sql, flags=re.IGNORECASE))

		if not has_existing_limit and row_limit != float('inf') and len(rows) > row_limit:
			rows = rows[:row_limit]

		values = _to_sheet_values(rows, include_headers=include_headers)

		# Clear and write
		_clear_range(sheets_api, spreadsheet_id, sheet_name, starting_cell)
		if values:
			_write_values(sheets_api, spreadsheet_id, sheet_name, starting_cell, values, value_input_option=value_input_option)

		# Write status cells
		duration_ms = int((time.time() - start_time) * 1000)
		if timestamp_cell:
			_update_cell(sheets_api, spreadsheet_id, timestamp_cell, _iso_now())
		if status_cell:
			_update_cell(sheets_api, spreadsheet_id, status_cell, f"OK: {max(0, len(values) - (1 if include_headers else 0))} rows in {duration_ms} ms")

		return (
			json.dumps({
				"status": "ok",
				"rows": max(0, len(values) - (1 if include_headers else 0)),
				"duration_ms": duration_ms,
			}),
			200,
			{"Content-Type": "application/json"},
		)
	except PermissionError as e:
		return (str(e), 401)
	except Exception as e:
		# Enhanced error handling for Google API and permission issues
		error_message = _get_enhanced_error_message(e, request, query_sql)

		# Best-effort status write on error
		try:
			args = request.args or {}
			spreadsheet_id = args.get("spreadsheet_id")
			status_cell = args.get("status_cell")
			timestamp_cell = args.get("timestamp_cell")
			if spreadsheet_id and (status_cell or timestamp_cell):
				sheets_api = _build_sheets_client()
				if timestamp_cell:
					_update_cell(sheets_api, spreadsheet_id, timestamp_cell, _iso_now())
				if status_cell:
					_update_cell(sheets_api, spreadsheet_id, status_cell, error_message)
		except Exception:
			pass

		# Return appropriate HTTP status code based on error type
		status_code = _get_error_status_code(e)
		return (error_message, status_code)

