import streamlit as st
import boto3
import json
import bcrypt
import uuid
from botocore.exceptions import ClientError
from .config import get_config

class AuthManager:
    def __init__(self, secret_name):
        self.secret_name = secret_name
        self.users = self._load_users_from_secret()
        
    def _load_users_from_secret(self):
        """Load users from AWS Secrets Manager"""
        try:
            session = boto3.session.Session()
            client = session.client(service_name='secretsmanager')
            response = client.get_secret_value(SecretId=self.secret_name)
            secret_data = json.loads(response['SecretString'])
            return secret_data.get('users', [])
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Create new secret if it doesn't exist
                empty_users = {'users': []}
                client.create_secret(
                    Name=self.secret_name,
                    SecretString=json.dumps(empty_users)
                )
                return []
            else:
                st.error(f"Error accessing secret: {str(e)}")
                return []
    
    def _save_users_to_secret(self):
        """Save users back to AWS Secrets Manager"""
        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager')
        secret_data = {'users': self.users}
        client.put_secret_value(
            SecretId=self.secret_name,
            SecretString=json.dumps(secret_data)
        )
    
    def hash_password(self, password):
        """Generate bcrypt hash from password"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, stored_hash, provided_password):
        """Verify password against stored hash"""
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_hash.encode('utf-8'))
    
    def add_user(self, username, email, password, role):
        """Add a new user"""
        # Check if username already exists
        if any(user['username'] == username for user in self.users):
            return False, "Username already exists"
        
        user = {
            'username': username,
            'email': email,
            'password_hash': self.hash_password(password),
            'role': role
        }
        self.users.append(user)
        self._save_users_to_secret()
        return True, "User added successfully"
    
    def update_user(self, username, email=None, password=None, role=None):
        """Update an existing user"""
        for user in self.users:
            if user['username'] == username:
                if email:
                    user['email'] = email
                if password:
                    user['password_hash'] = self.hash_password(password)
                if role:
                    user['role'] = role
                self._save_users_to_secret()
                return True, "User updated successfully"
        return False, "User not found"
    
    def remove_user(self, username):
        """Remove a user"""
        initial_count = len(self.users)
        self.users = [user for user in self.users if user['username'] != username]
        if len(self.users) < initial_count:
            self._save_users_to_secret()
            return True, "User removed successfully"
        return False, "User not found"
    
    def get_users(self):
        """Get all users"""
        return self.users
    
    def authenticate(self, username, password):
        """Authenticate a user"""
        for user in self.users:
            if user['username'] == username and self.verify_password(user['password_hash'], password):
                return True, user
        return False, None

def bootstrap_admin():
    """Check if there are users and create first admin if needed"""
    if 'auth_manager' not in st.session_state:
        # Use config module instead of direct file load
        config = get_config()
        st.session_state.auth_manager = AuthManager(config['secrets_manager_secret_name'])
    
    if not st.session_state.auth_manager.get_users():
        st.title("Create First Admin User")
        with st.form("create_admin"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            submitted = st.form_submit_button("Create Admin")
            if submitted:
                if password != confirm_password:
                    st.error("Passwords do not match")
                elif not username or not email or not password:
                    st.error("All fields are required")
                else:
                    success, message = st.session_state.auth_manager.add_user(
                        username, email, password, "admin"
                    )
                    if success:
                        st.success("Admin user created. Please log in.")
                        st.session_state.show_login = True
                        st.experimental_rerun()
                    else:
                        st.error(message)
        return False
    return True

def login():
    """Render login form and handle authentication"""
    if 'auth_manager' not in st.session_state:
        # Use config module instead of direct file load
        config = get_config()
        st.session_state.auth_manager = AuthManager(config['secrets_manager_secret_name'])
    
    st.title("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        submitted = st.form_submit_button("Login")
        if submitted:
            success, user = st.session_state.auth_manager.authenticate(username, password)
            if success:
                st.session_state.username = user['username']
                st.session_state.role = user['role']
                st.session_state.email = user['email']
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")
    return False
