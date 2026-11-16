# verify.py
# This file checks the row counts in the PostgreSQL database
# We use SELECT COUNT(*) to verify that all data was loaded correctly

import logging
import pathlib
import pandas as pd

logger = logging.getLogger(__name__)

REPORTS_DIR = pathlib.Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)
VERIFY_REPORT = REPORTS_DIR / "verification_report.txt"

TABLES = [
    "aisles",
    "departments",
    "products",
    "orders",
    "order_products_train",
    "order_products_prior",
]


def count_table(conn, table):
    # run SELECT COUNT(*) on a table and return the number
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM " + table + ";")
        result = cur.fetchone()
    count = int(result[0]) if result else 0
    logger.info("COUNT(*) FROM %-28s = %d", table, count)
    return count


def verify_all(cleaned, row_counts):
    # connect to the database and verify each table count
    try:
        from src.database import get_connection
        conn = get_connection()
    except Exception as e:
        logger.error("Cannot verify - no database connection: %s", e)
        return {}

    results = {}

    with open(VERIFY_REPORT, "w", encoding="utf-8") as fh:
        fh.write("Instacart Verification Report\n")
        fh.write("=" * 70 + "\n\n")

        header = "  {:<30} {:>10} {:>10} {:>12} {:>10}".format(
            "Table", "Cleaned", "Loaded", "DB COUNT(*)", "Rejected"
        )
        print("\n" + header)
        print("  " + "-" * 70)
        fh.write(header + "\n")
        fh.write("  " + "-" * 70 + "\n")

        for table in TABLES:
            cleaned_rows = len(cleaned.get(table, pd.DataFrame()))
            loaded_rows = row_counts.get(table, 0)

            try:
                db_rows = count_table(conn, table)
            except Exception as e:
                logger.warning("Could not count %s: %s", table, e)
                db_rows = -1

            rejected = max(0, cleaned_rows - loaded_rows)
            results[table] = {
                "cleaned_rows": cleaned_rows,
                "loaded_rows": loaded_rows,
                "db_rows": db_rows,
                "rejected_rows": rejected,
            }

            line = "  {:<30} {:>10,} {:>10,} {:>12,} {:>10,}".format(
                table, cleaned_rows, loaded_rows, db_rows, rejected
            )
            print(line)
            fh.write(line + "\n")

        print()
        fh.write("\n")

        # check if everything matches
        mismatches = [t for t, v in results.items()
                      if v["db_rows"] >= 0 and v["db_rows"] != v["loaded_rows"]]
        if mismatches:
            msg = "WARNING: Mismatch found in: " + ", ".join(mismatches)
            print("  " + msg)
            fh.write("  " + msg + "\n")
        else:
            msg = "[OK] All row counts match the database COUNT(*)"
            print("  " + msg)
            fh.write("  " + msg + "\n")

    conn.close()
    logger.info("Verification report saved to %s", VERIFY_REPORT)
    return results


def run_sql_verify(sql_path=None):
    # run a sql file and print the results
    if sql_path is None:
        sql_path = pathlib.Path("sql") / "verify_counts.sql"

    if not pathlib.Path(sql_path).exists():
        logger.error("SQL file not found: %s", sql_path)
        return

    sql_text = pathlib.Path(sql_path).read_text(encoding="utf-8")

    try:
        from src.database import get_connection
        conn = get_connection()
    except Exception as e:
        logger.error("Cannot run SQL verify: %s", e)
        return

    print("\nRunning:", sql_path)
    print("-" * 50)

    with conn.cursor() as cur:
        for statement in sql_text.split(";"):
            stmt = statement.strip()
            if not stmt:
                continue
            try:
                cur.execute(stmt + ";")
                if cur.description:
                    cols = [d[0] for d in cur.description]
                    rows = cur.fetchall()
                    print("\n  Query:", stmt[:60], "...")
                    print("  Columns:", cols)
                    for row in rows:
                        print("  ", row)
            except Exception as e:
                logger.warning("Statement failed: %s - %s", stmt[:60], e)
                conn.rollback()

    conn.close()
    print("\n" + "-" * 50)
