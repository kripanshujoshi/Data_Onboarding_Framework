"""
File processing utilities for Data Onboarding Framework.
"""

import logging
import os
import pandas as pd
import zipfile

from modules.config_generators import generate_sys_config_table_info
from modules.logging_setup import log_function

logger = logging.getLogger(__name__)
SUPPORTED_EXTENSIONS = [".csv", ".xlsx"]


@log_function
def read_csv(file):
    """Read CSV file into DataFrame with error handling."""
    try:
        return pd.read_csv(file, dtype=str)
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        raise


@log_function
def read_excel(file):
    """Read Excel file into DataFrame with error handling."""
    try:
        xls = pd.ExcelFile(file)
        return xls.parse(xls.sheet_names[0], dtype=str)
    except Exception as e:
        logger.error(f"Error reading Excel file: {e}")
        raise


@log_function
def process_uploaded_zip(uploaded_zip_file, src_nm, table_nm, generate_sys_config_table_info_fn):
    """
    Process uploaded ZIP file, extract supported files, and generate metadata and table info.
    """
    from modules.metadata import extract_metadata_from_dataframe
    all_metadata = []
    table_info_df = pd.DataFrame()
    with zipfile.ZipFile(uploaded_zip_file) as z:
        for file_info in z.infolist():
            if file_info.is_dir():
                continue
            base_filename = os.path.basename(file_info.filename)
            _, ext = os.path.splitext(base_filename)
            ext = ext.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue
            try:
                with z.open(file_info) as file:
                    if ext == ".csv":
                        df = pd.read_csv(file, dtype=str)
                    else:  # .xlsx
                        xls = pd.ExcelFile(file)
                        df = xls.parse(xls.sheet_names[0], dtype=str)
                metadata_df = extract_metadata_from_dataframe(df, src_nm, base_filename)
                all_metadata.append(metadata_df)
                if not metadata_df.empty:
                    temp_table_df = generate_sys_config_table_info_fn(base_filename)
                    table_info_df = pd.concat([table_info_df, temp_table_df], ignore_index=True)
            except Exception as e:
                logger.error(f"Error processing file {base_filename} in zip: {e}")
    all_metadata_df = pd.concat(all_metadata, ignore_index=True) if all_metadata else pd.DataFrame()
    return all_metadata_df, table_info_df
