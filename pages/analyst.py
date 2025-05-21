import streamlit as st
import pandas as pd
import sys
import os

# Update import to use modules
from modules.database import get_postgres_connection

# Check authentication
if "username" not in st.session_state:
    st.error("Please login first")
    st.stop()

# Verify role
if st.session_state.role not in ["analyst", "admin"]:
    st.error("You don't have permission to access this page")
    st.stop()

st.title("Configuration Explorer")

# Search functionality
search_term = st.text_input("Search for datasets", "")

# Query to get datasets
def get_datasets(search):
    conn = get_postgres_connection()
    cursor = conn.cursor()
    if search:
        cursor.execute("""
            SELECT * FROM sys_config_datasets 
            WHERE dataset_name ILIKE %s 
            OR source_system ILIKE %s 
            OR description ILIKE %s
            ORDER BY dataset_name;
        """, (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("SELECT * FROM sys_config_datasets ORDER BY dataset_name;")
    
    columns = [desc[0] for desc in cursor.description]
    datasets = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return pd.DataFrame(datasets, columns=columns)

# Query to get fields for a dataset
def get_fields(dataset_name):
    conn = get_postgres_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM sys_config_fields 
        WHERE dataset_name = %s
        ORDER BY field_name;
    """, (dataset_name,))
    
    columns = [desc[0] for desc in cursor.description]
    fields = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return pd.DataFrame(fields, columns=columns)

# Get datasets based on search term
datasets_df = get_datasets(search_term)

if datasets_df.empty:
    st.info(f"No datasets found matching '{search_term}'")
else:
    st.write(f"Found {len(datasets_df)} datasets")
    
    # Display datasets
    st.subheader("Datasets")
    st.dataframe(datasets_df, use_container_width=True)
    
    # Allow selecting a dataset to view fields
    selected_dataset = st.selectbox("Select a dataset to view fields", 
                                   [""] + datasets_df['dataset_name'].tolist())
    
    if selected_dataset:
        # Get fields for the selected dataset
        fields_df = get_fields(selected_dataset)
        
        # Display fields
        st.subheader(f"Fields for {selected_dataset}")
        st.dataframe(fields_df, use_container_width=True)
        
        # Show DDL preview
        if not fields_df.empty:
            with st.expander("DDL Preview"):
                # Generate DDL based on the fields
                ddl = f"-- DDL for {selected_dataset}\n"
                ddl += f"CREATE TABLE staging.{selected_dataset} (\n"
                
                for i, row in fields_df.iterrows():
                    nullable = "" if row['is_nullable'] else "NOT NULL"
                    ddl += f"    {row['field_name']} {row['field_type']} {nullable}"
                    if i < len(fields_df) - 1:
                        ddl += ","
                    ddl += "\n"
                
                ddl += ");\n"
                
                st.code(ddl, language="sql")
