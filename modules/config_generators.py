import logging
import os
import pandas as pd
from .config import config
from modules.logging_setup import log_function

logger = logging.getLogger(__name__)

"""
Functions to generate system configuration dataframes for dataset, pre-processing, and table information.
"""

@log_function
def _get_table_conf(table_name):
    for tbl in config["tables"]:
        if tbl["name"] == table_name:
            return tbl
    raise ValueError(f"Table config not found for {table_name}")


@log_function
def generate_sys_config_dataset_info(src_nm, dataset_nm, dialect, warehouse_nm):
    """
    Generate sys_config_dataset_info dataframe.
    """
    logger.debug(f"Generating sys_config_dataset_info for src={src_nm}, dataset={dataset_nm}")
    table_conf = _get_table_conf("sys_config_dataset_info")
    row = dict(table_conf.get("defaults", {}))
    row.update({
        "src_nm": src_nm,
        "dataset_nm": dataset_nm,
        "trgt_dw_list": dialect,
        "cmput_whse_nm": warehouse_nm
    })
    return pd.DataFrame([row], columns=table_conf["columns"])


@log_function
def generate_sys_config_pre_proc_info(src_nm, dataset_nm, fmt_type_cd):
    """
    Generate sys_config_pre_proc_info dataframe.
    """
    logger.debug(f"Generating sys_config_pre_proc_info for src={src_nm}, dataset={dataset_nm}")
    table_conf = _get_table_conf("sys_config_pre_proc_info")
    row = dict(table_conf.get("defaults", {}))
    row.update({
        "src_nm": src_nm,
        "dataset_nm": dataset_nm,
        "fmt_type_cd": fmt_type_cd
    })
    return pd.DataFrame([row], columns=table_conf["columns"]