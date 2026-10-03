import logging
import pandas as pd
from typing import Iterator
from pathlib import Path
from code.utils.file_existence_check import file_existence_check
from code.utils.extract_csv_delimiter import extract_csv_delimiter

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
HISTORICAL_DATA_DIR = BASE_DIR / "data" / "historical_data"
HISTORICAL_DATA_FILE = "flights.csv"
CHUNK_SIZE = 100000  # Number of rows to read in each chunk

dtype_mapping = {
    'YEAR': 'Int16',
    'MONTH': 'Int8',
    'DAY': 'Int8',
    'DAY_OF_WEEK': 'Int8',

    'AIRLINE': 'string',
    'FLIGHT_NUMBER': 'Int32',
    'TAIL_NUMBER': 'string',

    'ORIGIN_AIRPORT': 'string',
    'DESTINATION_AIRPORT': 'string',

    'SCHEDULED_DEPARTURE': 'string',
    'DEPARTURE_TIME': 'string',
    'WHEELS_OFF': 'string',
    'TAXI_OUT': 'Int32',

    'SCHEDULED_TIME': 'Int32',
    'ELAPSED_TIME': 'Int32',
    'AIR_TIME': 'Int32',

    'SCHEDULED_ARRIVAL': 'string',
    'ARRIVAL_TIME': 'string',
    'WHEELS_ON': 'string',
    'TAXI_IN': 'Int32',

    'DEPARTURE_DELAY': 'Float32',
    'ARRIVAL_DELAY': 'Float32',
    'DISTANCE': 'Int32',

    'DIVERTED': 'Int8',
    'CANCELLED': 'Int8',
    'CANCELLATION_REASON': 'string',

    'AIR_SYSTEM_DELAY': 'Float32',
    'SECURITY_DELAY': 'Float32',
    'AIRLINE_DELAY': 'Float32',
    'LATE_AIRCRAFT_DELAY': 'Float32',
    'WEATHER_DELAY': 'Float32'
}


def extract_csv_chunks(data_path: str, filename: str) -> Iterator[tuple[int, pd.DataFrame]]:
    """
    Extracts data from a CSV file in chunks.

    Args:
        data_path:  Path to the directory containing the CSV file.
        filename:   Filename of the CSV file to be extracted.
    Returns:
        Iterator[tuple[int, pd.DataFrame]]: An iterator yielding tuples of chunk number and corresponding DataFrame.
    """
    file_path = data_path / filename 
    
    logger.info("Starting CSV extraction: %s", file_path) 
    # ---------------------------------------------------------
    # 1. Check file existence 
    # --------------------------------------------------------- 
    if not file_existence_check(data_path, filename): 
        raise FileNotFoundError( f"CSV file does not exist: {file_path}" ) 
    
    # ---------------------------------------------------------
    # 2. Detect delimiter 
    # --------------------------------------------------------- 
    delimiter = extract_csv_delimiter(data_path, filename) 
    logger.info( "Detected CSV delimiter '%s' for file %s", delimiter, filename) 
    
    # ---------------------------------------------------------
    # 3. Read CSV in chunks
    # ---------------------------------------------------------
    try: 
        chunks = pd.read_csv(file_path, dtype = dtype_mapping, sep = delimiter, chunksize=CHUNK_SIZE, low_memory=False, encoding='utf-8') 
        total_rows = 0 
        for chunk_number, df in enumerate(chunks, start=1): 
            rows, columns = df.shape 
            logger.info( "Reading chunk %d: %d rows, %d columns", chunk_number, rows, columns) 
    # -------------------------------------------------
    # 4. Validate chunk 
    # -------------------------------------------------
    
            if df.empty: 
                logger.warning( "Chunk %d from %s is empty", chunk_number, filename) 
             
            if df.shape[1] == 0: 
                logger.warning( "Chunk %d from %s has no columns", chunk_number, filename) 

            total_rows += rows 
    
            logger.info( "Successfully extracted chunk %d from %s", chunk_number, filename, ) 
    
            yield chunk_number, df 
    
        logger.info( "Finished CSV extraction: %s. Total rows extracted: %d", filename, total_rows, ) 

    except pd.errors.ParserError as exc:
        logger.exception("CSV parsing error: %s", file_path)
        raise ValueError(f"Unable to parse CSV file: {filename}") from exc

    except Exception:
        logger.exception("Unexpected error while extracting: %s", filename)
        raise

def extract_csv() -> Iterator[tuple[int, pd.DataFrame]]: 
    """ Extract historical flights data. 
    Yields: Tuple containing chunk number and DataFrame. 
    """ 
    yield from extract_csv_chunks(HISTORICAL_DATA_DIR, HISTORICAL_DATA_FILE)
