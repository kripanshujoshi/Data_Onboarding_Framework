import boto3
import json
import psycopg2
import psycopg2.extras
import uuid
from datetime import datetime
import streamlit as st
import pandas as pd
from .storage import S3Helper
# Add config import
from .config import get_config

# Database connection functions
def get_secret(secret_name, region_name="us-east-1"):
    """Retrieve database credentials from AWS Secrets Manager"""
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

def get_postgres_connection():
    """Create and return a PostgreSQL connection"""
    # Use config module instead of direct file load
    config = get_config()
    
    db_config = config['database']
    
    # Get credentials from Secrets Manager
    secret = get_secret(db_config['secret_name'], db_config['region'])
    
    # Create connection
    conn = psycopg2.connect(
        host=db_config['host'],
        dbname=db_config['dbname'],
        user=secret['username'],
        password=secret['password'],
        port=db_config['port']
    )
    
    return conn

# SQL Requests Management
def initialize_sql_requests_table():
    """Create metadata_onboarding_requests table if it doesn't exist"""
    conn = get_postgres_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata_onboarding_requests (
                id SERIAL PRIMARY KEY,
                created_by VARCHAR(255) NOT NULL,
                dataset_name VARCHAR(255) NOT NULL,
                request_id UUID NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                s3_prefix TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                approved_by VARCHAR(255),
                approved_at TIMESTAMP,
                rejection_reason TEXT
            );
        """)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def submit_sql_request(user, dataset, request_id, s3_prefix):
    """Insert a new SQL request record"""
    conn = get_postgres_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO metadata_onboarding_requests 
            (created_by, dataset_name, request_id, s3_prefix) 
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """, (user, dataset, request_id, s3_prefix))
        request_db_id = cursor.fetchone()[0]
        conn.commit()
        return True, request_db_id
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def get_pending_requests():
    """Get all pending SQL requests"""
    conn = get_postgres_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cursor.execute("""
            SELECT id, created_by, dataset_name, request_id, status, 
                   s3_prefix, created_at, approved_by, approved_at 
            FROM metadata_onboarding_requests 
            WHERE status = 'pending'
            ORDER BY created_at DESC;
        """)
        return cursor.fetchall()
    except Exception as e:
        return []
    finally:
        cursor.close()
        conn.close()

def get_all_requests():
    """Get all SQL requests regardless of status"""
    conn = get_postgres_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cursor.execute("""
            SELECT id, created_by, dataset_name, request_id, status, 
                   s3_prefix, created_at, approved_by, approved_at,
                   rejection_reason
            FROM metadata_onboarding_requests 
            ORDER BY created_at DESC;
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def approve_request(request_id, approver):
    """Mark a request as approved"""
    conn = get_postgres_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE metadata_onboarding_requests 
            SET status = 'approved', 
                approved_by = %s, 
                approved_at = CURRENT_TIMESTAMP
            WHERE request_id = %s AND status = 'pending'
            RETURNING id;
        """, (approver, request_id))
        result = cursor.fetchone()
        conn.commit()
        return result is not None
    except Exception as e:
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def reject_request(request_id, rejection_reason):
    """Mark a request as rejected"""
    conn = get_postgres_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE metadata_onboarding_requests 
            SET status = 'rejected',
                rejection_reason = %s
            WHERE request_id = %s AND status = 'pending'
            RETURNING id;
        """, (rejection_reason, request_id))
        result = cursor.fetchone()
        conn.commit()
        return result is not None
    except Exception as e:
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_request_by_id(request_id):
    """Get SQL request details by ID"""
    conn = get_postgres_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cursor.execute("""
            SELECT id, created_by, dataset_name, request_id, status, 
                   s3_prefix, created_at, approved_by, approved_at,
                   rejection_reason
            FROM metadata_onboarding_requests 
            WHERE request_id = %s;
        """, (request_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

# Database Onboarding Specific Functions
def generate_sql_scripts(dataset_info, fields):
    """Generate SQL scripts for data onboarding"""
    # Generate landing table DDL
    land_ddl = f"-- Landing table DDL for {dataset_info['name']}\n"
    land_ddl += f"CREATE TABLE landing.{dataset_info['name']} (\n"
    for i, field in enumerate(fields):
        nullable = "" if field['nullable'] == "YES" else "NOT NULL"
        land_ddl += f"    {field['name']} {field['type']} {nullable}"
        if i < len(fields) - 1:
            land_ddl += ","
        land_ddl += "\n"
    land_ddl += ");\n"
    
    # Generate staging table DDL
    stage_ddl = f"-- Staging table DDL for {dataset_info['name']}\n"
    stage_ddl += f"CREATE TABLE staging.{dataset_info['name']} (\n"
    for i, field in enumerate(fields):
        nullable = "" if field['nullable'] == "YES" else "NOT NULL"
        stage_ddl += f"    {field['name']} {field['type']} {nullable}"
        if i < len(fields) - 1:
            stage_ddl += ","
        land_ddl += "\n"
    stage_ddl += ");\n"
    
    # Generate metadata DDL
    metadata_ddl = f"-- Metadata for {dataset_info['name']}\n"
    metadata_ddl += "INSERT INTO sys_config_datasets\n"
    metadata_ddl += "(dataset_name, source_system, data_owner, refresh_frequency, data_classification, retention_period, description)\n"
    metadata_ddl += f"VALUES ('{dataset_info['name']}', '{dataset_info['source_system']}', '{dataset_info['data_owner']}', "
    metadata_ddl += f"'{dataset_info['refresh_frequency']}', '{dataset_info['data_classification']}', {dataset_info['retention_period']}, "
    metadata_ddl += f"'{dataset_info['description']}');\n\n"
    
    metadata_ddl += "INSERT INTO sys_config_fields\n"
    metadata_ddl += "(dataset_name, field_name, field_type, is_nullable, is_primary_key, description)\n"
    metadata_ddl += "VALUES\n"
    for i, field in enumerate(fields):
        nullable = "true" if field['nullable'] == "YES" else "false"
        is_pk = "true" if field['primary_key'] else "false"
        metadata_ddl += f"('{dataset_info['name']}', '{field['name']}', '{field['type']}', {nullable}, {is_pk}, '{field['description']}')"
        if i < len(fields) - 1:
            metadata_ddl += ",\n"
        else:
            metadata_ddl += ";\n"
    
    return land_ddl, stage_ddl, metadata_ddl

def submit_onboarding_request(username, dataset_info, fields):
    """Submit a complete onboarding request"""
    try:
        # Use config module instead of direct file load
        config = get_config()
        
        # Initialize S3 helper
        s3_helper = S3Helper(config['s3_bucket'], config['s3_root_prefix'])
        
        # Generate SQL scripts
        land_ddl, stage_ddl, metadata_ddl = generate_sql_scripts(dataset_info, fields)
        
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        dataset_name = dataset_info['name']
        
        # Upload scripts to S3
        land_result, land_path = s3_helper.put_script(
            request_id, dataset_name, "land_ddl", land_ddl)
        stage_result, stage_path = s3_helper.put_script(
            request_id, dataset_name, "stage_ddl", stage_ddl)
        meta_result, meta_path = s3_helper.put_script(
            request_id, dataset_name, "metadata_ddl", metadata_ddl)
        
        if land_result and stage_result and meta_result:
            # Store request in database
            s3_prefix = f"{config['s3_root_prefix']}/pending/{request_id}"
            success, req_id = submit_sql_request(
                username, dataset_name, request_id, s3_prefix)
            
            if success:
                return True, request_id, {"land_ddl": land_ddl, "stage_ddl": stage_ddl, "metadata_ddl": metadata_ddl}
            else:
                return False, f"Failed to submit request to database: {req_id}", None
        else:
            return False, "Failed to upload scripts to S3", None
    except Exception as e:
        return False, f"Error submitting request: {str(e)}", None
