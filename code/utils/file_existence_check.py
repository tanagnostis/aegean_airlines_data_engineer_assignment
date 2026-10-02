import os
import logging

def file_existence_check(data_path: str, filename: str) -> bool:
    """
    Checks for file existence.
    Args:
        data_path:  Path to the directory containing the file.
        filename:   Filename to be checked.
    Returns:
        bool:       True if file exists, False otherwise.
    """
    if os.path.exists(f"{data_path}/{filename}"):
        logging.info("Existing file in %s with name: %s ", data_path, filename)
        return True
    else:
        logging.error("No existing file in %s with name: %s ", data_path, filename)
        logging.info("Provide proper path and file name.")
        return False