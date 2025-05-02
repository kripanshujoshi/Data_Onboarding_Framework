# Data Onboarding Framework

A Streamlit‑based tool to automate ingestion and configuration of datasets into a data warehouse. This project extracts metadata from sample files, generates system configuration tables and SQL DDL for landing and staging tables, and provides Git integration for version control.

## Features

- Extracts field metadata (data types, lengths, keys) from CSV, Excel, or ZIP archives
- Automatically builds `sys_config_*` dataframes for dataset, pre‑processing, table, and field configurations
- Generates DDL scripts for `land` and `stage` schemas
- Supports pushing SQL artifacts to a Git feature branch and creating PRs via environment credentials
- Inserts configuration entries into PostgreSQL (AWS RDS) using Secrets Manager
- Centralized logging, error handling, and configuration management

## Prerequisites

- Python 3.9+ installed
- Git CLI installed and available in PATH
- AWS credentials in environment or IAM role for Secrets Manager access
- Environment variables:
  - `GIT_USERNAME`, `GIT_TOKEN` (for GitHub push)
  - `LOG_LEVEL` (optional, defaults to `INFO`)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/akashgarje/ingestion-onboarding-automation.git
   cd ingestion-onboarding-automation
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # on Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Edit `configs/config.json` to match your AWS Secrets Manager secret name, region, RDS host, database name, and port.
2. Verify Git settings in `configs/config.json` (repo owner and name).
3. Set environment variables for Git credentials:
   ```bash
   set GIT_USERNAME=<your_username>
   set GIT_TOKEN=<your_token>
   ```
   On PowerShell, use `$env:GIT_USERNAME=...`.

## Usage

Launch the Streamlit app:
```bash
streamlit run app.py
```

1. Enter source, domain, dataset, and table details.
2. Upload a sample file (CSV, Excel, or ZIP containing supported files).
3. Click **Generate Template** to extract metadata and preview configuration tables.
4. Edit entries if needed, then click **Generate SQL Scripts**.
5. Review generated DDL scripts under the SQL tabs.
6. Optionally **Download Files**, **GIT Push**, or **Insert into RDS**.

## Testing

- Activate the virtual environment:
  ```powershell
  venv\Scripts\Activate
  ```
- Lint the code:
  ```powershell
  python -m flake8 .
  ```
- Run unit tests:
  ```powershell
  python -m pytest -q
  ```

## Testing & Troubleshooting

### Running Tests

Activate your virtual environment and run:

```bash
pytest --maxfail=1 --disable-warnings -q
```

### Linting

Check code style with:

```bash
flake8 .
```

### Troubleshooting

- Ensure all required environment variables are set (see above).
- For AWS or GitHub errors, check credentials and permissions.
- For database errors, verify your RDS instance and Secrets Manager config.
- For UI issues, check Streamlit logs and browser console.

## Best Practices

- Use environment variables for all secrets and credentials.
- Keep dependencies up to date (`pip install -U -r requirements.txt`).
- Add unit tests for new modules and functions.
- Use type hints and docstrings for all public functions.
- Clean up temporary files and resources in all scripts.
- Avoid hardcoding values; use config files or environment variables.

## Contributing

1. Fork the repo and create a feature branch.
2. Ensure linting and formatting (e.g., `flake8`, `black`) pass.
3. Add unit tests for new modules and functions.
4. Submit a pull request with clear description.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.