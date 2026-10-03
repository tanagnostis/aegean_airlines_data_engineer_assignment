import logging
from pathlib import Path
from code.db_setup.init_db import execute_sql_file

logging.basicConfig(level=logging.INFO)

def setup_availability_view():
    sql_file = Path("code/sql/availability_view_setup.sql")
    execute_sql_file(sql_file)

if __name__ == "__main__":
    setup_availability_view()
    logging.info("Availability view setup completed.")