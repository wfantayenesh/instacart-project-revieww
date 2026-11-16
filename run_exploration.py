# run_exploration.py
# Run this file to explore all the CSV files using pandas
# It shows head(), shape, dtypes, describe(), info(), isnull() and duplicates
# No database connection needed
#
# Usage:
#   python run_exploration.py
#   python run_exploration.py --raw-dir data/raw

import argparse
import logging
import pathlib
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

pathlib.Path("reports").mkdir(exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Explore Instacart CSV files")
    parser.add_argument(
        "--raw-dir",
        default="data/raw",
        help="Path to the folder with CSV files. Default: data/raw"
    )
    args = parser.parse_args()
    raw_dir = pathlib.Path(args.raw_dir)

    if not raw_dir.exists():
        print("Error: folder not found:", raw_dir)
        print("Put the Kaggle CSV files in data/raw/ and try again.")
        sys.exit(1)

    from src.explore import explore_all_files
    dataframes = explore_all_files(raw_dir)

    print("\n[OK] Exploration complete.")
    print("     Loaded", len(dataframes), "DataFrame(s).")
    print("     Report saved to: reports/data_exploration.txt\n")


if __name__ == "__main__":
    main()
