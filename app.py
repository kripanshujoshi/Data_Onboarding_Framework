"""
Streamlit application for Data Onboarding Framework UI and workflow orchestration.
"""
import logging
import streamlit as st
import json
import traceback
from modules.logging_setup import setup_logging
from modules import db, onboarding_service

# Initialize logging at application start
setup_logging()
logger = logging.getLogger(__name__)

# Load configuration file
try:
    with open("configs/config.json") as f:
        config = json.load(f)
    logger.info("Configuration loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise

st.title("Data Onboarding Tool")

# Input fields
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    src_nm = st.text_input(
        "Source Name", placeholder="e.g. fin_user, smrt_fctry, comrcl_user"
    )
    fmt_type_cd = st.selectbox(
        "Format Type",
        ["csv", "excel", "txt", "zip", "json", "parquet", "orc"]
    )
with col2:
    domn_nm = st.text_input(
        "Domain Name",
        placeholder="e.g. sales_prfmnc_eval, mktg_start_plan, info_sec_mgmt"
    )
    delmtr_cd = st.text_input("Delimiter Code")
with col3:
    dataset_nm = st.text_input(
        "Dataset Name",
        placeholder="e.g. sales_prfmnc_eval, mktg_start_plan, info_sec_mgmt"
    )
    dprct_methd_cd = st.selectbox(
        "Deprecation Method",
        [
            "okrdra", "orrrra", "okkkra", "okkkra_extrctr",
            "okkkka", "file_cntl_upsrt_repl"
        ]
    )
with col4:
    table_nm = st.text_input("Table Name")
    data_clasfctn_nm = st.selectbox(
        "Data Classification Name", ["confd", "intrnl"]
    )
with col5:
    dialect = st.selectbox(
        "Target Warehouse", ["Snowflake", "Redshift"]
    )
    warehouse_nm = st.selectbox(
        "Compute Role",
        [
            "keu_it_small", "keu_fin_small", "keu_elt_analytic_small",
            "keu_elt_supplychain_small"
        ]
    )

uploaded_file = st.file_uploader(
    "Upload File (CSV, ZIP, or Excel)", type=["xlsx", "csv", "zip"]
)

# Session state initialization
if "template_generated" not in st.session_state:
    st.session_state.template_generated = False
if "metadata_df" not in st.session_state:
    st.session_state.metadata_df = None
if "sheets_data" not in st.session_state:
    st.session_state.sheets_data = {}
if "sql_generated" not in st.session_state:
    st.session_state.sql_generated = False

# Generate Template
generate_template = st.button("Generate Template")
if generate_template:
    logger.info("Generate Template button clicked.")
    try:
        if uploaded_file is None:
            st.error("Upload Sample Data File")
            st.session_state.template_generated = False
        elif db.check_existence(src_nm, dataset_nm, table_nm):
            st.warning(
                "Existing configurations found. Kindly validate before proceeding."
            )
            st.session_state.template_generated = True
        else:
            st.session_state.template_generated = True
    except Exception as e:
        st.error(str(e))
        st.text(traceback.format_exc())
        logger.error(f"Error during template generation: {e}")

if st.session_state.template_generated:
    if db.check_existence(src_nm, dataset_nm, table_nm):
        st.session_state.metadata_df = onboarding_service.get_table_field_info(
            src_nm, table_nm
        )
        st.session_state.sys_config_dataset_info = onboarding_service.get_dataset_info(
            src_nm, dataset_nm
        )
        st.session_state.sys_config_pre_proc_info = onboarding_service.get_pre_proc_info(
            src_nm, dataset_nm
        )
        st.session_state.sys_config_table_info = onboarding_service.get_table_info(
            src_nm, dataset_nm
        )
    else:
        (
            metadata_df,
            sys_config_dataset_info,
            sys_config_pre_proc_info,
            sys_config_table_info,
        ) = onboarding_service.generate_templates(
            uploaded_file,
            src_nm,
            domn_nm,
            dataset_nm,
            table_nm,
            data_clasfctn_nm,
            fmt_type_cd,
            delmtr_cd,
            dprct_methd_cd,
            dialect,
            warehouse_nm,
        )
        st.session_state.metadata_df = metadata_df
        st.session_state.sys_config_dataset_info = sys_config_dataset_info
        st.session_state.sys_config_pre_proc_info = sys_config_pre_proc_info
        st.session_state.sys_config_table_info = sys_config_table_info
    st.success("Metadata extraction complete.")
    logger.info("Metadata extraction complete.")
    sheet_names = [
        "sys_config_dataset_info",
        "sys_config_pre_proc_info",
        "sys_config_table_info",
        "sys_config_table_field_info",
    ]
    tab1, tab2, tab3, tab4 = st.tabs(sheet_names)

    def update_dataset_info():
        st.write("update dataset info - called!")
        st.write(st.session_state.get("sys_config_dataset_info_edit"))
        st.session_state.sys_config_dataset_info = st.session_state.sys_config_dataset_info_edit

    def update_pre_proc_info():
        st.session_state.sys_config_proc_info = st.session_state.sys_config_pre_proc_info_edit

    def update_table_info():
        st.session_state.sys_config_table_info = st.session_state.sys_config_table_info_edit

    def update_field_info():
        st.session_state.metadata_df = st.session_state.sys_config_table_field_info_edit

    with tab1:
        st.write(f"### {sheet_names[0]}")
        dataset_serv_now_priorty_cd = ["P1", "P2", "P3", "P4", "P5"]
        dataset_lake_load_enbl_flg = ["Y", "N"]
        dataset_trgt_dw_list = [
            "snowflake", "redshift", "redshift|snowflake"
        ]
        dataset_manl_upld_flg = ["Y", "N"]
        dataset_whse_load_enbl_flg = ["Y", "N"]

        st.data_editor(
            st.session_state.sys_config_dataset_info,
            num_rows="dynamic",  # Allows adding new rows
            key="sys_config_dataset_info_edit",
            column_config={
                "serv_now_priorty_cd": st.column_config.SelectboxColumn(
                    "serv_now_priorty_cd",
                    options=dataset_serv_now_priorty_cd,
                    required=True,
                ),
                "load_enbl_flg": st.column_config.SelectboxColumn(
                    "load_enbl_flg",
                    options=dataset_lake_load_enbl_flg,
                    required=True,
                ),
                "trgt_dw_list": st.column_config.SelectboxColumn(
                    "trgt_dw_list",
                    options=dataset_trgt_dw_list,
                    required=True,
                ),
                "manl_upld_flg": st.column_config.SelectboxColumn(
                    "manl_upld_flg",
                    options=dataset_manl_upld_flg,
                    required=True,
                ),
            },
            on_change=update_dataset_info,
        )

    with tab2:
        st.write(f"### {sheet_names[1]}")
        st.data_editor(
            st.session_state.sys_config_pre_proc_info,
            num_rows="dynamic",  # Allows adding new rows
            key="sys_config_pre_proc_info_edit",
            on_change=update_pre_proc_info,
        )

    with tab3:
        st.write(f"### {sheet_names[2]}")
        st.data_editor(
            st.session_state.sys_config_table_info,
            num_rows="dynamic",  # Allows adding new rows
            key="sys_config_table_info_edit",
            on_change=update_table_info,
        )

    with tab4:
        st.write(f"### {sheet_names[3]}")
        st.data_editor(
            st.session_state.metadata_df,
            num_rows="dynamic",  # Allows adding new rows
            key="sys_config_table_field_info_edit",
            on_change=update_field_info,
        )

# Generate SQL Scripts
if st.session_state.template_generated:
    generate_sql_button = st.button("Generate SQL Scripts")
    if generate_sql_button:
        logger.info("Generate SQL Scripts button clicked.")
        try:
            if st.session_state.metadata_df.empty:
                st.error("Metadata DataFrame is empty! SQL cannot be generated.")
                logger.warning(
                    "Metadata DataFrame is empty! SQL cannot be generated."
                )
            else:
                (
                    land_sql_script,
                    stage_sql_script,
                    rds_sql_script,
                ) = onboarding_service.generate_sql_scripts(
                    st.session_state.metadata_df,
                    src_nm,
                    dataset_nm,
                    table_nm,
                    st.session_state.sys_config_dataset_info,
                    st.session_state.sys_config_pre_proc_info,
                    st.session_state.sys_config_table_info,
                )
                st.session_state.land_sql_script = land_sql_script
                st.session_state.stage_sql_script = stage_sql_script
                st.session_state.rds_sql_script = rds_sql_script
                st.session_state.sql_generated = True
                logger.info("SQL scripts generated successfully.")
        except Exception as e:
            st.error(f"SQL generation failed: {e}")
            st.text(traceback.format_exc())
            logger.error(f"SQL generation failed: {e}")

if st.session_state.sql_generated:
    sheet_names_sql = ["Land DDL", "Stage DDL", "RDS Config Entries"]
    tab1, tab2, tab3 = st.tabs(sheet_names_sql)
    with tab1:
        st.text_area(
            "Generated Land DDL Scripts",
            st.session_state.land_sql_script,
            height=200,
        )
    with tab2:
        st.text_area(
            "Generated Stage DDL Scripts",
            st.session_state.stage_sql_script,
            height=200,
        )
    with tab3:
        edited = False
        if "sys_config_dataset_info_edit" in st.session_state:
            edited_rows = st.session_state.sys_config_dataset_info_edit.get(
                "edited_rows", {}
            )
            for idx, changes in edited_rows.items():
                for col, value in changes.items():
                    st.session_state.sys_config_dataset_info.at[int(idx), col] = value
                    edited = True

        if "sys_config_pre_proc_info_edit" in st.session_state:
            edited_rows = st.session_state.sys_config_pre_proc_info_edit.get(
                "edited_rows", {}
            )
            for idx, changes in edited_rows.items():
                for col, value in changes.items():
                    st.session_state.sys_config_pre_proc_info.at[int(idx), col] = value
                    edited = True

        if "sys_config_table_info_edit" in st.session_state:
            edited_rows = st.session_state.sys_config_table_info_edit.get(
                "edited_rows", {}
            )
            for idx, changes in edited_rows.items():
                for col, value in changes.items():
                    st.session_state.sys_config_table_info.at[int(idx), col] = value
                    edited = True

        if "sys_config_table_field_info_edit" in st.session_state:
            edited_rows = st.session_state.sys_config_table_field_info_edit.get(
                "edited_rows", {}
            )
            for idx, changes in edited_rows.items():
                for col, value in changes.items():
                    st.session_state.metadata_df.at[int(idx), col] = value
                    edited = True
        if edited:
            _, _, rds_sql_script = onboarding_service.generate_sql_scripts(
                st.session_state.metadata_df,
                src_nm,
                dataset_nm,
                table_nm,
                st.session_state.sys_config_dataset_info,
                st.session_state.sys_config_pre_proc_info,
                st.session_state.sys_config_table_info,
            )
            st.session_state.rds_sql_script = rds_sql_script
        st.text_area(
            "Generated RDS Scripts",
            st.session_state.rds_sql_script,
            height=200,
        )

    col1, col2, col3 = st.columns(3)
    with col1:
        download_button_clicked = st.button("Download Files", use_container_width=True)
    with col2:
        git_push_clicked = st.button("GIT Push", use_container_width=True)
    with col3:
        insert_into_rds_clicked = st.button("Insert into RDS", use_container_width=True)

    if git_push_clicked:
        logger.info("GIT Push button clicked.")
        try:
            scripts = {
                f"{src_nm}_{dataset_nm}_land.sql": st.session_state.land_sql_script,
                f"{src_nm}_{dataset_nm}_stage.sql": st.session_state.stage_sql_script,
                f"{src_nm}_{dataset_nm}_rds.sql": st.session_state.rds_sql_script,
            }
            onboarding_service.git_push_scripts(scripts, src_nm, dataset_nm)
            st.success("Git Code Push Successful and PR raised")
            logger.info("Git Code Push Successful and PR raised.")
        except Exception as e:
            st.error(str(e))
            logger.error(f"GIT Push failed: {e}")
    if download_button_clicked:
        logger.info("Download Files button clicked.")
        try:
            scripts = {
                f"{src_nm}_{dataset_nm}_land.sql": st.session_state.land_sql_script,
                f"{src_nm}_{dataset_nm}_stage.sql": st.session_state.stage_sql_script,
                f"{src_nm}_{dataset_nm}_rds.sql": st.session_state.rds_sql_script,
            }
            output = onboarding_service.prepare_zip(scripts, src_nm, dataset_nm)
            st.download_button(
                label="Download Files",
                data=output,
                file_name=f"{src_nm}_{dataset_nm}_Onboarding_Files.zip",
                mime="application/zip",
            )
            logger.info("Files downloaded successfully.")
        except Exception as e:
            st.error(str(e))
            logger.error(f"File download failed: {e}")
    if insert_into_rds_clicked:
        logger.info("Insert into RDS button clicked.")
        try:
            success = onboarding_service.insert_into_rds(
                st.session_state.rds_sql_script
            )
            if success:
                st.success("Insert statements executed successfully in PostgreSQL.")
                logger.info("Insert statements executed successfully in PostgreSQL.")
        except Exception as e:
            st.error(str(e))
            logger.error(f"Insert into RDS failed: {e}")
