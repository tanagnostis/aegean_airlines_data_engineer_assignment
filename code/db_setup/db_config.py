'''Module for database configuration and credentials.'''
import logging
import os
from .db_connection import DBConnection

logger = logging.getLogger(__name__)

def get_warehouse_creds() -> DBConnection:
    return DBConnection(
        user=os.getenv("WAREHOUSE_USER", ""),
        password=os.getenv("WAREHOUSE_PASSWORD", ""),
        db=os.getenv("WAREHOUSE_DB", ""),
        host=os.getenv("WAREHOUSE_HOST", ""),
        port=int(os.getenv("WAREHOUSE_PORT", 5432)),
    )