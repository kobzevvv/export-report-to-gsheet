# 🚀 Export Report to Google Sheets

A powerful bidirectional data synchronization system between **Neon Postgres** and **Google Sheets** using Google Cloud Functions. This project provides HTTP endpoints for seamless data export and import operations with advanced JSON unnesting capabilities.

## 🌟 Features

### 📤 Export Function (`pg_query_output_to_gsheet`)
- Execute SQL queries against Neon Postgres and export results to Google Sheets
- **Advanced JSON Unnesting**: Automatically flatten JSON/JSONB columns into separate columns
- Real-time data synchronization with configurable row limits
- Automatic timestamp and status tracking
- Support for complex queries with JOINs, WHERE clauses, and aggregations

### 📥 Import Function (`gsheet_to_database`)
- Import data from Google Sheets into Neon Postgres
- **Append-only architecture** for maximum reliability and audit trails
- Flexible column mapping and renaming
- Automatic schema and table creation
- Support for large datasets with batch processing

### 🔧 JSON Unnesting Magic
Transform complex JSON structures into flat, spreadsheet-friendly columns:

```sql
-- Before: Complex JSON array
SELECT * FROM candidates WHERE position_name ILIKE '%flutter%'

-- After: Flattened columns with JSON unnesting
SELECT *,
       {{all_fields_as_columns_from(answers_json, question_title, value_text)}}
FROM candidates WHERE position_name ILIKE '%flutter%'
```

**Result**: Creates columns like `answers_json_question_title_1`, `answers_json_value_text_1`, etc.

## 🏗️ Architecture

```
┌─────────────────┐    HTTP    ┌──────────────────┐    SQL    ┌─────────────────┐
│   Google Sheets │ ◄───────── │  Cloud Functions │ ────────► │  Neon Postgres  │
│                 │            │                  │           │                 │
│ • Export Data   │            │ • JSON Unnesting │           │ • Read/Write    │
│ • Import Data   │            │ • Data Validation│           │ • Complex Queries│
│ • Status Cells  │            │ • Error Handling │           │ • JSON Support  │
└─────────────────┘            └──────────────────┘           └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Google Cloud Project with APIs enabled
- Neon Postgres database
- Google Sheets API access
- Service account with proper permissions

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/your-username/export-report-to-gsheet.git
cd export-report-to-gsheet

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env.example .env
```

### 2. Google Cloud Configuration

```bash
# Set up Google Cloud authentication
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"

# Configure environment variables
export NEON_DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
```

### 3. Deploy Cloud Functions

```bash
# Deploy via GitHub Actions (recommended)
# 1. Add secrets to GitHub repository:
#    - GBQ_CREDS_JSON: Service account JSON
#    - NEON_DATABASE_URL: Database connection string
#    - GCP_PROJECT_ID: Your GCP project ID

# 2. Push to main branch or trigger workflow manually
git push origin main
```

### 4. Set Up Google Sheets

Create a spreadsheet with this structure:

| A1 (Function URL) | B1 (SQL Query) | C1 (Timestamp) | D1 (Status) |
|-------------------|----------------|----------------|-------------|
| `https://your-function-url.run.app` | `SELECT * FROM users WHERE active = true` | `(auto)` | `(auto)` |

Add this formula to create a run button:
```excel
=HYPERLINK(
  A1 & "?spreadsheet_id=" & ENCODEURL(REGEXEXTRACT(TO_TEXT(SPREADSHEET_URL()), "/d/([^/]+)"))
  & "&sheet_name=" & ENCODEURL("Data")
  & "&starting_cell=" & ENCODEURL("A2")
  & "&sql_cell=" & ENCODEURL("Config!B1")
  & "&timestamp_cell=" & ENCODEURL("Config!C1")
  & "&status_cell=" & ENCODEURL("Config!D1"),
  "🚀 Run Export"
)
```

## 📖 Usage Examples

### Basic Export
```bash
curl "https://your-function-url.run.app?spreadsheet_id=YOUR_SHEET_ID&sql=SELECT * FROM users&sheet_name=Users"
```

### Advanced Export with JSON Unnesting
```bash
curl "https://your-function-url.run.app?spreadsheet_id=YOUR_SHEET_ID&sql=SELECT *, {{all_fields_as_columns_from(survey_data, question, answer)}} FROM candidates WHERE status = 'active'&sheet_name=Candidates"
```

### Import from Sheets to Database
```bash
curl "https://your-import-function-url.run.app?spreadsheet_id=YOUR_SHEET_ID&sheet_name=Updates&id_field=user_email&export_fields=status,notes&target_schema=imports&target_table=user_updates"
```

## 🔧 JSON Unnesting Examples

### Survey Data Flattening
```sql
-- Original complex JSON
{
  "survey_responses": [
    {"question": "Experience Level", "answer": "5+ years"},
    {"question": "Skills", "answer": "Python, SQL, JavaScript"}
  ]
}

-- Flattened result
| id | name | survey_responses_question_1 | survey_responses_answer_1 | survey_responses_question_2 | survey_responses_answer_2 |
|----|------|------------------------------|---------------------------|------------------------------|---------------------------|
| 1  | John | Experience Level            | 5+ years                 | Skills                       | Python, SQL, JavaScript  |
```

### Flexible JSON Structure Support
The system automatically handles various JSON formats:
- **Arrays**: `[{"key": "value"}, {"key": "value2"}]`
- **Objects**: `{"key": "value", "key2": "value2"}`
- **Nested structures**: `{"list": [{"field": "data"}]}`

## 🛠️ Development

### Local Testing
```bash
# Run tests
python -m pytest tests/

# Test JSON unnesting functionality
python test_json_unnesting.py

# Test integration
python test_integration_example.py
```

### Project Structure
```
├── cloud_function/                 # Export function (Postgres → Sheets)
├── cloud_function_gsheet_to_database/  # Import function (Sheets → Postgres)
├── json_extraction/               # JSON unnesting strategies
├── tests/                         # Comprehensive test suite
├── docs/                          # Documentation
└── scripts/                       # Deployment and utility scripts
```

### JSON Unnesting Strategies
The system uses a strategy pattern for different JSON structures:
- **Direct Field Strategy**: Simple key-value pairs
- **Nested List Strategy**: Arrays with nested objects
- **Flexible Array Strategy**: Dynamic array structures
- **Wildcard Search Strategy**: Pattern-based field discovery

## 🔒 Security

- **IAM Protection**: Functions are protected by Google Cloud IAM
- **Read-Only Queries**: Only SELECT statements are allowed
- **Input Validation**: Comprehensive SQL injection protection
- **Service Account**: Least-privilege access model
- **Secret Management**: Database credentials stored securely

## 📊 Monitoring & Troubleshooting

### Status Tracking
Functions automatically update status cells in your spreadsheet:
- **Timestamp**: Last execution time
- **Status**: Success/failure with row count
- **Error Messages**: Detailed error information

### Common Issues

| Issue | Solution |
|-------|----------|
| 403 Forbidden | Grant `roles/run.invoker` to your user |
| Empty Results | Check SQL syntax and database connectivity |
| Permission Denied | Share spreadsheet with service account |
| JSON Parsing Error | Verify JSON structure matches expected format |

### Debugging Tools
```bash
# Check deployment status
python check_deployment_status.py

# Validate JSON structure
python check_json_structure.py

# Test specific patterns
python test_pattern_matching.py
```

## 🚀 Deployment

### GitHub Actions (Recommended)
The project includes automated CI/CD with GitHub Actions:
- Automatic deployment on push to main
- Environment variable management
- Secret handling via GitHub Secrets
- Rollback capabilities

### Manual Deployment
```bash
# Deploy export function
gcloud functions deploy pg_query_output_to_gsheet \
  --runtime python311 \
  --trigger-http \
  --source cloud_function/ \
  --entry-point pg_query_output_to_gsheet

# Deploy import function  
gcloud functions deploy gsheet_to_database \
  --runtime python311 \
  --trigger-http \
  --source cloud_function_gsheet_to_database/ \
  --entry-point gsheet_to_database
```

## 📈 Performance

- **Export**: ~1000 rows/second for typical queries
- **Import**: ~500 rows/second with JSON processing
- **JSON Unnesting**: ~2.8x overhead (acceptable for functionality)
- **Memory**: Optimized for large datasets with batching

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Run tests: `python -m pytest tests/`
4. Commit changes: `git commit -m 'Add amazing feature'`
5. Push to branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add tests for new functionality
- Update documentation for API changes
- Use type hints for better code clarity

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `docs/` directory for detailed guides
- **Issues**: Report bugs and request features via GitHub Issues
- **Examples**: See `test_*.py` files for usage examples
- **Live Demo**: Use the test Google Sheet for hands-on testing

## 🔗 Related Projects

- [Neon Postgres](https://neon.tech/) - Serverless PostgreSQL
- [Google Sheets API](https://developers.google.com/sheets/api) - Official Google Sheets API
- [Cloud Functions](https://cloud.google.com/functions) - Serverless compute platform

---

**Made with ❤️ for seamless data synchronization between Postgres and Google Sheets**
