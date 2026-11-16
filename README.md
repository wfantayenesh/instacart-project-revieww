# Instacart Big Data ETL Pipeline
### Using Python Pandas and PostgreSQL

---

## Business Problem

> **"When do customers order and how often do they return?"**

The Instacart Market Basket Analysis dataset contains over 3 million grocery orders
from more than 200,000 users. This project builds a complete ETL pipeline that:

1. **Extracts** six raw CSV files (including a 32-million-row fact table)
2. **Explores** every file using pandas and saves a full exploration report
3. **Transforms** data types, standardises columns, and creates derived columns
4. **Cleans** missing values, duplicates, and invalid records safely
5. **Loads** cleaned data into a local PostgreSQL database (`bigdata_db`)
6. **Verifies** every table using `SELECT COUNT(*)`
7. **Reports** charts and analytics answering the business question

---

## Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    AISLES {
        smallint aisle_id PK
        varchar  aisle_name
    }
    DEPARTMENTS {
        smallint department_id PK
        varchar  department_name
    }
    PRODUCTS {
        integer  product_id PK
        varchar  product_name
        smallint aisle_id FK
        smallint department_id FK
        smallint product_name_length
    }
    ORDERS {
        integer  order_id PK
        integer  user_id
        varchar  eval_set
        smallint order_number
        smallint order_dow
        smallint order_hour_of_day
        real     days_since_prior_order
        boolean  is_first_order
        varchar  order_period
    }
    ORDER_PRODUCTS_TRAIN {
        integer  order_id PK FK
        integer  product_id PK FK
        smallint add_to_cart_order
        smallint reordered
        boolean  is_reordered
    }
    ORDER_PRODUCTS_PRIOR {
        integer  order_id FK
        integer  product_id FK
        smallint add_to_cart_order
        smallint reordered
        boolean  is_reordered
    }

    AISLES       ||--o{ PRODUCTS              : "has"
    DEPARTMENTS  ||--o{ PRODUCTS              : "contains"
    ORDERS       ||--o{ ORDER_PRODUCTS_TRAIN  : "includes"
    PRODUCTS     ||--o{ ORDER_PRODUCTS_TRAIN  : "appears in"
    ORDERS       ||--o{ ORDER_PRODUCTS_PRIOR  : "includes"
    PRODUCTS     ||--o{ ORDER_PRODUCTS_PRIOR  : "appears in"
```

---

## Project Structure

```
instacart-bigdata-etl/
│
├── data/
│   ├── raw/            ← Place the 6 Kaggle CSV files here
│   ├── processed/      ← Cleaned CSVs saved here by the pipeline
│   └── sample/         ← Tiny fake CSVs for testing (auto-generated)
│
├── src/
│   ├── __init__.py
│   ├── explore.py      ← Pandas exploration (all 9 required methods)
│   ├── transform.py    ← Type conversions and derived columns
│   ├── clean.py        ← Missing values, duplicates, orphan FKs
│   ├── database.py     ← psycopg2 connection, DB creation
│   ├── load.py         ← COPY FROM STDIN bulk load, constraints
│   ├── pipeline.py     ← Orchestrator (Steps 1-5)
│   ├── verify.py       ← COUNT(*) verification
│   └── charts.py       ← 3 PNG charts (matplotlib Agg)
│
├── sql/
│   ├── schema.sql          ← CREATE TABLE statements
│   ├── verify_counts.sql   ← SELECT COUNT(*) for all tables
│   └── analytics.sql       ← 9 business analytics queries
│
├── tests/
│   ├── __init__.py
│   ├── test_transform.py   ← 20 unit tests for transform.py
│   └── test_clean.py       ← 20 unit tests for clean.py
│
├── notebooks/
│   └── exploration.ipynb   ← Jupyter notebook (all 9 pandas methods)
│
├── reports/                ← Generated reports and PNG charts
│
├── run_pipeline.py         ← MAIN ENTRY POINT
├── run_exploration.py      ← Exploration only (no DB)
├── run_verification.py     ← DB COUNT(*) verification
├── run_charts.py           ← Generate PNG charts
├── make_sample_data.py     ← Create tiny fake CSVs for testing
│
├── .env.example            ← Copy this to .env and add your password
├── .gitignore
├── requirements.txt
├── setup_windows.ps1       ← Automated Windows setup script
├── README.md               ← This file
└── REPORT_TEMPLATE.md      ← Fill-in report template
```

---

## Quick Start (Windows + VS Code)

### Prerequisites
- Windows 10 / 11
- Python 3.11 (from python.org — check "Add to PATH")
- PostgreSQL installed locally (from postgresql.org)
- VS Code with the Python extension

---

## Step-by-Step Windows Setup

### Step 1 — Download and extract the project

1. Download `instacart-bigdata-etl.zip`
2. Right-click → **Extract All** → choose a folder (e.g. `C:\Projects\`)
3. You should now have a folder: `C:\Projects\instacart-bigdata-etl\`

### Step 2 — Open the project in VS Code

1. Open VS Code
2. **File → Open Folder** → select `instacart-bigdata-etl`
3. Open a terminal: **Terminal → New Terminal** (opens PowerShell)

### Step 3 — Allow PowerShell scripts (one-time per session)

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

> This only applies to the current PowerShell window. It does not change system settings.

### Step 4 — Run the automated setup script

```powershell
.\setup_windows.ps1
```

This script:
- Checks your Python version
- Creates a virtual environment (`venv/`)
- Installs all packages from `requirements.txt`
- Copies `.env.example` → `.env`
- Verifies imports work

### Step 5 — Configure your database credentials

Open `.env` in VS Code and replace the placeholder:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bigdata_db
DB_USER=postgres
DB_PASSWORD=replace_with_your_local_password   ← change this
PRIOR_ROWS_LIMIT=3000000
```

> `PRIOR_ROWS_LIMIT=3000000` loads the first 3 million rows of the 32-million-row
> prior-order file. Set to `0` to load all rows (needs ~10 GB RAM).

### Step 6 — Create the bigdata_db database

**Option A — using psql (command line):**
```powershell
psql -U postgres -c "CREATE DATABASE bigdata_db;"
```

**Option B — using pgAdmin:**
1. Open pgAdmin
2. Connect to your local server
3. Right-click **Databases** → **Create** → **Database**
4. Name: `bigdata_db` → **Save**

### Step 7 — Download the Kaggle dataset

1. Go to: https://www.kaggle.com/competitions/instacart-market-basket-analysis/data
2. Sign in to Kaggle (free account required)
3. Click **Download All** → saves `instacart-market-basket-analysis.zip`
4. Extract the ZIP
5. Copy these 6 files into `data\raw\`:

```
data\raw\aisles.csv
data\raw\departments.csv
data\raw\products.csv
data\raw\orders.csv
data\raw\order_products__train.csv
data\raw\order_products__prior.csv
```

> Note the double underscore in `order_products__prior.csv` and `order_products__train.csv`

### Step 8 — Activate the virtual environment

```powershell
.\venv\Scripts\Activate.ps1
```

You should see `(venv)` at the start of your prompt.

### Step 9 — Test with sample data first (no Kaggle files needed)

```powershell
python make_sample_data.py
python run_pipeline.py --raw-dir data/sample --skip-db
```

Expected output: pipeline runs, cleans 6 tiny sample files, saves to `data/processed/`.

### Step 10 — Run exploration on real data

```powershell
python run_exploration.py
```

Output saved to `reports/data_exploration.txt`

### Step 11 — Run the full ETL pipeline

```powershell
python run_pipeline.py
```

This runs all 5 steps:
1. Extract + Explore → `reports/data_exploration.txt`
2. Transform (type conversions, derived columns)
3. Clean (removes invalid rows, keeps legitimate NaNs)
4. Load into PostgreSQL `bigdata_db` via `COPY FROM STDIN`
5. Verify with `SELECT COUNT(*)` → `reports/verification_report.txt`

### Step 12 — Verify database counts

```powershell
python run_verification.py
python run_verification.py --analytics
```

### Step 13 — Generate charts

```powershell
python run_charts.py
```

Saves to `reports/`:
- `chart_orders_per_dow.png`
- `chart_orders_per_hour.png`
- `chart_days_since_prior.png`

### Step 14 — Run unit tests

```powershell
python -m unittest discover -s tests -v
```

Expected: all tests pass. No database or Kaggle files needed for tests.

### Step 15 — Open the Jupyter notebook

```powershell
jupyter notebook notebooks/exploration.ipynb
```

---

## Running the Pipeline — All Commands Reference

```powershell
# Test PostgreSQL connection
python run_pipeline.py --test-connection

# Run on sample data (no DB, no Kaggle files)
python run_pipeline.py --raw-dir data/sample --skip-db

# Run explore + clean only (no DB)
python run_pipeline.py --skip-db

# Run the full pipeline (requires PostgreSQL + Kaggle data)
python run_pipeline.py

# Run exploration only
python run_exploration.py

# Run verification only (after pipeline has loaded data)
python run_verification.py
python run_verification.py --analytics

# Generate charts
python run_charts.py

# Run tests
python -m unittest discover -s tests -v

# Compile-check all source files
python -m compileall src
```

---

## Teacher Requirement → File and Function Mapping

| # | Requirement | File | Function / Line |
|---|-------------|------|-----------------|
| 1 | `pd.read_csv()` | `src/explore.py` | `_explore_small_file()` line ~56; `_explore_large_file_chunked()` line ~100 |
| 2 | `df.head()` | `src/explore.py` | `_explore_small_file()` — `df.head(5)` |
| 3 | `df.columns` | `src/explore.py` | `_explore_small_file()` — `df.columns.tolist()` |
| 4 | `df.describe()` | `src/explore.py` | `_explore_small_file()` — `df.describe(include="all")` |
| 5 | `df.info()` | `src/explore.py` | `_explore_small_file()` — `df.info(buf=buf2)` |
| 6 | `df.shape` | `src/explore.py` | `_explore_small_file()` — `rows, cols = df.shape` |
| 7 | `df.dtypes` | `src/explore.py` | `_explore_small_file()` — `df.dtypes.to_string(buf)` |
| 8 | `df.isnull().sum()` | `src/explore.py` | `_explore_small_file()` — `df.isnull().sum()` |
| 9 | Duplicate detection | `src/explore.py` | `_explore_small_file()` — `df.duplicated().sum()` |
| 10 | Python `for` loop over CSVs | `src/explore.py` | `explore_all_files()` — `for name, (path, is_large) in csv_files.items()` |
| 11 | `chunksize=` for large files | `src/explore.py` | `_explore_large_file_chunked()` — `pd.read_csv(path, chunksize=CHUNK_SIZE)` |
| 12 | Transform data types | `src/transform.py` | `transform_orders()`, `transform_products()`, etc. |
| 13 | Create derived columns | `src/transform.py` | `is_first_order`, `order_period`, `product_name_length`, `is_reordered` |
| 14 | Clean missing values | `src/clean.py` | `clean_orders()` — preserves NaN for first orders |
| 15 | Load into PostgreSQL `bigdata_db` | `src/load.py` | `load_all()` + `_copy_df()` using `cursor.copy_expert()` |
| 16 | `SELECT COUNT(*)` verification | `src/verify.py` | `count_table()` + `sql/verify_counts.sql` |
| 17 | SQL schema | `sql/schema.sql` | All 6 `CREATE TABLE IF NOT EXISTS` statements |

---

## Troubleshooting

### `psycopg2.OperationalError: could not connect to server`
- Make sure PostgreSQL service is running:
  ```powershell
  Get-Service -Name postgresql*
  # If stopped:
  Start-Service -Name postgresql-x64-15  # adjust version number
  ```
- Check `.env` credentials match your PostgreSQL installation
- Try connecting manually: `psql -U postgres`

### `ModuleNotFoundError: No module named 'pandas'`
- Make sure the virtual environment is activated: `.\venv\Scripts\Activate.ps1`
- Reinstall: `pip install -r requirements.txt`

### `FileNotFoundError: data/raw/orders.csv`
- The Kaggle CSV files must be placed manually in `data/raw/`
- See Step 7 above for download instructions

### `password authentication failed for user "postgres"`
- Open `.env` and correct your `DB_PASSWORD`
- If you forgot your PostgreSQL password, reset it via pgAdmin

### Pipeline runs slowly on the prior file
- Reduce `PRIOR_ROWS_LIMIT` in `.env` (e.g. `500000`)
- Or test with sample data: `python run_pipeline.py --raw-dir data/sample --skip-db`

### PowerShell says "execution of scripts is disabled"
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

---

## Important Notes

- **Never commit `.env`** — it contains your database password
- **Never overwrite `data/raw/`** — the pipeline only reads from it
- **The prior-order file is ~550 MB** — it is always read in chunks
- **Re-running the pipeline is safe** — each table is TRUNCATEd before reload
- **`days_since_prior_order` NaN values are legitimate** — they represent first orders and are preserved throughout

---

## Data Source

Kaggle Instacart Market Basket Analysis:
https://www.kaggle.com/competitions/instacart-market-basket-analysis/data
