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


def _iso_now() -> str:
	return datetime.now(timezone.utc).isoformat()


def _is_select_only(sql: str) -> bool:
	# Basic guardrail: ensure the first statement is a SELECT and no DDL/DML keywords present
	statements = [s for s in sqlparse.parse(sql) if str(s).strip()]
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
	if re.search(r"\bLIMIT\b", sql, flags=re.IGNORECASE):
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
	# Clear a large range starting from starting_cell downwards
	# Using a generous range to ensure prior content is removed
	clear_range = f"{sheet_name}!{starting_cell}:ZZZ1000000"
	sheets_api.spreadsheets().values().clear(
		spreadsheetId=spreadsheet_id,
		range=clear_range,
		body={},
	).execute()


def _write_values(sheets_api, spreadsheet_id: str, sheet_name: str, starting_cell: str, values: typing.List[typing.List[str]], value_input_option: str):
	sheets_api.spreadsheets().values().update(
		spreadsheetId=spreadsheet_id,
		range=f"{sheet_name}!{starting_cell}",
		valueInputOption=value_input_option,
		body={"values": values},
	).execute()


def _require_token_if_configured(token_param: typing.Optional[str]):
	configured = os.getenv("PUBLIC_TRIGGER_TOKEN")
	if configured:
		if not token_param or token_param != configured:
			raise PermissionError("Unauthorized: invalid token")


@functions_framework.http
def pg_query_output_to_gsheet(request):
	start_time = time.time()
	try:
		args = request.args or {}
		spreadsheet_id = args.get("spreadsheet_id")
		sheet_name = args.get("sheet_name", "Data")
		starting_cell = args.get("starting_cell", "A2")
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
		if sql_cell:
			query_sql = _read_cell(sheets_api, spreadsheet_id, sql_cell)
		else:
			query_sql = sql_inline or ""

		query_sql = query_sql.strip().rstrip(";")
		if not query_sql:
			return ("SQL is empty", 400)

		if not _is_select_only(query_sql):
			return ("Only a single SELECT statement is allowed", 400)

		final_sql = _apply_row_limit(query_sql, row_limit)

		# Connect to Neon Postgres
		database_url = os.getenv("NEON_DATABASE_URL")
		if not database_url:
			return ("NEON_DATABASE_URL is not configured", 500)

		conn = psycopg.connect(database_url, connect_timeout=15, row_factory=dict_row)
		try:
			with conn.cursor() as cur:
				# Safety guardrails
				cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
				cur.execute("SET LOCAL statement_timeout = '60s'")

				cur.execute(final_sql)
				rows = cur.fetchall()
		finally:
			conn.close()

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
					_update_cell(sheets_api, spreadsheet_id, status_cell, f"ERROR: {type(e).__name__}: {e}")
		except Exception:
			pass
		return (f"Error: {type(e).__name__}: {e}", 500)

