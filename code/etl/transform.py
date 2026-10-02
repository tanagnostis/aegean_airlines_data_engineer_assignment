import logging
import pandas as pd
from code.etl.extract import extract_csv


logger = logging.getLogger(__name__)

EXPECTED_COLUMNS = [
    "YEAR",
    "MONTH",
    "DAY",
    "DAY_OF_WEEK",
    "AIRLINE",
    "FLIGHT_NUMBER",
    "TAIL_NUMBER",
    "ORIGIN_AIRPORT",
    "DESTINATION_AIRPORT",
    "SCHEDULED_DEPARTURE",
    "DEPARTURE_TIME",
    "DEPARTURE_DELAY",
    "TAXI_OUT",
    "WHEELS_OFF",
    "SCHEDULED_TIME",
    "ELAPSED_TIME",
    "AIR_TIME",
    "DISTANCE",
    "WHEELS_ON",
    "TAXI_IN",
    "SCHEDULED_ARRIVAL",
    "ARRIVAL_TIME",
    "ARRIVAL_DELAY",
    "DIVERTED",
    "CANCELLED",
    "CANCELLATION_REASON",
    "AIR_SYSTEM_DELAY",
    "SECURITY_DELAY",
    "AIRLINE_DELAY",
    "LATE_AIRCRAFT_DELAY",
    "WEATHER_DELAY"
]

KEY_COLUMNS = [
    "flight_date",
    "AIRLINE",
    "FLIGHT_NUMBER",
    "TAIL_NUMBER",
    "ORIGIN_AIRPORT",
    "DESTINATION_AIRPORT",
    "SCHEDULED_DEPARTURE"
    ]

STAGING_COLUMNS = ["flight_date", "airline", "flight_number", 
                   "tail_number", "origin_airport", "destination_airport", 
                   "scheduled_departure_ts", "actual_departure_ts", "wheels_off_ts", 
                    "scheduled_arrival_ts", "actual_arrival_ts", "wheels_on_ts",
                   "scheduled_time_minutes", "elapsed_time_minutes", "air_time_minutes", 
                   "distance", "departure_delay_minutes", "arrival_delay_minutes", "taxi_out_minutes", 
                   "taxi_in_minutes", "diverted", "cancelled", "cancellation_reason", "air_system_delay_minutes", 
                   "security_delay_minutes", "airline_delay_minutes", "late_aircraft_delay_minutes", "weather_delay_minutes"]

def create_flight_date(df):
    df["flight_date"] = pd.to_datetime(
        {"year": df["YEAR"], "month": df["MONTH"], "day": df["DAY"]},
        errors="coerce"
    )
    return df

def validate_schema(df):
    actual = list(df.columns)
    if actual != EXPECTED_COLUMNS:
        missing = set(EXPECTED_COLUMNS) - set(actual)
        extra = set(actual) - set(EXPECTED_COLUMNS)
        raise ValueError(f"Invalid CSV schema. Missing: {missing}; Extra: {extra}")

def data_quality_checks(df):

    # Check for duplicate rows
    if (df.duplicated().any()):
        raise ValueError("Data quality check failed: Duplicate rows found.")
    logger.info("Data quality check passed: No duplicate rows found.")

    # Check for duplicate business-key rows
    duplicate_count = int(df.duplicated(KEY_COLUMNS).sum())
    if duplicate_count:
        raise ValueError(
            f"Found {duplicate_count} duplicate business-key rows"
        )
    logger.info("Data quality check passed: No duplicate business-key rows found.")

    # Check for negative values in numeric columns
    for col in ["DISTANCE", "ELAPSED_TIME", "AIR_TIME", "TAXI_OUT", "TAXI_IN"]:
        if (df[col].dropna() < 0).any():
            raise ValueError(f"Negative values found in {col}")
    logger.info("Data quality check passed: No negative values found in numeric columns.")

    # Check for valid flag values in DIVERTED and CANCELLED columns
    for col in ["DIVERTED", "CANCELLED"]:
        bad = ~df[col].dropna().isin([0, 1])
        if bad.any():
            raise ValueError(f"Invalid flag values in {col}")
    logger.info("Data quality check passed: Valid flag values in DIVERTED and CANCELLED columns.")

    # Check for valid flight dates, months, and days
    if df["flight_date"].isna().any():
        raise ValueError("Invalid flight dates detected.")
    logger.info("Data quality check passed: Valid flight dates detected.")
    if (~df["MONTH"].between(1, 12)).any():
        raise ValueError("Invalid month detected.")
    logger.info("Data quality check passed: Valid month values detected.")
    if (~df["DAY"].between(1, 31)).any():
        raise ValueError("Invalid day detected.")
    logger.info("Data quality check passed: Valid day values detected.")

def hhmm_to_minutes(value):
    """Convert HHMM value to minutes after midnight."""

    if pd.isna(value):
        return pd.NA

    value = str(value).strip()

    if not value:
        return pd.NA

    try:
        hhmm = int(value)

        hours = hhmm // 100
        minutes = hhmm % 100

        if hours >= 24 or minutes >= 60:
            return pd.NA

        return hours * 60 + minutes

    except (TypeError, ValueError):
        return pd.NA

def create_flight_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Convert HHMM flight times into timestamps."""

    df = df.copy()

    time_columns = {
        "SCHEDULED_DEPARTURE": "scheduled_departure_ts",
        "DEPARTURE_TIME": "actual_departure_ts",
        "WHEELS_OFF": "wheels_off_ts",
        "WHEELS_ON": "wheels_on_ts",
        "SCHEDULED_ARRIVAL": "scheduled_arrival_ts",
        "ARRIVAL_TIME": "actual_arrival_ts",
    }

    for source_column, target_column in time_columns.items():

        minutes = df[source_column].apply(hhmm_to_minutes)

        df[target_column] = (
            df["flight_date"]
            + pd.to_timedelta(minutes, unit="m")
        )

    # Actual flights crossing midnight.
    overnight = (
        df["actual_departure_ts"].notna()
        & df["actual_arrival_ts"].notna()
        & (
            df["actual_arrival_ts"]
            < df["actual_departure_ts"]
        )
    )

    df.loc[
        overnight,
        "actual_arrival_ts"
    ] += pd.Timedelta(days=1)

    # Scheduled flights crossing midnight.
    scheduled_overnight = (
        df["scheduled_departure_ts"].notna()
        & df["scheduled_arrival_ts"].notna()
        & (
            df["scheduled_arrival_ts"]
            < df["scheduled_departure_ts"]
        )
    )

    df.loc[
        scheduled_overnight,
        "scheduled_arrival_ts"
    ] += pd.Timedelta(days=1)

    return df

def transform_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    numeric_columns = {
        "FLIGHT_NUMBER": "flight_number",
        "SCHEDULED_TIME": "scheduled_time_minutes",
        "ELAPSED_TIME": "elapsed_time_minutes",
        "AIR_TIME": "air_time_minutes",
        "DISTANCE": "distance",

        "DEPARTURE_DELAY": "departure_delay_minutes",
        "ARRIVAL_DELAY": "arrival_delay_minutes",

        "TAXI_OUT": "taxi_out_minutes",
        "TAXI_IN": "taxi_in_minutes",

        "DIVERTED": "diverted",
        "CANCELLED": "cancelled",

        "AIR_SYSTEM_DELAY": "air_system_delay_minutes",
        "SECURITY_DELAY": "security_delay_minutes",
        "AIRLINE_DELAY": "airline_delay_minutes",
        "LATE_AIRCRAFT_DELAY": "late_aircraft_delay_minutes",
        "WEATHER_DELAY": "weather_delay_minutes",
    }

    for source_column, target_column in numeric_columns.items():
        df[target_column] = pd.to_numeric(
            df[source_column],
            errors="coerce",
        )

    return df

def normalize_columns(df):
    return df.rename(columns={
        "AIRLINE": "airline",
        "TAIL_NUMBER": "tail_number",
        "ORIGIN_AIRPORT": "origin_airport",
        "DESTINATION_AIRPORT": "destination_airport",
        "CANCELLATION_REASON": "cancellation_reason",
    })

def select_staging_columns( df: pd.DataFrame, ) -> pd.DataFrame: 
    """
    Return only normalized staging columns.
    """ 
    missing = [ column for column in STAGING_COLUMNS if column not in df.columns ] 
    if missing: 
        raise ValueError( "Missing transformed staging columns: " f"{missing}" )
    return df[STAGING_COLUMNS].copy()


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Transform raw flight data into DWH-ready records."""

    logger.info("Starting transformation: %d rows", len(df))

    validate_schema(df)

    df = create_flight_date(df)
    logger.info("Created flight_date column.")

    # Validate source data here.
    data_quality_checks(df)
    logger.info("Data quality checks passed.")

    df = create_flight_timestamps(df)
    logger.info("Created flight timestamp columns.")

    df = transform_numeric_columns(df)
    logger.info("Transformed numeric columns.")

    df = normalize_columns(df)
    logger.info("Normalized column names.")

    df = select_staging_columns(df)

    logger.info(
        "Transformation completed: %d rows, %d columns",
        len(df),
        len(df.columns),
    )
    return df

if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO, format=( "%(asctime)s | " "%(levelname)s | " "%(name)s | " "%(message)s" ), )
    for chunk_number, df in extract_csv():
        print(df.head(5))
        try:
            transformed_df = transform(df)
            logger.info("Chunk %d transformed successfully.", chunk_number)
        except ValueError as e:
            logger.error("Error transforming chunk %d: %s", chunk_number, e)
    logger.info("Data transformation completed.")