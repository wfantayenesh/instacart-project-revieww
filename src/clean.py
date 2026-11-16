# clean.py
# This file handles data cleaning
# We remove bad rows, duplicates, and rows with invalid values
# Important: we do NOT remove NaN in days_since_prior_order
# because NaN means it is the customer's first order - that is valid data

import io
import logging
import pathlib
import pandas as pd

logger = logging.getLogger(__name__)

REPORTS_DIR = pathlib.Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)
CLEAN_REPORT = REPORTS_DIR / "cleaning_report.txt"


def clean_aisles(df, fh):
    logger.info("Cleaning aisles...")
    before = len(df)
    fh.write("aisles - before: " + str(before) + "\n")

    # remove duplicate aisle_id rows
    df = df.drop_duplicates(subset=["aisle_id"])

    # remove rows where aisle_name is empty
    blank = df["aisle_name"].isna() | (df["aisle_name"].str.strip() == "")
    df = df[~blank]

    after = len(df)
    fh.write("aisles - after: " + str(after) + "\n")
    fh.write("aisles - removed: " + str(before - after) + "\n\n")
    logger.info("aisles cleaned: %d -> %d rows", before, after)
    return df


def clean_departments(df, fh):
    logger.info("Cleaning departments...")
    before = len(df)
    fh.write("departments - before: " + str(before) + "\n")

    df = df.drop_duplicates(subset=["department_id"])
    blank = df["department_name"].isna() | (df["department_name"].str.strip() == "")
    df = df[~blank]

    after = len(df)
    fh.write("departments - after: " + str(after) + "\n")
    fh.write("departments - removed: " + str(before - after) + "\n\n")
    logger.info("departments cleaned: %d -> %d rows", before, after)
    return df


def clean_products(df, valid_aisle_ids, valid_dept_ids, fh):
    logger.info("Cleaning products...")
    before = len(df)
    fh.write("products - before: " + str(before) + "\n")

    # remove duplicate product ids
    df = df.drop_duplicates(subset=["product_id"])

    # remove products with empty name
    blank = df["product_name"].isna() | (df["product_name"].str.strip() == "")
    df = df[~blank]

    # remove products that have an aisle_id not in the aisles table
    if valid_aisle_ids:
        orphan = ~df["aisle_id"].isin(valid_aisle_ids)
        logger.info("products with invalid aisle_id: %d", orphan.sum())
        df = df[~orphan]

    # remove products that have a department_id not in the departments table
    if valid_dept_ids:
        orphan = ~df["department_id"].isin(valid_dept_ids)
        logger.info("products with invalid department_id: %d", orphan.sum())
        df = df[~orphan]

    after = len(df)
    fh.write("products - after: " + str(after) + "\n")
    fh.write("products - removed: " + str(before - after) + "\n\n")
    logger.info("products cleaned: %d -> %d rows", before, after)
    return df


def clean_orders(df, fh):
    logger.info("Cleaning orders...")
    before = len(df)
    fh.write("orders - before: " + str(before) + "\n")

    # show missing values
    fh.write("missing values:\n" + str(df.isnull().sum()) + "\n")
    fh.write("NOTE: days_since_prior_order NaN is valid - means first order\n")

    # remove duplicate order ids
    df = df.drop_duplicates(subset=["order_id"])

    # order_dow must be 0 to 6
    bad_dow = ~df["order_dow"].between(0, 6)
    if bad_dow.sum() > 0:
        logger.warning("Removing %d rows with bad order_dow", bad_dow.sum())
        df = df[~bad_dow]

    # order_hour_of_day must be 0 to 23
    bad_hour = ~df["order_hour_of_day"].between(0, 23)
    if bad_hour.sum() > 0:
        logger.warning("Removing %d rows with bad order_hour_of_day", bad_hour.sum())
        df = df[~bad_hour]

    # days_since_prior_order must be 0 to 30 if not null
    bad_days = df["days_since_prior_order"].notna() & (
        (df["days_since_prior_order"] < 0) | (df["days_since_prior_order"] > 30)
    )
    if bad_days.sum() > 0:
        logger.warning("Removing %d rows with bad days_since_prior_order", bad_days.sum())
        df = df[~bad_days]

    after = len(df)
    fh.write("orders - after: " + str(after) + "\n")
    fh.write("orders - removed: " + str(before - after) + "\n\n")
    logger.info("orders cleaned: %d -> %d rows", before, after)
    return df


def clean_order_products(df, valid_order_ids, valid_product_ids, source_name, fh):
    logger.info("Cleaning order_products [%s]...", source_name)
    before = len(df)
    fh.write(source_name + " - before: " + str(before) + "\n")

    # remove exact duplicates
    df = df.drop_duplicates()

    # remove rows with missing values in required columns
    required = ["order_id", "product_id", "add_to_cart_order", "reordered"]
    null_mask = df[required].isnull().any(axis=1)
    df = df[~null_mask]

    # remove rows where order_id is not in the orders table
    if valid_order_ids:
        orphan_order = ~df["order_id"].isin(valid_order_ids)
        logger.info("[%s] orphan order_id rows: %d", source_name, orphan_order.sum())
        fh.write("orphan order_id: " + str(orphan_order.sum()) + "\n")
        df = df[~orphan_order]

    # remove rows where product_id is not in the products table
    if valid_product_ids:
        orphan_prod = ~df["product_id"].isin(valid_product_ids)
        logger.info("[%s] orphan product_id rows: %d", source_name, orphan_prod.sum())
        fh.write("orphan product_id: " + str(orphan_prod.sum()) + "\n")
        df = df[~orphan_prod]

    # add_to_cart_order must be at least 1
    bad_cart = df["add_to_cart_order"] < 1
    df = df[~bad_cart]

    # reordered must be 0 or 1
    bad_reorder = ~df["reordered"].isin([0, 1])
    df = df[~bad_reorder]

    after = len(df)
    fh.write(source_name + " - after: " + str(after) + "\n")
    fh.write(source_name + " - removed: " + str(before - after) + "\n\n")
    logger.info("[%s] cleaned: %d -> %d rows", source_name, before, after)
    return df


def clean_all(transformed):
    cleaned = {}

    with open(CLEAN_REPORT, "w", encoding="utf-8") as fh:
        fh.write("Instacart Cleaning Report\n")
        fh.write("=" * 50 + "\n\n")

        # clean in order so we can check foreign keys
        if "aisles" in transformed:
            cleaned["aisles"] = clean_aisles(transformed["aisles"], fh)

        if "departments" in transformed:
            cleaned["departments"] = clean_departments(transformed["departments"], fh)

        if "products" in transformed:
            aisle_ids = set(cleaned["aisles"]["aisle_id"].tolist()) if "aisles" in cleaned else set()
            dept_ids = set(cleaned["departments"]["department_id"].tolist()) if "departments" in cleaned else set()
            cleaned["products"] = clean_products(transformed["products"], aisle_ids, dept_ids, fh)

        if "orders" in transformed:
            cleaned["orders"] = clean_orders(transformed["orders"], fh)

        if "order_products_train" in transformed:
            order_ids = set(cleaned["orders"]["order_id"].tolist()) if "orders" in cleaned else set()
            product_ids = set(cleaned["products"]["product_id"].tolist()) if "products" in cleaned else set()
            cleaned["order_products_train"] = clean_order_products(
                transformed["order_products_train"], order_ids, product_ids, "train", fh
            )

        fh.write("Cleaning complete.\n")

    logger.info("Cleaning report saved to %s", CLEAN_REPORT)
    logger.info("clean_all done - %d tables cleaned", len(cleaned))
    return cleaned


def clean_prior_chunk(chunk, valid_order_ids, valid_product_ids):
    # used for cleaning each chunk of the large prior file
    fh = io.StringIO()
    return clean_order_products(chunk, valid_order_ids, valid_product_ids, "prior_chunk", fh)
