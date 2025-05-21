import streamlit as st
import pandas as pd
import json
import sys
import os
from datetime import datetime

# Update imports to use modules
from modules.database import get_pending_requests, approve_request, reject_request
from modules.storage import S3Helper

# Check authentication
if "username" not in st.session_state:
    st.error("Please login first")
    st.stop()

# Verify role
if st.session_state.role not in ["approver", "admin"]:
    st.error("You don't have permission to access this page")
    st.stop()

# Load configuration
with open('configs/config.json', 'r') as config_file:
    config = json.load(config_file)

# Initialize S3 helper
s3_helper = S3Helper(config['s3_bucket'], config['s3_root_prefix'])

st.title("Approval Queue")

# Get pending requests
pending_requests = get_pending_requests()

if not pending_requests:
    st.info("No pending requests found")
else:
    # Convert to DataFrame for display
    df = pd.DataFrame(pending_requests)
    # Format datetime for display
    df['created_at'] = df['created_at'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
    
    st.write(f"Found {len(df)} pending requests")
    
    # Display requests in a table
    st.dataframe(df[['id', 'created_by', 'dataset_name', 'created_at']], use_container_width=True)
    
    # Allow selecting a request to review
    selected_request_id = st.selectbox("Select a request to review", 
                                       [""] + [str(row['id']) for row in pending_requests])
    
    if selected_request_id:
        # Find the selected request
        selected_request = next((r for r in pending_requests if str(r['id']) == selected_request_id), None)
        
        if selected_request:
            st.subheader(f"Review Request #{selected_request['id']}")
            
            st.write(f"**Dataset:** {selected_request['dataset_name']}")
            st.write(f"**Created by:** {selected_request['created_by']}")
            st.write(f"**Created at:** {selected_request['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Fetch SQL scripts from S3
            request_id = selected_request['request_id']
            
            # Fetch landing DDL
            land_success, land_ddl = s3_helper.get_script(request_id, "land_ddl", "pending")
            # Fetch staging DDL
            stage_success, stage_ddl = s3_helper.get_script(request_id, "stage_ddl", "pending")
            # Fetch metadata DDL
            meta_success, meta_ddl = s3_helper.get_script(request_id, "metadata_ddl", "pending")
            
            if land_success and stage_success and meta_success:
                with st.expander("Landing Table DDL", expanded=True):
                    st.code(land_ddl, language="sql")
                
                with st.expander("Staging Table DDL", expanded=True):
                    st.code(stage_ddl, language="sql")
                
                with st.expander("Metadata DDL", expanded=True):
                    st.code(meta_ddl, language="sql")
                
                # Approval / Rejection form
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Approve", type="primary"):
                        # Update request status in database
                        if approve_request(request_id, st.session_state.username):
                            # Move scripts to approved folder
                            move_success, message = s3_helper.move_scripts(request_id, "pending", "approved")
                            
                            if move_success:
                                st.success(f"Request #{selected_request['id']} approved successfully!")
                                # Here you would add code to execute the SQL against your databases
                                # This is where you'd call your existing execution routines
                                st.experimental_rerun()
                            else:
                                st.error(f"Error moving scripts to approved folder: {message}")
                        else:
                            st.error("Error updating request status in database")
                
                with col2:
                    # Rejection reason input
                    rejection_reason = st.text_area("Rejection Reason (required if rejecting)")
                    
                    if st.button("Reject", type="secondary"):
                        if not rejection_reason:
                            st.error("Please provide a reason for rejection")
                        else:
                            # Update request status in database
                            if reject_request(request_id, rejection_reason):
                                # Move scripts to rejected folder
                                move_success, message = s3_helper.move_scripts(request_id, "pending", "rejected")
                                
                                if move_success:
                                    st.success(f"Request #{selected_request['id']} rejected.")
                                    st.experimental_rerun()
                                else:
                                    st.error(f"Error moving scripts to rejected folder: {message}")
                            else:
                                st.error("Error updating request status in database")
            else:
                st.error("Could not retrieve all SQL scripts for this request")
