#!/usr/bin/env python3
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration(migration_file):
    """Run a migration script on the database."""
    # Get database URL from environment
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Create engine
    engine = create_engine(db_url)
    
    # Read migration file
    try:
        with open(migration_file, "r") as f:
            migration_sql = f.read()
    except FileNotFoundError:
        print(f"Error: Migration file {migration_file} not found")
        sys.exit(1)
    
    # Run migration
    try:
        with engine.begin() as conn:
            conn.execute(text(migration_sql))
        print(f"Migration {migration_file} completed successfully")
    except SQLAlchemyError as e:
        print(f"Error executing migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <migration_file>")
        sys.exit(1)
    
    migration_file = sys.argv[1]
    run_migration(migration_file) 