'''Modules for extracting data from csv file.'''
import os
import sys
import logging
import pandas as pd
import csv
# sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')) 

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

def extract_csv_delimiter(data_path: str, filename: str) -> str:
    """
    Checks for delimiter in the csv file and file size.
    Args:
        data_path:  Path to the directory containing the file.
        filename:   Filename from where to extract delimiter.
    Returns:
        str:        Delimiter used in the csv file.
    """
    with open(f"{data_path}/{filename}", newline='', encoding = "utf-8") as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(8192)) # Checking the separator and use that for the pandas read_csv function
        logging.info("File %s has delimiter/separator: '%s'", filename, dialect.delimiter)
        file_size = os.path.getsize(f"{data_path}/{filename}") # Checking file size
        logging.info("File size: %d KB", round(file_size/1024))
        return dialect.delimiter