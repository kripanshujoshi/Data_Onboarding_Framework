import pandas as pd
from modules import db
import streamlit as st
from modules.logging_setup import log_function


@log_function
def infer_snowflake_type(col_data: pd.Series) -> str:
    if col_data.empty:
        return "VARCHAR(255)"

    if col_data.str.isnumeric().all():
        return "NUMBER(38,0)"

    try:
        if pd.to_datetime(col_data, errors='coerce').notna().all():
            return "TIMESTAMP_NTZ"
    except Exception:
        pass

    return "VARCHAR(255)"


@log_function
def generate_create_table_script(
    metadata_df: pd.DataFrame, schema_name: str, src_nm: str, dataset_nm: str
) -> str:
    if metadata_df.empty:
        return "No metadata available to generate SQL."

    table_name = metadata_df.iloc[0]['src_table_nm']
    columns_sql = []

    for _, row in metadata_df.iterrows():
        col_def = f"{row['field_nm']} {row['datatype_nm']}"
        if row['key_ind'] == "Y":
            col_def += " PRIMARY KEY"
        columns_sql.append(col_def)

    sql_script = (
        f"CREATE TABLE {schema_name}.{src_nm}_{dataset_nm}_{table_name} (\n" +
        ",\n".join(columns_sql) +
        "\n);"
    )
    return sql_script


@log_function
def create_insert_statement(table_name: str, df: pd.DataFrame) -> str:
    if df.empty:
        return f"-- No data to insert into {table_name}"

    columns = ", ".join(df.columns)
    values = ",\n".join(
        f"({', '.join(repr(v) if pd.notna(v) else 'NULL' for v in row)})"
        for row in df.itertuples(index=False, name=None)
    )
    return f"INSERT INTO {table_name} ({columns}) VALUES\n{values};"


@log_function
def create_update_statement(
    table_name: str, df: pd.DataFrame, where_keys: list
) -> str:
    if df.empty:
        return f"-- No data to update in {table_name}"

    update_queries = []

    for _, row in df.iterrows():
        set_clauses = []
        where_clauses = []

        for col in df.columns:
            val = row[col]
            val_str = f"'{val}'" if pd.notna(val) else "NULL"
            if col in where_keys:
                where_clauses.append(f"{col} = {val_str}")
            else:
                set_clauses.append(f"{col} = {val_str}")

        if not set_clauses or not where_clauses:
            continue

        query = (
            f"UPDATE {table_name} SET {', '.join(set_clauses)} "
            f"WHERE {' AND '.join(where_clauses)};"
        )
        update_queries.append(query)

    return "\n".join(update_queries)


@log_function
def generate_insert_statements(
    src_nm, dataset_nm, table_nm, df_dataset_info, df_pre_proc_info,
    df_table_info, df_metadata_df
) -> str:
    insert_statements = []
    update_statements = []

    if db.check_existence(src_nm, dataset_nm, table_nm):
        update_statements.append(
            create_update_statement(
                "app_mgmt.sys_config_dataset_info", df_dataset_info,
                ["src_nm", "dataset_nm"]
            )
        )
        update_statements.append(
            create_update_statement(
                "app_mgmt.sys_config_pre_proc_info", df_pre_proc_info,
                ["src_nm", "dataset_nm"]
            )
        )
        update_statements.append(
            create_update_statement(
                "app_mgmt.sys_config_table_info", df_table_info,
                ["src_nm", "dataset_nm"]
            )
        )
        update_statements.append(
            create_update_statement(
                "app_mgmt.sys_config_table_field_info", df_metadata_df,
                ["src_nm", "src_table_nm"]
            )
        )

        st.session_state.rds_sql_script = "\n\n".join(update_statements)

    else:
        insert_statements.append(
            create_insert_statement(
                "app_mgmt.sys_config_dataset_info", df_dataset_info
            )
        )
        insert_statements.append(
            create_insert_statement(
                "app_mgmt.sys_config_pre_proc_info", df_pre_proc_info
            )
        )
        insert_statements.append(
            create_insert_statement(
                "app_mgmt.sys_config_table_info", df_table_info
            )
        )
        insert_statements.append(
            create_insert_statement(
                "app_mgmt.sys_config_table_field_info", df_metadata_df
            )
        )

        st.session_state.rds_sql_script = "\n\n".join(insert_statements)

    return st.session_state.rds_sql_script
