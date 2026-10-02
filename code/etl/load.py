"""Functions for loading transformed data into PostgreSQL."""

import logging
from io import StringIO

import pandas as pd
from sqlalchemy import Engine

logger = logging.getLogger(__name__)


def load_chunk(
    df: pd.DataFrame,
    engine: Engine,
    schema_name: str,
    table_name: str,
) -> int:
    """
    Load a Pandas DataFrame into PostgreSQL using COPY.

    The DataFrame is converted to CSV in memory and streamed to
    PostgreSQL using COPY FROM STDIN.
    """

    if df.empty:
        logger.warning(
            "Skipping empty DataFrame for %s.%s",
            schema_name,
            table_name,
        )
        return 0

    row_count = len(df)

    logger.info(
        "Loading %d rows into %s.%s using COPY",
        row_count,
        schema_name,
        table_name,
    )

    # Convert DataFrame to CSV in memory.
    csv_buffer = StringIO()

    df.to_csv(
        csv_buffer,
        index=False,
        header=False,
        na_rep="\\N",
    )

    csv_buffer.seek(0)

    # Get the underlying psycopg2 connection from SQLAlchemy.
    raw_connection = engine.raw_connection()

    try:
        with raw_connection.cursor() as cursor:

            copy_sql = f"""
                COPY "{schema_name}"."{table_name}"
                ( flight_date, airline, flight_number, tail_number, origin_airport, destination_airport, scheduled_departure_ts, actual_departure_ts, wheels_off_ts, wheels_on_ts, scheduled_arrival_ts, actual_arrival_ts, scheduled_time_minutes, elapsed_time_minutes, air_time_minutes, distance, departure_delay_minutes, arrival_delay_minutes, taxi_out_minutes, taxi_in_minutes, diverted, cancelled, cancellation_reason, air_system_delay_minutes, security_delay_minutes, airline_delay_minutes, late_aircraft_delay_minutes, weather_delay_minutes )
                FROM STDIN
                WITH (
                    FORMAT CSV,
                    NULL '\\N'
                )
            """

            cursor.copy_expert(
                copy_sql,
                csv_buffer,
            )

        raw_connection.commit()

    except Exception:
        raw_connection.rollback()
        logger.exception(
            "COPY failed for %s.%s",
            schema_name,
            table_name,
        )
        raise

    finally:
        raw_connection.close()

    logger.info(
        "Successfully loaded %d rows into %s.%s",
        row_count,
        schema_name,
        table_name,
    )

    return row_count

