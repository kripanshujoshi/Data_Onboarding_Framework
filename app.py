"""
Streamlit application for Data Onboarding Framework UI and workflow orchestration.
"""
import streamlit as st
import json
import os
# Change imports to use modules directly
from modules.auth import bootstrap_admin, login
from modules.database import initialize_sql_requests_table
from modules.config import get_config  # If you have this module

# Get environment-aware configuration
config = get_config()

# Set page config
st.set_page_config(
    page_title="Data Onboarding Framework",
    page_icon="📊",
    layout="wide"
)

# Display environment banner in non-prod environments
if os.environ.get('DEPLOY_ENV', 'dev') != 'prod':
    env = os.environ.get('DEPLOY_ENV', 'dev').upper()
    st.warning(f"⚠️ {env} ENVIRONMENT ⚠️")

# Add environment indicator (optional)
env = config['environment'].upper()
if env != 'PROD':
    st.sidebar.warning(f"⚠️ {env} ENVIRONMENT")

# Initialize database tables
initialize_sql_requests_table()

# Check authentication
if not bootstrap_admin():
    st.stop()

if "username" not in st.session_state:
    if not login():
        st.stop()

# Display user info
st.sidebar.write(f"Welcome, {st.session_state.username}")
st.sidebar.write(f"Role: {st.session_state.role}")

# Role-based navigation
role = st.session_state.role

# Create navigation sections based on role
if role == "developer" or role == "admin":
    developer_expander = st.sidebar.expander("▶ Data Onboarding")
    developer_expander.page_link("pages/developer.py", label="Create Onboarding Request")

if role == "analyst" or role == "admin":
    analyst_expander = st.sidebar.expander("▶ Config Explorer")
    analyst_expander.page_link("pages/analyst.py", label="Browse Configurations")

if role == "approver" or role == "admin":
    approver_expander = st.sidebar.expander("▶ Approvals")
    approver_expander.page_link("pages/approver.py", label="Review Pending Requests")

if role == "admin":
    admin_expander = st.sidebar.expander("▶ Admin Panel")
    admin_expander.page_link("pages/admin.py", label="User Management")
    admin_expander.page_link("pages/admin.py", label="All Requests", args={"section": "requests"})

# Environment indicator
current_env = os.environ.get('DEPLOY_ENV', 'dev')
st.sidebar.info(f"Environment: {current_env.upper()}")

# Logout button
if st.sidebar.button("Logout"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

# Main content
st.title("Data Onboarding Framework")
st.markdown("""
Welcome to the Data Onboarding Framework. Use the navigation menu on the left to access your role-specific features.

### Quick Overview
- **Data Onboarding**: Create and submit data onboarding requests
- **Config Explorer**: Browse existing data configurations
- **Approvals**: Review and approve pending requests
- **Admin Panel**: Manage users and view all requests
""")
