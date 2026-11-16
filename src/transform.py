# transform.py
# This file cleans up the data types and creates new useful columns
# We convert columns to smaller data types to save memory

import logging
import pandas as pd

logger = logging.getLogger(__name__)


def transform_aisles(df):
    logger.info("Transforming aisles (%d rows)", len(df))
    df = df.copy()

    # convert aisle_id to int32 to save memory
    df["aisle_id"] = df["aisle_id"].astype("int32")

    # remove extra spaces from text
    df["aisle"] = df["aisle"].str.strip()

    # rename column to be more clear
    df = df.rename(columns={"aisle": "aisle_name"})

    logger.info("transform_aisles done")
    return df


def transform_departments(df):
    logger.info("Transforming departments (%d rows)", len(df))
    df = df.copy()

    df["department_id"] = df["department_id"].astype("int32")
    df["department"] = df["department"].str.strip()
    df = df.rename(columns={"department": "department_name"})

    logger.info("transform_departments done")
    return df


def transform_products(df):
    logger.info("Transforming products (%d rows)", len(df))
    df = df.copy()

    # convert id columns to int32
    df["product_id"] = df["product_id"].astype("int32")
    df["aisle_id"] = df["aisle_id"].astype("int32")
    df["department_id"] = df["department_id"].astype("int32")

    # remove extra spaces from product names
    df["product_name"] = df["product_name"].str.strip()

    # create a new column with the length of the product name
    df["product_name_length"] = df["product_name"].str.len()

    # create uppercase version for easier searching
    df["product_name_upper"] = df["product_name"].str.upper()

    logger.info("Added new columns: product_name_length, product_name_upper")
    logger.info("transform_products done")
    return df


def transform_orders(df):
    logger.info("Transforming orders (%d rows)", len(df))
    df = df.copy()

    # convert id columns
    df["order_id"] = df["order_id"].astype("int32")
    df["user_id"] = df["user_id"].astype("int32")
    df["order_number"] = df["order_number"].astype("int16")
    df["order_dow"] = df["order_dow"].astype("int8")
    df["order_hour_of_day"] = df["order_hour_of_day"].astype("int8")

    # keep as float32 because NaN means it is the customer first order
    df["days_since_prior_order"] = df["days_since_prior_order"].astype("float32")

    # create new column: True if this is the customer first order
    df["is_first_order"] = df["days_since_prior_order"].isna()
    logger.info("First orders found: %d", df["is_first_order"].sum())

    # create new column: time of day when order was placed
    def get_period(hour):
        if 5 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 17:
            return "Afternoon"
        elif 17 <= hour < 21:
            return "Evening"
        else:
            return "Night"

    df["order_period"] = df["order_hour_of_day"].apply(get_period)
    logger.info("Order periods: %s", df["order_period"].value_counts().to_dict())

    logger.info("transform_orders done")
    return df


def transform_order_products(df, source_name):
    logger.info("Transforming order_products [%s] (%d rows)", source_name, len(df))
    df = df.copy()

    df["order_id"] = df["order_id"].astype("int32")
    df["product_id"] = df["product_id"].astype("int32")
    df["add_to_cart_order"] = df["add_to_cart_order"].astype("int16")
    df["reordered"] = df["reordered"].astype("int8")

    # new column: True if the item was reordered
    df["is_reordered"] = df["reordered"] == 1
    pct = df["is_reordered"].mean() * 100
    logger.info("Reorder rate: %.1f%%", pct)

    logger.info("transform_order_products [%s] done", source_name)
    return df


def transform_all(dataframes):
    # apply the right transform function to each table
    result = {}

    if "aisles" in dataframes:
        result["aisles"] = transform_aisles(dataframes["aisles"])

    if "departments" in dataframes:
        result["departments"] = transform_departments(dataframes["departments"])

    if "products" in dataframes:
        result["products"] = transform_products(dataframes["products"])

    if "orders" in dataframes:
        result["orders"] = transform_orders(dataframes["orders"])

    if "order_products_train" in dataframes:
        result["order_products_train"] = transform_order_products(
            dataframes["order_products_train"], "train"
        )

    logger.info("transform_all done - %d tables transformed", len(result))
    return result


def transform_order_products_chunk(chunk, source_name):
    # used when loading the large prior file in chunks
    return transform_order_products(chunk, source_name)
