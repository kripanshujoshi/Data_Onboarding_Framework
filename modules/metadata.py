import logging
import os
import pandas as pd
from modules.logging_setup import log_function
from modules.sql_generator import infer_snowflake_type

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = [".csv", ".xlsx"]


"""
Metadata extraction utilities for Data Onboarding Framework.
"""


@log_function
def extract_metadata_from_dataframe(df, src_nm, table_nm):
    """Extract metadata from DataFrame for a given table."""
    logger.debug(f"Extracting metadata for src={src_nm}, table={table_nm}")
    if df.empty:
        return pd.DataFrame()
    name_without_ext = os.path.splitext(table_nm)[0]
    redshift_table_nm = name_without_ext.strip()
    df.columns = df.columns.str.strip()
    extracted_data = []
    for counter, col in enumerate(df.columns, start=1):
        col_data = df[col].dropna()
        inferred_type = infer_snowflake_type(col_data)
        max_length = col_data.astype(str).str.len().max() if not col_data.empty else 0
        primary_key = "X" if col_data.nunique() == len(df) and not col_data.empty else ""
        extracted_data.append({
            "src_nm": src_nm,
            "src_table_nm": redshift_table_nm,
            "field_nm": col,
            "field_posn_nbr": counter,
            "datatype_nm": inferred_type,
            "datatype_size_val": max_length if max_length else "",
            "datatype_scale_val": max_length if max_length else "",
            "key_ind": primary_key,
            "check_table": '',
            "field_desc": '',
            "dprct_ind": '',
            "partitn_ind": '',
            "sort_key_ind": '',
            "dist_key_ind": '',
            "proc_stage_cd": '',
            "catlg_flg": '',
            "dblqt_repl_flg": '',
            "delta_key_ind": ''
        })
    return pd.DataFrame(extracted_data)


@log_function
def extract_metadata_from_excel(xls, src_nm, table_nm):
    """Extract metadata from first sheet of Excel file."""
    logger.debug(f"Extracting metadata from Excel for src={src_nm}, table={table_nm}")
    sheet_name = xls.sheet_names[0]  # Use first sheet
    df = xls.parse(sheet_name, dtype=str)
    if df.empty:
        return pd.DataFrame()
    df.columns = df.columns.str.strip()
    return extract_metadata_from_dataframe(df, src_nm, table_nm)


@log_function
def extract_from_uploaded_file(uploaded_file, src_nm, table_nm, generate_sys_config_table_info_fn):
    """Process uploaded file and extract metadata and table config info."""
    from modules.file_processor import process_uploaded_zip, read_csv, read_excel
    filename = uploaded_file.name
    ext = os.path.splitext(filename)[1].lower()
    logger.info(f"Processing uploaded file: {filename}")
    try:
        if ext == ".csv":
            df = read_csv(uploaded_file)
            metadata_df = extract_metadata_from_dataframe(df, src_nm, table_nm)
            table_info_df = generate_sys_config_table_info_fn(filename)
        elif ext == ".xlsx":
            df = read_excel(uploaded_file)
            metadata_df = extract_metadata_from_dataframe(df, src_nm, table_nm)
            table_info_df = generate_sys_config_table_info_fn(filename)
        elif ext == ".zip":
            metadata_df, table_info_df = process_uploaded_zip(uploaded_file, src_nm, table_nm, generate_sys_config_table_info_fn)
        else:
            raise ValueError("Unsupported file type.")
        return metadata_df, table_info_df
    except Exception as e:
        logger.error(f"Error extracting from uploaded file: {e}")
        raise