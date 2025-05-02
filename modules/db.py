import json
import logging
import boto3
import psycopg2
import pandas as pd
from botocore.exceptions import ClientError
from modules.config import config
from modules.logging_setup import log_function

logger = logging.getLogger(__name__)

# Load database configuration
DB_CONFIG = config.get('database', {})
SECRET_NAME = DB_CONFIG.get('secret_name')
REGION_NAME = DB_CONFIG.get('region')
HOST = DB_CONFIG.get('host')
DBNAME = DB_CONFIG.get('dbname')
PORT = DB_CONFIG.get('port')


@log_function
def get_db_credentials() -> dict:
    """
    Retrieve database credentials from AWS Secrets Manager.
    """
    logger.debug(f"Fetching DB credentials from Secrets Manager: {SECRET_NAME}")
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=REGION_NAME)
    try:
        secret_value = client.get_secret_value(SecretId=SECRET_NAME)
        secret_dict = json.loads(secret_value["SecretString"])
        logger.info("Database credentials retrieved successfully.")
        return secret_dict
    except ClientError as e:
        logger.error(f"Error fetching secrets: {e}")
        raise Exception(f"Error fetching secrets: {e}")


@log_function
def check_db_connection() -> psycopg2.extensions.connection:
    """
    Establish and return a new database connection.
    """
    creds = get_db_credentials()
    try:
        conn = psycopg2.connect(
            user=creds.get("username"),
            password=creds.get("password"),
            host=HOST,
            dbname=DBNAME,
            port=PORT
        )
        logger.debug("Database connection established.")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise Exception(f"Failed to connect to database: {e}")


@log_function
def fetch_dataframe(query: str, params=None) -> pd.DataFrame:
    """
    Execute a SELECT query and return results as a pandas DataFrame.
    """
    conn = check_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            result = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            logger.debug(f"Query executed: {query}")
            return pd.DataFrame(result, columns=columns)
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        raise Exception(f"Error fetching data: {e}")
    finally:
        conn.close()


@log_function
def insert_statements_into_postgres(sql_script: str) -> bool:
    """
    Execute DDL/DML SQL script against the database.
    """
    conn = check_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql_script)
            conn.commit()
            logger.info("SQL script executed successfully.")
            return True
    except Exception as e:
        logger.error(f"Error executing SQL: {e}")
        raise Exception(f"Error executing SQL: {e}")
    finally:
        conn.close()


@log_function
def check_existence(src_nm: str, dataset_nm: str, src_table_nm: str) -> bool:
    """
    Check if configuration entries already exist in the database.
    Returns True if any records found.
    """
    conn = check_db_connection()
    try:
        with conn.cursor() as cur:
            queries = [
                (
                    "SELECT 1 FROM app_mgmt.sys_config_dataset_info WHERE src_nm = %s AND dataset_nm = %s",
                    (src_nm, dataset_nm),
                ),
                (
                    "SELECT 1 FROM app_mgmt.sys_config_table_info WHERE src_nm = %s AND dataset_nm = %s",
                    (src_nm, dataset_nm),
                ),
                (
                    "SELECT 1 FROM app_mgmt.sys_config_table_field_info WHERE src_nm = %s AND src_table_nm = %s",
                    (src_nm, src_table_nm),
                ),
                (
                    "SELECT 1 FROM app_mgmt.sys_config_pre_proc_info WHERE src_nm = %s AND dataset_nm = %s",
                    (src_nm, dataset_nm),
                ),
            ]
            for q, params in queries:
                cur.execute(q, params)
                if cur.fetchone():
                    logger.info(
                        f"Configuration exists for src={src_nm}, dataset={dataset_nm}, "
                        f"table={src_table_nm}"
                    )
                    return True
            return False
    except Exception as e:
        logger.error(f"Error checking existence: {e}")
        raise Exception(f"Error checking existence: {e}")
    finally:
        conn.close()
