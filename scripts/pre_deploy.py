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
    # Load configuration
    with open('../configs/config.json', 'r') as config_file:
        config = json.load(config_file)
    
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
        # Get all migration files
        migration_dir = '../migrations'
        migration_files = [f for f in os.listdir(migration_dir) if f.endswith('.sql')]
        migration_files.sort()  # Sort to ensure order
        
        print(f"Found {len(migration_files)} migration files")
        
        for migration_file in migration_files:
            print(f"Running migration: {migration_file}")
            with open(os.path.join(migration_dir, migration_file), 'r') as f:
                sql = f.read()
                cursor.execute(sql)
        
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
