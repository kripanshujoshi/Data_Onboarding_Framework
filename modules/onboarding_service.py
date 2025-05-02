"""
Business logic for Data Onboarding Framework: template generation, SQL script generation, file zipping, and git push.
"""
from modules import metadata
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


@log_function
def fetch_dataframe(query, params):
    pass


@log_function
def get_table_field_info(src_nm, src_table_nm):
    pass


@log_function
def get_dataset_info(src_nm, dataset_nm):
    pass


@log_function
def get_table_info(src_nm, dataset_nm):
    pass


@log_function
def get_pre_proc_info(src_nm, dataset_nm):
    pass


@log_function
def generate_sql_scripts(df_metadata_df, src_nm, dataset_nm, table_nm, df_dataset_info, df_pre_proc_info, df_table_info):
    pass


@log_function
def prepare_zip(scripts, src_nm, dataset_nm):
    pass


@log_function
def git_push_scripts(scripts, src_nm, dataset_nm):
    pass


@log_function
def insert_into_rds(rds_sql_script):
    pass
