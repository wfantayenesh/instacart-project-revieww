# database.py
# This file handles the PostgreSQL database connection
# We use psycopg2 to connect to the local PostgreSQL server
# Connection settings are read from the .env file

import logging
import os
import pathlib
import psycopg2

try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass

logger = logging.getLogger(__name__)


def get_db_params():
    # read connection settings from environment variables
    password = os.environ.get("DB_PASSWORD", "")
    if not password:
        raise EnvironmentError(
            "DB_PASSWORD is not set. Please copy .env.example to .env and set your password."
        )
    return {
        "host":     os.environ.get("DB_HOST", "localhost"),
        "port":     int(os.environ.get("DB_PORT", "5432")),
        "dbname":   os.environ.get("DB_NAME", "bigdata_db"),
        "user":     os.environ.get("DB_USER", "postgres"),
        "password": password,
    }


def create_database_if_missing():
    # connect to the default postgres database and create bigdata_db if it does not exist
    params = get_db_params()
    target = params["dbname"]

    # connect to postgres maintenance database first
    conn_params = {**params, "dbname": "postgres"}

    try:
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True  # needed for CREATE DATABASE
        cur = conn.cursor()

        # check if the database already exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (target,))
        exists = cur.fetchone() is not None

        if not exists:
            cur.execute('CREATE DATABASE "' + target + '";')
            logger.info("Database %s created", target)
        else:
            logger.info("Database %s already exists", target)

        cur.close()
        conn.close()

    except psycopg2.OperationalError as e:
        logger.error("Could not connect to PostgreSQL: %s", e)
        logger.error("Make sure PostgreSQL is running on %s:%s", params["host"], params["port"])
        logger.error("You can also create the database manually in pgAdmin")
        raise


def get_connection():
    # open a connection to bigdata_db
    params = get_db_params()
    try:
        conn = psycopg2.connect(**params)
        logger.info("Connected to PostgreSQL - host=%s db=%s", params["host"], params["dbname"])
        return conn
    except psycopg2.OperationalError as e:
        logger.error("Cannot connect to bigdata_db: %s", e)
        logger.error("Check that PostgreSQL is running and .env settings are correct")
        raise


def run_sql_file(conn, sql_path):
    # read and run a sql file
    sql_text = pathlib.Path(sql_path).read_text(encoding="utf-8")
    try:
        with conn.cursor() as cur:
            cur.execute(sql_text)
        conn.commit()
        logger.info("SQL file executed: %s", pathlib.Path(sql_path).name)
    except Exception as e:
        conn.rollback()
        logger.error("Error running SQL file %s: %s", sql_path, e)
        raise


def test_connection():
    # quick test to check if the database connection works
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
        conn.close()
        print("\n[OK] PostgreSQL connection successful")
        print("    ", version, "\n")
        return True
    except Exception as e:
        print("\n[FAIL] PostgreSQL connection failed")
        print("    ", e, "\n")
        return False
