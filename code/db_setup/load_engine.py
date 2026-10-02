
import logging
from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text
from .db_config import get_warehouse_creds
from .db_connection import WarehouseConnection

logger = logging.getLogger(__name__)

def load_engine() -> Engine: 
	"""
	Create and return a SQLAlchemy engine.
	""" 
	logger.info("Starting load_db process") 
	
	load_dotenv() 
	db_creds = get_warehouse_creds() 
	database_connection = WarehouseConnection(db_creds) 
	
	engine = create_engine(database_connection.conn_url) 
	logger.info("SQLAlchemy engine created successfully") 
	return engine 
	
if __name__ == "__main__": 
	logging.basicConfig( level=logging.INFO, format=( "%(asctime)s | " "%(levelname)s | " "%(name)s | " "%(message)s" ), ) 
	load_engine()