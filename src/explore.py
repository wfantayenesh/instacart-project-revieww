import io
import logging
import pathlib
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

REPORTS_DIR = pathlib.Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)
REPORT_FILE = REPORTS_DIR / "data_exploration.txt"
CHUNK_SIZE = 500000


def explore_small_file(name, path, fh):
    logger.info("Reading %s with pd.read_csv() ...", name)
    df = pd.read_csv(path)

    print("=" * 60)
    print("FILE:", name)
    print("=" * 60)
    fh.write("FILE: " + name + "\n")

    print("shape:", df.shape)
    fh.write("shape: " + str(df.shape) + "\n")

    print("columns:", df.columns.tolist())
    fh.write("columns: " + str(df.columns.tolist()) + "\n")

    print("\ndtypes:")
    print(df.dtypes)
    fh.write("\ndtypes:\n" + str(df.dtypes) + "\n")

    print("\nhead(5):")
    print(df.head(5))
    fh.write("\nhead(5):\n" + df.head(5).to_string() + "\n")

    print("\ndescribe():")
    print(df.describe(include="all"))
    fh.write("\ndescribe():\n" + df.describe(include="all").to_string() + "\n")

    print("\ninfo():")
    buf = io.StringIO()
    df.info(buf=buf)
    print(buf.getvalue())
    fh.write("\ninfo():\n" + buf.getvalue() + "\n")

    print("\nisnull().sum():")
    print(df.isnull().sum())
    fh.write("\nisnull().sum():\n" + str(df.isnull().sum()) + "\n")

    dups = df.duplicated().sum()
    print("Duplicate rows:", dups)
    fh.write("Duplicate rows: " + str(dups) + "\n\n")

    return df


def explore_large_file(name, path, fh):
    logger.info("Reading %s in chunks of %d rows ...", name, CHUNK_SIZE)

    print("=" * 60)
    print("FILE (chunked):", name)
    print("=" * 60)
    fh.write("FILE (chunked): " + name + "\n")

    total_rows = 0
    null_totals = None
    total_dups = 0
    first = True

    for i, chunk in enumerate(pd.read_csv(path, chunksize=CHUNK_SIZE), start=1):
        total_rows += len(chunk)

        if first:
            print("columns:", chunk.columns.tolist())
            print("dtypes:")
            print(chunk.dtypes)
            print("\nhead(5):")
            print(chunk.head(5))
            print("\ndescribe():")
            print(chunk.describe())
            buf = io.StringIO()
            chunk.info(buf=buf)
            print("\ninfo():")
            print(buf.getvalue())
            fh.write("columns: " + str(chunk.columns.tolist()) + "\n")
            fh.write("dtypes:\n" + str(chunk.dtypes) + "\n")
            first = False

        chunk_nulls = chunk.isnull().sum()
        if null_totals is None:
            null_totals = chunk_nulls
        else:
            null_totals = null_totals.add(chunk_nulls)

        total_dups += int(chunk.duplicated().sum())
        logger.info("  chunk %d: %d rows  (total so far: %d)", i, len(chunk), total_rows)

    print("\nTotal rows (all chunks):", total_rows)
    print("Total duplicate rows:", total_dups)
    print("isnull().sum() across all chunks:")
    print(null_totals)

    fh.write("Total rows: " + str(total_rows) + "\n")
    fh.write("Total duplicates: " + str(total_dups) + "\n")
    fh.write("isnull().sum():\n" + str(null_totals) + "\n\n")


def explore_all_files(raw_dir):
    raw_dir = pathlib.Path(raw_dir)

    csv_files = {
        "aisles":               (raw_dir / "aisles.csv",                False),
        "departments":          (raw_dir / "departments.csv",           False),
        "products":             (raw_dir / "products.csv",              False),
        "orders":               (raw_dir / "orders.csv",                False),
        "order_products_train": (raw_dir / "order_products__train.csv", False),
        "order_products_prior": (raw_dir / "order_products__prior.csv", True),
    }

    loaded = {}

    with open(REPORT_FILE, "w", encoding="utf-8") as fh:
        fh.write("Instacart Data Exploration Report\n")
        fh.write("=" * 60 + "\n\n")

        for name, (path, is_large) in csv_files.items():
            if not path.exists():
                print("File not found:", path)
                fh.write("File not found: " + str(path) + "\n")
                continue

            if is_large:
                explore_large_file(name, path, fh)
            else:
                df = explore_small_file(name, path, fh)
                loaded[name] = df

    logger.info("Report saved to %s", REPORT_FILE)
    return loaded
