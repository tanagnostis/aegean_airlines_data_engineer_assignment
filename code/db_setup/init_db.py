import logging
from pathlib import Path
from sqlalchemy import Engine, text
from .load_engine import load_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SQL_DIR = BASE_DIR / "code" / "sql"
SQL_STAGING_FILE = "staging.sql"
SQL_STAGING_PATH = SQL_DIR / SQL_STAGING_FILE
SQL_TARGET_FILE = "target.sql"
SQL_TARGET_PATH = SQL_DIR / SQL_TARGET_FILE


def execute_sql_file( engine: Engine, sql_path: Path, ) -> None: 
    """ 
    Execute a SQL script using the supplied SQLAlchemy engine.
    """
    logger.info( "Executing SQL script: %s", sql_path)

    sql = sql_path.read_text( encoding="utf-8" ) 
    
    if not sql.strip(): 
        logger.warning( "SQL file is empty: %s", sql_path)
        return
    
    with engine.begin() as connection: 
        connection.execute(text(sql)) 
        connection.commit()
        logger.info( "Successfully executed: %s", sql_path)


def init_db(engine: Engine) -> None:
    """
    Initializes the database by executing SQL scripts for staging and target tables.
    Args:
        engine: SQLAlchemy engine object for database connection.
    """
    logger.info("Initializing the database...")
    
    # Create staging tables 
    execute_sql_file(engine, SQL_STAGING_PATH) 
    
    # Create target tables 
    execute_sql_file(engine, SQL_TARGET_PATH) 
    
    logger.info( "Database initialization completed.")