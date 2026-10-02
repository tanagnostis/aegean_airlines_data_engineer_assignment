import logging
from pathlib import Path

import pandas as pd

from code.db_setup.init_db import execute_sql_file
from code.db_setup.load_engine import load_engine
from code.etl.load import load_chunk
from code.etl.transform import transform
from code.etl.extract import dtype_mapping
from code.utils.extract_csv_delimiter import extract_csv_delimiter
from code.utils.file_existence_check import file_existence_check


logger = logging.getLogger(__name__)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DAILY_FEED_DATA_DIR = BASE_DIR / "data" / "daily_feed"
DAILY_FEED_DATA_FILE = "daily_feed_2015-01-07.csv"
DAILY_FEED_DATA_PATH = DAILY_FEED_DATA_DIR / DAILY_FEED_DATA_FILE
SQL_DIR = BASE_DIR / "code" / "sql"
DAILY_FEED_SQL_PATH = SQL_DIR / "daily_feed.sql"
DAILY_FEED_UPDATE_SQL_PATH = SQL_DIR / "daily_feed_update.sql"


# ============================================================
# BUSINESS RULES
# ============================================================

FEED_WINDOW_DAYS = 14

CORRECTION_WINDOW_DAYS = 7


# ============================================================
# EXTRACT
# ============================================================

def extract_daily_feed() -> pd.DataFrame:
    """
    Extract the daily flight feed from CSV.

    Returns:
        Pandas DataFrame containing the daily feed.
    """

    logger.info(
        "Starting daily feed extraction..."
    )

    # --------------------------------------------------------
    # Check file
    # --------------------------------------------------------

    if not file_existence_check(
        DAILY_FEED_DATA_DIR,
        DAILY_FEED_DATA_FILE,
    ):
        raise FileNotFoundError(
            "Daily feed file does not exist: "
            f"{DAILY_FEED_DATA_PATH}"
        )


    # --------------------------------------------------------
    # Detect delimiter
    # --------------------------------------------------------

    delimiter = extract_csv_delimiter(
        DAILY_FEED_DATA_DIR,
        DAILY_FEED_DATA_FILE,
    )


    logger.info(
        "Detected CSV delimiter: %r",
        delimiter,
    )


    # --------------------------------------------------------
    # Read CSV
    # --------------------------------------------------------

    try:

        daily_feed_df = pd.read_csv(
            DAILY_FEED_DATA_PATH,
            sep=delimiter,
            dtype=dtype_mapping,
            low_memory=False,
        )

    except pd.errors.ParserError as exc:

        logger.exception(
            "Unable to parse daily feed: %s",
            DAILY_FEED_DATA_PATH,
        )

        raise ValueError(
            "Invalid daily feed CSV format."
        ) from exc

    except OSError:

        logger.exception(
            "Unable to read daily feed: %s",
            DAILY_FEED_DATA_PATH,
        )

        raise


    # --------------------------------------------------------
    # Validate not empty
    # --------------------------------------------------------

    if daily_feed_df.empty:

        raise ValueError(
            "Daily feed is empty: "
            f"{DAILY_FEED_DATA_PATH}"
        )


    logger.info(
        "Daily feed extracted successfully: %d rows",
        len(daily_feed_df),
    )


    return daily_feed_df


# ============================================================
# STAGING TABLE
# ============================================================

def create_daily_feed_table(engine) -> None:
    """
    Create the daily feed staging table.
    """

    logger.info(
        "Creating daily feed staging table..."
    )

    execute_sql_file(
        engine,
        DAILY_FEED_SQL_PATH,
    )

    logger.info(
        "Daily feed staging table is ready."
    )


# ============================================================
# CLEAR STAGING
# ============================================================

def truncate_daily_feed(engine) -> None:
    """
    Remove the previous daily feed from staging.
    """

    logger.info(
        "Truncating staging.daily_feed..."
    )

    with engine.begin() as connection:

        connection.exec_driver_sql(
            "TRUNCATE TABLE staging.daily_feed"
        )

    logger.info(
        "staging.daily_feed truncated successfully."
    )


# ============================================================
# LOAD STAGING
# ============================================================

def load_daily_feed(
    engine,
    daily_feed_df: pd.DataFrame,
) -> int:
    """
    Load transformed daily feed into PostgreSQL staging.
    """

    logger.info(
        "Loading daily feed into "
        "staging.daily_feed..."
    )

    rows_loaded = load_chunk(
        daily_feed_df,
        engine,
        schema_name="staging",
        table_name="daily_feed",
    )

    logger.info(
        "Loaded %d rows into staging.daily_feed",
        rows_loaded,
    )

    return rows_loaded


# ============================================================
# UPDATE DWH
# ============================================================

def update_dwh(engine) -> None:
    """
    Replace the correction window in the DWH
    using the current daily feed.
    """

    logger.info(
        "Starting DWH daily-feed refresh..."
    )

    execute_sql_file(
        engine,
        DAILY_FEED_UPDATE_SQL_PATH,
    )

    logger.info(
        "DWH daily-feed refresh completed."
    )


# ============================================================
# PIPELINE
# ============================================================

def run_daily_feed_update(engine) -> None:
    """
    Run the complete daily feed ETL process.

    Process:

        CSV
         ↓
        Extract
         ↓
        Transform + DQ
         ↓
        staging.daily_feed
         ↓
        correction-window refresh
         ↓
        dw.fact_flight
    """

    logger.info(
        "=================================================="
    )

    logger.info(
        "Starting daily feed update..."
    )

    logger.info(
        "Feed window: %d days",
        FEED_WINDOW_DAYS,
    )

    logger.info(
        "Correction window: %d days",
        CORRECTION_WINDOW_DAYS,
    )


    # --------------------------------------------------------
    # 1. EXTRACT
    # --------------------------------------------------------

    daily_feed_df = extract_daily_feed()


    # --------------------------------------------------------
    # 2. TRANSFORM + DATA QUALITY
    # --------------------------------------------------------

    logger.info(
        "Transforming daily feed..."
    )

    daily_feed_df = transform(
        daily_feed_df
    )


    logger.info(
        "Daily feed transformation completed."
    )


    # --------------------------------------------------------
    # 3. CREATE STAGING TABLE
    # --------------------------------------------------------

    create_daily_feed_table(
        engine
    )


    # --------------------------------------------------------
    # 4. CLEAR PREVIOUS FEED
    # --------------------------------------------------------

    truncate_daily_feed(
        engine
    )


    # --------------------------------------------------------
    # 5. LOAD DAILY FEED
    # --------------------------------------------------------

    rows_loaded = load_daily_feed(
        engine,
        daily_feed_df,
    )


    # --------------------------------------------------------
    # 6. UPDATE DWH
    # --------------------------------------------------------

    update_dwh(
        engine
    )


    # --------------------------------------------------------
    # 7. FINISH
    # --------------------------------------------------------

    logger.info(
        "Daily feed update completed successfully."
    )

    logger.info(
        "Rows processed: %d",
        rows_loaded,
    )

    logger.info(
        "=================================================="
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )


    engine = load_engine()


    run_daily_feed_update(
        engine
    )
