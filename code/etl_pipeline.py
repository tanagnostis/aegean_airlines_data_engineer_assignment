"""Historical flights ETL pipeline."""

import logging
from pathlib import Path
from sqlalchemy import text

from code.db_setup.init_db import init_db
from code.db_setup.load_engine import load_engine
from code.etl.extract import extract_csv
from code.etl.transform import transform
from code.etl.load import load_chunk
from code.db_update.daily_feed_update import run_daily_feed_update


logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

SQL_DIR = BASE_DIR / "code" / "sql"
DWH_SETUP_FILE = "dwh_setup.sql"

DWH_SETUP_PATH = SQL_DIR / DWH_SETUP_FILE

def run_pipeline():
    logger.info("Starting historical flights ETL pipeline")

    # Create SQLAlchemy engine once.
    engine = load_engine()

    # Create schemas/tables.
    init_db(engine)

    total_rows = 0

    # Extract → Transform → Load
    for chunk_number, df in extract_csv():

        logger.info(
            "Processing chunk %d (%d rows)",
            chunk_number,
            len(df),
        )

        transformed_df = transform(df)

        # print("Column count:", len(transformed_df.columns)) 
        # for i, column in enumerate( transformed_df.columns, start=1, ): 
        #     print(i, column)

        rows_loaded = load_chunk(
            transformed_df,
            engine,
            schema_name="staging",
            table_name="flights_stg",
        )

        total_rows += rows_loaded

        logger.info(
            "Chunk %d completed. Total rows loaded: %d",
            chunk_number,
            total_rows,
        )

    logger.info(
        "Historical ETL completed. Total rows loaded: %d",
        total_rows,
    )

    logger.info("Start population of dimension tables and fact table.")

    # Execute the DWH setup SQL script to populate dimension and fact tables.

    dwh_setup_sql = DWH_SETUP_PATH.read_text( encoding="utf-8" )
    
    with engine.begin() as connection: 
        connection.execute(text(dwh_setup_sql)) 
        connection.commit()
        logger.info("Successfully executed: %s", DWH_SETUP_PATH)
        logger.info("Fact table fact_flights populated successfully.")
    logger.info("Population of dimension tables and fact table completed.")

    # Execute script for daily feed update.
    run_daily_feed_update(engine)
    logger.info("Daily feed update completed.")

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

    run_pipeline()