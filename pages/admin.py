import streamlit as st
import pandas as pd
import json
import sys
import os
from datetime import datetime

# Update imports to use modules
from modules.auth import AuthManager
from modules.database import get_all_requests, get_request_by_id, approve_request, reject_request
from modules.storage import S3Helper

# Check authentication
if "username" not in st.session_state:
    st.error("Please login first")
    st.stop()

# Verify role
if st.session_state.role != "admin":
    st.error("You don't have permission to access this page")
    st.stop()

# Load configuration
with open('configs/config.json', 'r') as config_file:
    config = json.load(config_file)

# Initialize AuthManager
if 'auth_manager' not in st.session_state:
    st.session_state.auth_manager = AuthManager(config['secrets_manager_secret_name'])

# Initialize S3 helper
s3_helper = S3Helper(config['s3_bucket'], config['s3_root_prefix'])

# Get the section parameter if it exists
query_params = st.experimental_get_query_params()
section = query_params.get("section", ["users"])[0]

# Tabs for user management and request management
if section == "requests":
    tab_index = 1
else:
    tab_index = 0

tab1, tab2 = st.tabs(["User Management", "All Requests"])

with tab1:
    st.title("User Management")
    
    # Get users
    users = st.session_state.auth_manager.get_users()
    
    # Display users table
    if users:
        user_data = [{
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        } for user in users]
        
        df = pd.DataFrame(user_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No users found")
    
    # Add user form
    with st.expander("Add New User"):
        with st.form("add_user_form"):
            new_username = st.text_input("Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["developer", "analyst", "approver", "admin"])
            
            submit_button = st.form_submit_button("Add User")
            if submit_button:
                if not new_username or not new_email or not new_password:
                    st.error("All fields are required")
                else:
                    success, message = st.session_state.auth_manager.add_user(
                        new_username, new_email, new_password, new_role)
                    if success:
                        st.success(f"User {new_username} added successfully")
                        st.experimental_rerun()
                    else:
                        st.error(message)
    
    # Update user form
    with st.expander("Update User"):
        with st.form("update_user_form"):
            existing_usernames = [user["username"] for user in users]
            update_username = st.selectbox("Select User", [""] + existing_usernames)
            
            if update_username:
                # Find the user to prepopulate fields
                selected_user = next((u for u in users if u["username"] == update_username), None)
                update_email = st.text_input("Email", value=selected_user["email"] if selected_user else "")
                update_password = st.text_input("New Password (leave blank to keep current)", type="password")
                update_role = st.selectbox("Role", 
                                          ["developer", "analyst", "approver", "admin"],
                                          index=["developer", "analyst", "approver", "admin"].index(selected_user["role"]) if selected_user else 0)
            else:
                update_email = st.text_input("Email")
                update_password = st.text_input("New Password", type="password")
                update_role = st.selectbox("Role", ["developer", "analyst", "approver", "admin"])
            
            update_button = st.form_submit_button("Update User")
            if update_button:
                if not update_username:
                    st.error("Please select a user to update")
                else:
                    success, message = st.session_state.auth_manager.update_user(
                        update_username, update_email, update_password, update_role)
                    if success:
                        st.success(f"User {update_username} updated successfully")
                        st.experimental_rerun()
                    else:
                        st.error(message)
    
    # Remove user form
    with st.expander("Remove User"):
        with st.form("remove_user_form"):
            existing_usernames = [user["username"] for user in users if user["username"] != st.session_state.username]
            remove_username = st.selectbox("Select User to Remove", [""] + existing_usernames)
            
            remove_button = st.form_submit_button("Remove User")
            if remove_button:
                if not remove_username:
                    st.error("Please select a user to remove")
                else:
                    success, message = st.session_state.auth_manager.remove_user(remove_username)
                    if success:
                        st.success(f"User {remove_username} removed successfully")
                        st.experimental_rerun()
                    else:
                        st.error(message)

with tab2:
    st.title("All Requests")
    
    # Get all requests
    all_requests = get_all_requests()
    
    if not all_requests:
        st.info("No requests found")
    else:
        # Convert to DataFrame for display
        df = pd.DataFrame(all_requests)
        # Format datetime for display
        df['created_at'] = df['created_at'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
        if 'approved_at' in df.columns:
            df['approved_at'] = df['approved_at'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if x else None)
        
        # Add a view column
        df['view'] = 'View'
        
        # Display the dataframe
        st.dataframe(df[['id', 'created_by', 'dataset_name', 'status', 'created_at', 'approved_by', 'view']], 
                    use_container_width=True)
        
        # Allow selecting a request to review
        selected_request_id = st.selectbox("Select a request to view", 
                                          [""] + [str(row['id']) for row in all_requests])
        
        if selected_request_id:
            # Find the selected request
            selected_request = next((r for r in all_requests if str(r['id']) == selected_request_id), None)
            
            if selected_request:
                st.subheader(f"Request #{selected_request['id']} Details")
                
                status = selected_request['status']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Dataset:** {selected_request['dataset_name']}")
                    st.write(f"**Created by:** {selected_request['created_by']}")
                    st.write(f"**Created at:** {selected_request['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                with col2:
                    st.write(f"**Status:** {status}")
                    if status == 'approved' and selected_request['approved_by'] and selected_request['approved_at']:
                        st.write(f"**Approved by:** {selected_request['approved_by']}")
                        st.write(f"**Approved at:** {selected_request['approved_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                    elif status == 'rejected' and selected_request['rejection_reason']:
                        st.write(f"**Rejection reason:** {selected_request['rejection_reason']}")
                
                # Fetch SQL scripts from S3
                request_id = selected_request['request_id']
                
                # Determine which folder to look in based on status
                status_folder = status if status in ['approved', 'rejected'] else 'pending'
                
                # Fetch scripts
                land_success, land_ddl = s3_helper.get_script(request_id, "land_ddl", status_folder)
                stage_success, stage_ddl = s3_helper.get_script(request_id, "stage_ddl", status_folder)
                meta_success, meta_ddl = s3_helper.get_script(request_id, "metadata_ddl", status_folder)
                
                if land_success and stage_success and meta_success:
                    with st.expander("Landing Table DDL", expanded=True):
                        st.code(land_ddl, language="sql")
                    
                    with st.expander("Staging Table DDL", expanded=True):
                        st.code(stage_ddl, language="sql")
                    
                    with st.expander("Metadata DDL", expanded=True):
                        st.code(meta_ddl, language="sql")
                    
                    # Show approve/reject buttons only for pending requests
                    if status == 'pending':
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("Approve Request", type="primary"):
                                # Update request status in database
                                if approve_request(request_id, st.session_state.username):
                                    # Move scripts to approved folder
                                    move_success, message = s3_helper.move_scripts(request_id, "pending", "approved")
                                    
                                    if move_success:
                                        st.success(f"Request #{selected_request['id']} approved successfully!")
                                        # Here you would add code to execute the SQL against your databases
                                        st.experimental_rerun()
                                    else:
                                        st.error(f"Error moving scripts to approved folder: {message}")
                                else:
                                    st.error("Error updating request status in database")
                        
                        with col2:
                            # Rejection reason input
                            rejection_reason = st.text_area("Rejection Reason (required if rejecting)")
                            
                            if st.button("Reject Request", type="secondary"):
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
