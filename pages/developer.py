import streamlit as st
import json
import pandas as pd
import sys
import os
from datetime import datetime

# Update import to use modules
from modules.database import submit_onboarding_request
from modules.storage import S3Helper  # If directly used

# Check authentication
if "username" not in st.session_state:
    st.error("Please login first")
    st.stop()

# Verify role
if st.session_state.role not in ["developer", "admin"]:
    st.error("You don't have permission to access this page")
    st.stop()

# Page title
st.title("Data Onboarding Request")

# Create tabs for different steps
tab1, tab2, tab3 = st.tabs(["Dataset Information", "Field Mapping", "Generate & Submit"])

with tab1:
    st.header("Dataset Information")
    
    # Dataset details form
    with st.form("dataset_info"):
        col1, col2 = st.columns(2)
        with col1:
            dataset_name = st.text_input("Dataset Name", help="Name of the dataset (lowercase, underscore separated)")
            source_system = st.text_input("Source System", help="Name of the source system")
            data_owner = st.text_input("Data Owner Email", help="Email of the person responsible for this data")
        
        with col2:
            refresh_frequency = st.selectbox("Refresh Frequency", 
                                           ["daily", "weekly", "monthly", "quarterly", "yearly", "one-time"])
            data_classification = st.selectbox("Data Classification", 
                                             ["public", "internal", "confidential", "restricted"])
            retention_period = st.selectbox("Retention Period (days)", 
                                          [30, 60, 90, 180, 365, 730, 1095, 1825])
        
        data_description = st.text_area("Dataset Description", 
                                      help="Detailed description of what this dataset contains and its purpose")
        
        submitted = st.form_submit_button("Save and Continue")
        if submitted:
            # Save to session state
            st.session_state.dataset_info = {
                "name": dataset_name,
                "source_system": source_system,
                "data_owner": data_owner,
                "refresh_frequency": refresh_frequency,
                "data_classification": data_classification,
                "retention_period": retention_period,
                "description": data_description
            }
            st.success("Dataset information saved. Proceed to Field Mapping.")

with tab2:
    st.header("Field Mapping")
    
    if 'field_mappings' not in st.session_state:
        st.session_state.field_mappings = []
    
    with st.form("add_field"):
        cols = st.columns(4)
        with cols[0]:
            field_name = st.text_input("Field Name", help="Name of the field in source data")
        with cols[1]:
            data_type = st.selectbox("Data Type", 
                                    ["VARCHAR", "INTEGER", "DECIMAL", "DATE", "TIMESTAMP", "BOOLEAN"])
        with cols[2]:
            if data_type == "VARCHAR":
                length = st.number_input("Length", min_value=1, value=255)
            elif data_type == "DECIMAL":
                precision = st.number_input("Precision", min_value=1, value=18)
                scale = st.number_input("Scale", min_value=0, value=2)
                length = f"({precision},{scale})"
            else:
                length = ""
        with cols[3]:
            is_nullable = st.checkbox("Nullable", value=True)
            is_pk = st.checkbox("Primary Key")
        
        field_description = st.text_area("Field Description", help="Description of what this field represents")
        
        submitted = st.form_submit_button("Add Field")
        if submitted:
            field_type = data_type if length == "" else f"{data_type}{length}"
            new_field = {
                "name": field_name,
                "type": field_type,
                "nullable": "YES" if is_nullable else "NO",
                "primary_key": is_pk,
                "description": field_description
            }
            st.session_state.field_mappings.append(new_field)
            st.success(f"Field {field_name} added!")
    
    # Display current mappings
    if st.session_state.field_mappings:
        st.subheader("Current Field Mappings")
        df = pd.DataFrame(st.session_state.field_mappings)
        st.dataframe(df)
        
        if st.button("Clear All Fields"):
            st.session_state.field_mappings = []
            st.experimental_rerun()

with tab3:
    st.header("Generate & Submit SQL Scripts")
    
    if 'dataset_info' not in st.session_state or not st.session_state.field_mappings:
        st.warning("Please complete the Dataset Information and Field Mapping sections first")
    else:
        # Generate and submit button
        if st.button("Generate & Submit Request"):
            success, message, scripts = submit_onboarding_request(
                st.session_state.username,
                st.session_state.dataset_info,
                st.session_state.field_mappings
            )
            
            if success:
                st.success(f"Request submitted successfully! Request ID: {message}")
                
                # Show preview of scripts
                with st.expander("Preview Generated Scripts"):
                    st.subheader("Landing Table DDL")
                    st.code(scripts["land_ddl"], language="sql")
                    
                    st.subheader("Staging Table DDL")
                    st.code(scripts["stage_ddl"], language="sql")
                    
                    st.subheader("Metadata DDL")
                    st.code(scripts["metadata_ddl"], language="sql")
                
                # Clear session state for a new request
                if st.button("Start New Request"):
                    for key in ['dataset_info', 'field_mappings']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.experimental_rerun()
            else:
                st.error(message)
