#!/usr/bin/env python3
"""
Script to create all database tables for the Legal Case Management System
"""

from models import Base
from db.db import engine
from config import Config

def create_tables():
    """Create all tables defined in the models"""
    print("Creating database tables...")
    print(f"Database URI: {Config.SQLALCHEMY_DATABASE_URI}")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # Print created tables
        print("\nCreated tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise

if __name__ == "__main__":
    create_tables()
