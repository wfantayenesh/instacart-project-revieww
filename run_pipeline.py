# run_pipeline.py
# Main entry point for the ETL pipeline
# Run this file to execute the full pipeline:
#   python run_pipeline.py
#
# Options:
#   --skip-db       run only explore + transform + clean (no database needed)
#   --raw-dir PATH  use a different folder for the CSV files
#   --test-connection  test the PostgreSQL connection and exit

import argparse
import logging
import pathlib
import sys

# make sure reports folder exists before writing the log file
pathlib.Path("reports").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("reports/pipeline.log", mode="w", encoding="utf-8"),
    ],
)


def main():
    parser = argparse.ArgumentParser(description="Instacart ETL Pipeline")
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Run explore + transform + clean only. Do not load into PostgreSQL."
    )
    parser.add_argument(
        "--raw-dir",
        default="data/raw",
        help="Path to the folder with raw CSV files. Default: data/raw"
    )
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test the PostgreSQL connection and exit."
    )
    args = parser.parse_args()

    # just test the connection and exit
    if args.test_connection:
        from src.database import test_connection
        ok = test_connection()
        sys.exit(0 if ok else 1)

    raw_dir = pathlib.Path(args.raw_dir)

    # check that the raw data folder exists
    if not raw_dir.exists():
        print("Error: folder not found:", raw_dir)
        print("Please put the Kaggle CSV files in data/raw/ and try again.")
        sys.exit(1)

    from src.pipeline import run
    run(raw_dir=raw_dir, skip_db=args.skip_db)


if __name__ == "__main__":
    main()
