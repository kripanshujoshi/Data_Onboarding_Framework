import os
import subprocess
import tempfile
import shutil
from datetime import datetime
from modules.config import config

def git_push_files_to_feature_branch(files, branch_name, folder):
    temp_repo_dir = None
    try:
        GIT_USERNAME = os.getenv('GIT_USERNAME')
        GIT_TOKEN = os.getenv('GIT_TOKEN')
        git_conf = config.get('git', {})
        REPO_OWNER = git_conf.get('repo_owner')
        REPO_NAME = git_conf.get('repo_name')
        BOT_NAME = git_conf.get('bot_name')
        BOT_EMAIL = git_conf.get('bot_email')
        GIT_REPO = f'https://{GIT_USERNAME}:{GIT_TOKEN}@github.com/{REPO_OWNER}/{REPO_NAME}.git'

        # Clone the repo into a temporary directory
        temp_repo_dir = tempfile.mkdtemp()
        subprocess.run(["git", "clone", GIT_REPO, temp_repo_dir], check=True)
        os.chdir(temp_repo_dir)

        branches_output = subprocess.check_output(["git", "branch", "-r"], text=True)
        main_branch = "main" if "origin/main" in branches_output else "master"
        subprocess.run(["git", "checkout", main_branch], check=True)
        subprocess.run(["git", "pull", "origin", main_branch], check=True)
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        subprocess.run(["git", "push", "--set-upstream", "origin", branch_name], check=True)

        # Ensure target folder exists and move files there
        folder_path = os.path.join(temp_repo_dir, folder)
        os.makedirs(folder_path, exist_ok=True)
        for file in files:
            dest_path = os.path.join(folder_path, os.path.basename(file))
            shutil.move(file, dest_path)
        
        subprocess.run(["git", "config", "user.name", BOT_NAME], check=True)
        subprocess.run(["git", "config", "user.email", BOT_EMAIL], check=True)
        subprocess.run(["git", "add", folder], check=True)
        subprocess.run(["git", "commit", "-m", f"Added files to {folder} in feature branch {branch_name}"], check=True)
        subprocess.run(["git", "push"], check=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"[ERROR] Git command failed: {e}")
    finally:
        if temp_repo_dir and os.path.exists(temp_repo_dir):
            shutil.rmtree(temp_repo_dir)