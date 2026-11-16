# load.py
# This file loads the cleaned data into PostgreSQL
# We use COPY FROM STDIN which is faster than INSERT for large files
# The prior file is too big to load all at once so we use chunks

import io
import logging
import os
import pathlib
import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass

from src.transform import transform_order_products_chunk
from src.clean import clean_prior_chunk

logger = logging.getLogger(__name__)

ROOT = pathlib.Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"
PROC_DIR = ROOT / "data" / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 500000


def df_to_buffer(df, columns):
    # convert dataframe to csv buffer for COPY command
    buf = io.StringIO()
    df[columns].to_csv(buf, index=False, header=False, na_rep="")
    buf.seek(0)
    return buf


def copy_to_table(cur, df, table, columns):
    # use COPY FROM STDIN to load data fast
    buf = df_to_buffer(df, columns)
    sql = "COPY " + table + " (" + ", ".join(columns) + ") FROM STDIN WITH (FORMAT csv, NULL '');"
    cur.copy_expert(sql, buf)
    return len(df)


def truncate_table(cur, table):
    cur.execute("TRUNCATE TABLE " + table + " CASCADE;")
    logger.info("Truncated table: %s", table)


def drop_constraint(cur, table, constraint):
    cur.execute("ALTER TABLE " + table + " DROP CONSTRAINT IF EXISTS " + constraint + " CASCADE;")


def create_schema(conn):
    from src.database import run_sql_file
    run_sql_file(conn, SQL_DIR / "schema.sql")
    logger.info("Schema created")


def load_aisles(conn, df):
    cols = ["aisle_id", "aisle_name"]
    with conn.cursor() as cur:
        truncate_table(cur, "aisles")
        n = copy_to_table(cur, df, "aisles", cols)
    conn.commit()
    logger.info("Loaded %d rows into aisles", n)
    return n


def load_departments(conn, df):
    cols = ["department_id", "department_name"]
    with conn.cursor() as cur:
        truncate_table(cur, "departments")
        n = copy_to_table(cur, df, "departments", cols)
    conn.commit()
    logger.info("Loaded %d rows into departments", n)
    return n


def load_products(conn, df):
    cols = ["product_id", "product_name", "aisle_id", "department_id", "product_name_length"]
    with conn.cursor() as cur:
        truncate_table(cur, "products")
        n = copy_to_table(cur, df, "products", cols)
    conn.commit()
    logger.info("Loaded %d rows into products", n)
    return n


def load_orders(conn, df):
    cols = ["order_id", "user_id", "eval_set", "order_number",
            "order_dow", "order_hour_of_day", "days_since_prior_order",
            "is_first_order", "order_period"]
    with conn.cursor() as cur:
        truncate_table(cur, "orders")
        n = copy_to_table(cur, df, "orders", cols)
    conn.commit()
    logger.info("Loaded %d rows into orders", n)
    return n


def load_order_products_train(conn, df):
    cols = ["order_id", "product_id", "add_to_cart_order", "reordered", "is_reordered"]
    with conn.cursor() as cur:
        truncate_table(cur, "order_products_train")
        n = copy_to_table(cur, df, "order_products_train", cols)
    conn.commit()
    logger.info("Loaded %d rows into order_products_train", n)
    return n


def load_order_products_prior_chunked(conn, raw_dir, valid_order_ids, valid_product_ids, limit=3000000):
    # load the large prior file in chunks to avoid memory issues
    prior_path = raw_dir / "order_products__prior.csv"
    if not prior_path.exists():
        logger.error("Prior file not found: %s", prior_path)
        return 0

    with conn.cursor() as cur:
        truncate_table(cur, "order_products_prior")
    conn.commit()

    cols = ["order_id", "product_id", "add_to_cart_order", "reordered", "is_reordered"]
    total = 0
    total_read = 0

    logger.info("Loading order_products_prior in chunks... limit=%s",
                "ALL" if limit == 0 else str(limit))

    for i, chunk in enumerate(pd.read_csv(prior_path, chunksize=CHUNK_SIZE), start=1):
        total_read += len(chunk)

        # stop if we reached the row limit
        if limit > 0 and total_read > limit:
            over = total_read - limit
            chunk = chunk.iloc[:len(chunk) - over]

        if len(chunk) == 0:
            break

        # transform and clean each chunk
        chunk = transform_order_products_chunk(chunk, "prior")
        chunk = clean_prior_chunk(chunk, valid_order_ids, valid_product_ids)

        with conn.cursor() as cur:
            n = copy_to_table(cur, chunk, "order_products_prior", cols)
        conn.commit()

        total += n
        logger.info("  chunk %d: %d rows loaded (total: %d)", i, n, total)

        if limit > 0 and total_read >= limit:
            logger.info("Row limit reached (%d)", limit)
            break

    logger.info("order_products_prior done. Total loaded: %d", total)
    return total


def add_constraints(conn):
    # add primary keys, foreign keys and indexes after loading
    # this is faster than having them during the bulk load
    logger.info("Adding primary keys, foreign keys and indexes...")
    try:
        with conn.cursor() as cur:
            # drop old constraints first so we can re-run safely
            drop_constraint(cur, "aisles",               "aisles_pkey")
            drop_constraint(cur, "departments",          "departments_pkey")
            drop_constraint(cur, "products",             "products_pkey")
            drop_constraint(cur, "products",             "fk_products_aisle")
            drop_constraint(cur, "products",             "fk_products_dept")
            drop_constraint(cur, "orders",               "orders_pkey")
            drop_constraint(cur, "order_products_train", "order_products_train_pkey")
            drop_constraint(cur, "order_products_train", "fk_opt_order")
            drop_constraint(cur, "order_products_train", "fk_opt_product")
            drop_constraint(cur, "order_products_prior", "fk_opp_order")
            drop_constraint(cur, "order_products_prior", "fk_opp_product")

            cur.execute("DROP INDEX IF EXISTS idx_products_aisle;")
            cur.execute("DROP INDEX IF EXISTS idx_products_dept;")
            cur.execute("DROP INDEX IF EXISTS idx_orders_user;")
            cur.execute("DROP INDEX IF EXISTS idx_opp_order;")
            cur.execute("DROP INDEX IF EXISTS idx_opp_product;")
            cur.execute("DROP INDEX IF EXISTS idx_opt_order;")

            # primary keys
            cur.execute("ALTER TABLE aisles ADD CONSTRAINT aisles_pkey PRIMARY KEY (aisle_id);")
            cur.execute("ALTER TABLE departments ADD CONSTRAINT departments_pkey PRIMARY KEY (department_id);")
            cur.execute("ALTER TABLE products ADD CONSTRAINT products_pkey PRIMARY KEY (product_id);")
            cur.execute("ALTER TABLE orders ADD CONSTRAINT orders_pkey PRIMARY KEY (order_id);")
            cur.execute("ALTER TABLE order_products_train ADD CONSTRAINT order_products_train_pkey PRIMARY KEY (order_id, product_id);")

            # foreign keys
            cur.execute("ALTER TABLE products ADD CONSTRAINT fk_products_aisle FOREIGN KEY (aisle_id) REFERENCES aisles(aisle_id);")
            cur.execute("ALTER TABLE products ADD CONSTRAINT fk_products_dept FOREIGN KEY (department_id) REFERENCES departments(department_id);")
            cur.execute("ALTER TABLE order_products_train ADD CONSTRAINT fk_opt_order FOREIGN KEY (order_id) REFERENCES orders(order_id);")
            cur.execute("ALTER TABLE order_products_train ADD CONSTRAINT fk_opt_product FOREIGN KEY (product_id) REFERENCES products(product_id);")
            cur.execute("ALTER TABLE order_products_prior ADD CONSTRAINT fk_opp_order FOREIGN KEY (order_id) REFERENCES orders(order_id);")
            cur.execute("ALTER TABLE order_products_prior ADD CONSTRAINT fk_opp_product FOREIGN KEY (product_id) REFERENCES products(product_id);")

            # indexes for faster queries
            cur.execute("CREATE INDEX idx_products_aisle ON products(aisle_id);")
            cur.execute("CREATE INDEX idx_products_dept ON products(department_id);")
            cur.execute("CREATE INDEX idx_orders_user ON orders(user_id);")
            cur.execute("CREATE INDEX idx_opp_order ON order_products_prior(order_id);")
            cur.execute("CREATE INDEX idx_opp_product ON order_products_prior(product_id);")
            cur.execute("CREATE INDEX idx_opt_order ON order_products_train(order_id);")

        conn.commit()
        logger.info("All constraints and indexes added successfully")

    except Exception as e:
        conn.rollback()
        logger.error("Error adding constraints: %s", e)
        raise


def save_processed(cleaned):
    # save cleaned dataframes to csv files in data/processed/
    for name, df in cleaned.items():
        out = PROC_DIR / (name + ".csv")
        df.to_csv(out, index=False)
        logger.info("Saved %s (%d rows)", out.name, len(df))


def load_all(cleaned, raw_dir, prior_rows_limit=3000000):
    from src.database import get_connection
    conn = get_connection()
    counts = {}

    try:
        create_schema(conn)

        counts["aisles"]      = load_aisles(conn, cleaned["aisles"])
        counts["departments"] = load_departments(conn, cleaned["departments"])
        counts["products"]    = load_products(conn, cleaned["products"])
        counts["orders"]      = load_orders(conn, cleaned["orders"])
        counts["order_products_train"] = load_order_products_train(
            conn, cleaned["order_products_train"]
        )

        order_ids   = set(cleaned["orders"]["order_id"].tolist())
        product_ids = set(cleaned["products"]["product_id"].tolist())

        counts["order_products_prior"] = load_order_products_prior_chunked(
            conn, raw_dir, order_ids, product_ids, prior_rows_limit
        )

        add_constraints(conn)

    finally:
        conn.close()

    return counts
