# run_verification.py
# Run this file after the pipeline to check that all data loaded correctly
# It runs SELECT COUNT(*) on all tables and compares with expected counts
#
# Usage:
#   python run_verification.py
#   python run_verification.py --analytics   (also run analytics queries)

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
    parser = argparse.ArgumentParser(description="Verify database row counts")
    parser.add_argument(
        "--analytics",
        action="store_true",
        help="Also run the analytics SQL queries"
    )
    args = parser.parse_args()

    from src.database import test_connection
    if not test_connection():
        print("Cannot connect to PostgreSQL.")
        print("Check that PostgreSQL is running and .env settings are correct.")
        sys.exit(1)

    from src.verify import run_sql_verify, count_table
    from src.database import get_connection

    # run verify_counts.sql
    print("\n" + "=" * 50)
    print("  Running sql/verify_counts.sql")
    print("=" * 50)
    run_sql_verify(pathlib.Path("sql") / "verify_counts.sql")

    # show direct COUNT(*) for each table
    print("\n" + "=" * 50)
    print("  Direct COUNT(*) per table")
    print("=" * 50)
    tables = [
        "aisles", "departments", "products", "orders",
        "order_products_train", "order_products_prior",
    ]
    conn = get_connection()
    print("\n  {:<30} {:>12}".format("Table", "COUNT(*)"))
    print("  " + "-" * 44)
    for table in tables:
        try:
            n = count_table(conn, table)
            print("  {:<30} {:>12,}".format(table, n))
        except Exception as e:
            print("  {:<30}  ERROR: {}".format(table, e))
    conn.close()

    # run analytics if requested
    if args.analytics:
        print("\n" + "=" * 50)
        print("  Running sql/analytics.sql")
        print("=" * 50)
        run_sql_verify(pathlib.Path("sql") / "analytics.sql")

    print("\n[OK] Verification complete. See reports/verification_report.txt\n")


if __name__ == "__main__":
    main()
