import json
import boto3
import psycopg2
import os
import sys
import argparse

def get_secret(secret_name, region_name="us-east-1"):
    """Retrieve database credentials from AWS Secrets Manager"""
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

def get_db_connection(env):
    """Get database connection for the specified environment"""
    # Load configuration - try multiple paths for GitHub Actions compatibility
    config_paths = [
        '../configs/config.json',  # When running locally
        'configs/config.json',     # When running from project root
        f'configs/config-{env}.json'  # Environment-specific config
    ]
    
    config = None
    for path in config_paths:
        try:
            if os.path.exists(path):
                with open(path, 'r') as config_file:
                    config = json.load(config_file)
                    print(f"Loaded config from {path}")
                    break
        except Exception as e:
            print(f"Could not load config from {path}: {str(e)}")
    
    if config is None:
        raise FileNotFoundError("Could not find config file in any of the expected locations")
    
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

def run_migrations(conn):
    """Run database migrations"""
    cursor = conn.cursor()
    
    try:
        # Try different paths for GitHub Actions compatibility
        possible_dirs = ['../migrations', 'migrations']
        migration_dir = None
        
        for directory in possible_dirs:
            if os.path.exists(directory):
                migration_dir = directory
                print(f"Using migration directory: {migration_dir}")
                break
            if migration_dir is None:
               raise FileNotFoundError("Could not find migrations directory")
            
        migration_files = [f for f in os.listdir(migration_dir) if f.endswith('.sql')]
        migration_files.sort()  # Sort to ensure order
        
        print(f"Found {len(migration_files)} migration files")
        for migration_file in migration_files:
            print(f"Running migration: {migration_file}")
            try:
                with open(os.path.join(migration_dir, migration_file), 'r') as f:
                    sql = f.read()
                    cursor.execute(sql)
                    print(f"Successfully executed migration: {migration_file}")
            except Exception as e:
                print(f"Error executing migration {migration_file}: {str(e)}")
                raise
        
        conn.commit()
        print("All migrations completed successfully")
    except Exception as e:
        conn.rollback()
        print(f"Error running migrations: {str(e)}")
        sys.exit(1)
    finally:
        cursor.close()

def main():
    parser = argparse.ArgumentParser(description='Run pre-deployment tasks')
    parser.add_argument('--env', required=True, choices=['dev', 'qa', 'prod'], 
                        help='Deployment environment')
    args = parser.parse_args()
    
    # Run database migrations
    try:
        print(f"Connecting to database for environment: {args.env}")
        conn = get_db_connection(args.env)
        run_migrations(conn)
        conn.close()
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
