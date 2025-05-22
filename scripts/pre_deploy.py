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

def create_migrations_table_if_needed(cursor):
    """Create migrations tracking table if it doesn't exist"""
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schema_migrations (
        migration_id VARCHAR(255) PRIMARY KEY,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

def check_if_migration_applied(cursor, migration_id):
    """Check if a specific migration has already been applied"""
    cursor.execute("SELECT 1 FROM schema_migrations WHERE migration_id = %s", (migration_id,))
    return cursor.fetchone() is not None

def record_migration_applied(cursor, migration_id):
    """Record that a migration has been applied"""
    cursor.execute("INSERT INTO schema_migrations (migration_id) VALUES (%s)", (migration_id,))

def run_migrations(conn):
    """Run database migrations"""
    cursor = conn.cursor()
    
    try:
        # Create migration tracking table
        create_migrations_table_if_needed(cursor)
        conn.commit()
        
        # Try different paths for GitHub Actions compatibility
        # Consider absolute paths based on script location and project root
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, '..'))
        current_dir = os.getcwd()
        
        # Print all directory information for debugging
        print(f"Script directory: {script_dir}")
        print(f"Project root: {project_root}")
        print(f"Current working directory: {current_dir}")
        
        # Check all possible directories where migrations might be located
        possible_dirs = [
            '../migrations',                               # When running from scripts dir
            'migrations',                                  # When running from project root
            os.path.join(project_root, 'migrations'),      # Absolute path to migrations
            os.path.join(script_dir, '../migrations'),     # Absolute path from scripts dir
            './migrations',                                # Current directory + migrations
            os.path.join(current_dir, 'migrations')        # Absolute path from current dir
        ]
        
        print(f"Looking for migrations in these directories: {possible_dirs}")
        
        # Find the first existing migration directory
        migration_dir = None
        for directory in possible_dirs:
            if os.path.exists(directory):
                print(f"Directory {directory} exists with contents: {os.listdir(directory)}")
                migration_dir = directory
                print(f"Using migration directory: {migration_dir}")
                break
            else:
                print(f"Directory {directory} does not exist")
                
        if migration_dir is None:
            raise FileNotFoundError("Could not find migrations directory")
            
        # Get all SQL migration files and sort them
        migration_files = [f for f in os.listdir(migration_dir) if f.endswith('.sql')]
        migration_files.sort()  # Sort to ensure order
        
        print(f"Found {len(migration_files)} migration files")
        applied_count = 0
        
        for migration_file in migration_files:
            migration_id = os.path.splitext(migration_file)[0]  # Remove .sql extension
            
            # Check if migration was already applied
            if check_if_migration_applied(cursor, migration_id):
                print(f"Migration {migration_file} already applied, skipping")
                continue
                
            print(f"Running migration: {migration_file}")
            try:
                with open(os.path.join(migration_dir, migration_file), 'r') as f:
                    sql = f.read()
                    # Execute each statement separately
                    for statement in sql.split(';'):
                        if statement.strip():  # Skip empty statements
                            cursor.execute(statement)
                    
                # Record that this migration was applied
                record_migration_applied(cursor, migration_id)
                applied_count += 1
                print(f"Successfully executed migration: {migration_file}")
            except Exception as e:
                print(f"Error executing migration {migration_file}: {str(e)}")
                raise
        
        conn.commit()
        print(f"Migrations completed successfully: {applied_count} applied, {len(migration_files) - applied_count} skipped")
    except Exception as e:
        conn.rollback()
        print(f"Error running migrations: {str(e)}")
        sys.exit(1)
    finally:
        cursor.close()

def verify_aws_credentials():
    """Verify that AWS credentials are properly configured"""
    try:
        session = boto3.session.Session()
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"Running as AWS Identity: {identity['Arn']}")
        return True
    except Exception as e:
        print(f"AWS credentials verification failed: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Run pre-deployment tasks')
    parser.add_argument('--env', required=True, choices=['dev', 'qa', 'prod'], 
                        help='Deployment environment')
    parser.add_argument('--skip-migrations', action='store_true', 
                        help='Skip database migrations')
    parser.add_argument('--debug', action='store_true',
                        help='Enable verbose debug output')
    args = parser.parse_args()
    
    # Set more verbose output if debug is enabled
    if args.debug:
        print("Debug mode enabled")
        import logging
        logging.basicConfig(level=logging.DEBUG)
        
    # Verify AWS credentials
    print("Verifying AWS credentials...")
    if not verify_aws_credentials():
        print("ERROR: AWS credentials verification failed. Cannot proceed with deployment.")
        sys.exit(1)
    
    # Run database migrations if not skipped
    if not args.skip_migrations:
        try:
            print(f"Connecting to database for environment: {args.env}")
            try:
                conn = get_db_connection(args.env)
                print("Database connection successful")
                
                run_migrations(conn)
                print("Migrations completed, closing connection")
                conn.close()
            except FileNotFoundError as e:
                print(f"Configuration error: {str(e)}")
                print("This may be due to missing configuration files. Check that configs/config-{env}.json exists.")
                sys.exit(1)
            except psycopg2.OperationalError as e:
                print(f"Database connection error: {str(e)}")
                print("This may be due to network issues, incorrect credentials, or the database not being available.")
                sys.exit(1)
        except Exception as e:
            print(f"Unexpected error during migrations: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print("Skipping database migrations as requested")
        
    print("Pre-deployment tasks completed successfully")

if __name__ == "__main__":
    main()
