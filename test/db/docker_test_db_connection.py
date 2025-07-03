#!/usr/bin/env python3
"""Test script for database connection to be run inside Docker"""

import os
import sys
from sqlalchemy import create_engine, text

# Print environment variables for debugging
print("\n🔍 Testing database connection with these settings:")
print(f"  - Host: {os.environ.get('DB_HOST')}")
print(f"  - Port: {os.environ.get('DB_PORT')}")
print(f"  - User: {os.environ.get('DB_USER')}")
print(f"  - Password: {'*' * len(os.environ.get('DB_PASSWORD', ''))}")
print(f"  - Database: {os.environ.get('DB_NAME')}\n")

try:
    # Create database URL
    db_url = f"mysql+mysqlconnector://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
    
    # Create SQLAlchemy engine
    engine = create_engine(db_url)
    
    # Test connection
    with engine.connect() as connection:
        # Test basic connectivity
        result = connection.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        print(f"   Result of test query: {result.scalar()}")
        
        # Test actual data
        result = connection.execute(text("SELECT COUNT(*) FROM unitati"))
        count = result.scalar()
        print(f"✅ There are {count} units in the unitati table")
        
    print("\n✅ TEST PASSED: Database connection successful!")
    sys.exit(0)
except Exception as e:
    print("\n❌ TEST FAILED: Database connection error")
    print(f"   Error: {e}")
    sys.exit(1)
