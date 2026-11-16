# pipeline.py
# This is the main ETL pipeline that runs all steps in order
# Step 1: Extract and Explore
# Step 2: Transform
# Step 3: Clean
# Step 4: Load into PostgreSQL
# Step 5: Verify with COUNT(*)

import logging
import os
import pathlib

try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass

logger = logging.getLogger(__name__)

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROC_DIR = ROOT / "data" / "processed"


def run(raw_dir=RAW_DIR, skip_db=False):
    from src.explore import explore_all_files
    from src.transform import transform_all
    from src.clean import clean_all
    from src.load import load_all, save_processed
    from src.verify import verify_all

    logger.info("=" * 50)
    logger.info("  INSTACART ETL PIPELINE STARTING")
    logger.info("=" * 50)

    # step 1 - read and explore all csv files
    logger.info("[STEP 1/5] Extract and Explore")
    dataframes = explore_all_files(raw_dir)

    if not dataframes:
        logger.error("No CSV files loaded. Put the Kaggle files in %s", raw_dir)
        return

    # step 2 - transform data types and create new columns
    logger.info("[STEP 2/5] Transform")
    transformed = transform_all(dataframes)

    # step 3 - clean data, remove bad rows
    logger.info("[STEP 3/5] Clean")
    cleaned = clean_all(transformed)

    # save cleaned files to data/processed/
    save_processed(cleaned)
    logger.info("Cleaned files saved to %s", PROC_DIR)

    # if skip_db flag is set, stop here without loading to database
    if skip_db:
        logger.info("[SKIP-DB] Stopping after clean step.")
        logger.info("Cleaned CSV files are in data/processed/")
        logger.info("Run without --skip-db on your local PC to load into PostgreSQL")
        print_summary(cleaned, None)
        return

    # step 4 - load data into PostgreSQL
    logger.info("[STEP 4/5] Load into PostgreSQL")
    limit = int(os.environ.get("PRIOR_ROWS_LIMIT", "3000000"))

    try:
        from src.database import create_database_if_missing
        create_database_if_missing()
    except Exception as e:
        logger.error("Could not create database: %s", e)
        logger.error("Create it manually: psql -U postgres -c \"CREATE DATABASE bigdata_db;\"")
        return

    counts = load_all(cleaned=cleaned, raw_dir=raw_dir, prior_rows_limit=limit)

    # step 5 - verify row counts using COUNT(*)
    logger.info("[STEP 5/5] Verify")
    verify_all(cleaned, counts)

    print_summary(cleaned, counts)


def print_summary(cleaned, counts):
    print("\n" + "=" * 50)
    print("  PIPELINE COMPLETE")
    print("=" * 50)
    print("  {:<30} {:>12}".format("Table", "Cleaned rows"))
    print("  " + "-" * 44)
    for name, df in cleaned.items():
        print("  {:<30} {:>12,}".format(name, len(df)))

    if counts:
        print()
        print("  {:<30} {:>12}".format("Table", "DB rows loaded"))
        print("  " + "-" * 44)
        for name, n in counts.items():
            print("  {:<30} {:>12,}".format(name, n))

    print("=" * 50)
    print("  Check reports/ folder for detailed output")
    print("=" * 50 + "\n")
