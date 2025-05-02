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

def generate_templates(uploaded_file, src_nm, domn_nm, dataset_nm, table_nm, data_clasfctn_nm, fmt_type_cd, delmtr_cd, dprct_methd_cd, dialect, warehouse_nm):
    metadata_df, table_info_df = metadata.extract_from_uploaded_file(
        uploaded_file, src_nm, table_nm,
        lambda file: generate_sys_config_table_info(src_nm, domn_nm, dataset_nm, file, data_clasfctn_nm, fmt_type_cd, delmtr_cd, dprct_methd_cd)
    )
    sys_config_dataset_info = generate_sys_config_dataset_info(src_nm, dataset_nm, dialect, warehouse_nm)
    sys_config_pre_proc_info = generate_sys_config_pre_proc_info(src_nm, dataset_nm, fmt_type_cd)
    sys_config_table_info = table_info_df
    return metadata_df, sys_config_dataset_info, sys_config_pre_proc_info, sys_config_table_info

def fetch_dataframe(query, params):
    conn = db.check_db_connection()
    if conn is None:
        return pd.DataFrame()

    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            result = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            df = pd.DataFrame(result, columns=columns)
            return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_table_field_info(src_nm, src_table_nm):
    query = f"SELECT * FROM app_mgmt.sys_config_table_field_info WHERE src_nm = %s AND src_table_nm = %s"
    return fetch_dataframe(query, (src_nm, src_table_nm))

def get_dataset_info(src_nm, dataset_nm):
    query = f"SELECT * FROM app_mgmt.sys_config_dataset_info WHERE src_nm = %s AND dataset_nm = %s"
    return fetch_dataframe(query, (src_nm, dataset_nm))

def get_table_info(src_nm, dataset_nm):
    query = f"SELECT * FROM app_mgmt.sys_config_table_info WHERE src_nm = %s AND dataset_nm = %s"
    return fetch_dataframe(query, (src_nm, dataset_nm))

def get_pre_proc_info(src_nm, dataset_nm):
    query = f"SELECT * FROM app_mgmt.sys_config_pre_proc_info WHERE src_nm = %s AND dataset_nm = %s"
    return fetch_dataframe(query, (src_nm, dataset_nm))

def generate_sql_scripts(df_metadata_df, src_nm, dataset_nm, table_nm, df_dataset_info, df_pre_proc_info, df_table_info):
    land_sql_script = sql_generator.generate_create_table_script(df_metadata_df, 'land', src_nm, dataset_nm)
    stage_sql_script = sql_generator.generate_create_table_script(df_metadata_df, 'stage', src_nm, dataset_nm)
    rds_sql_script = sql_generator.generate_insert_statements(src_nm, dataset_nm, table_nm,
        df_dataset_info, df_pre_proc_info, df_table_info, df_metadata_df)
    return land_sql_script, stage_sql_script, rds_sql_script

def prepare_zip(scripts, src_nm, dataset_nm):
    output = BytesIO()
    with zipfile.ZipFile(output, "w") as zf:
        for script_name, script_content in scripts.items():
            zf.writestr(script_name, script_content)
    output.seek(0)
    return output

def git_push_scripts(scripts, src_nm, dataset_nm):
    temp_dir = tempfile.mkdtemp()
    sql_files_list = []
    for script_name, script_content in scripts.items():
        file_path = os.path.join(temp_dir, script_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        sql_files_list.append(file_path)
    branch_name = f"feature/{src_nm}_{dataset_nm}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    folder_name = f"{src_nm}_{dataset_nm}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    git_helper.git_push_files_to_feature_branch(sql_files_list, branch_name, folder_name)
    # Clean up temp_dir is handled by git_helper

def insert_into_rds(rds_sql_script):
    return db.insert_statements_into_postgres(rds_sql_script)
