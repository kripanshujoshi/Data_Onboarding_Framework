"""
Business logic for Data Onboarding Framework: template generation, SQL script generation, file zipping, and git push.
"""
import os
import streamlit as st
import pandas as pd
import tempfile
import zipfile
from io import BytesIO
from datetime import datetime
from modules import metadata, db, git_helper, sql_generator
from modules.config_generators import generate_sys_config_dataset_info, generate_sys_config_pre_proc_info, generate_sys_config_table_info
from modules.logging_setup import log_function

@log_function
def generate_templates(uploaded_file, src_nm, domn_nm, dataset_nm, table_nm, data_clasfctn_nm, fmt_type_cd, delmtr_cd, dprct_methd_cd, dialect, warehouse_nm):
    metadata_df, table_info_df = metadata.extract_from_uploaded_file(
        uploaded_file, src_nm, table_nm,
        lambda file: generate_sys_config_table_info(src_nm, domn_nm, dataset_nm, file, data_clasfctn_nm, fmt_type_cd, delmtr_cd, dprct_methd_cd)
    )
    sys_config_dataset_info = generate_sys_config_dataset_info(src_nm, dataset_nm, dialect, warehouse_nm)
    sys_config_pre_proc_info = generate_sys_config_pre_proc_info(src_nm, dataset_nm, fmt_type_cd)
    sys_config_table_info = table_info_df
    return metadata_df, sys_config_dataset_info, sys_config_pre_proc_info, sys_config_table_info
