#!/usr/bin/env python3
"""
Database setup script for embedding tables.
Run this script to create the necessary tables in Supabase.
"""

import os
import sys
from pathlib import Path
from supabase_client import supabase

def setup_embedding_tables():
    """Create embedding tables in the database."""
    
    # Read the SQL file
    sql_file = Path(__file__).parent / "setup_embedding_tables.sql"
    
    try:
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        print("Setting up embedding tables in database...")
        
        # Execute the SQL
        result = supabase.rpc("exec_sql", {"sql": sql_content}).execute()
        
        if result.data:
            print("✅ Embedding tables created successfully!")
            print("Created tables:")
            print("  - user_embedding (stores user preference embeddings)")
            print("  - item_embedding (stores item content embeddings)")
            print("  - Added indexes and foreign key constraints")
        else:
            print("⚠️  Tables may already exist or there was an issue")
            
    except FileNotFoundError:
        print(f"❌ SQL file not found: {sql_file}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        sys.exit(1)

def verify_tables():
    """Verify that the tables were created correctly."""
    
    print("\nVerifying table creation...")
    
    try:
        # Check user_embedding table
        user_emb_result = supabase.table("user_embedding").select("*").limit(1).execute()
        print("✅ user_embedding table exists")
        
        # Check item_embedding table  
        item_emb_result = supabase.table("item_embedding").select("*").limit(1).execute()
        print("✅ item_embedding table exists")
        
        print("\n🎉 Database setup completed successfully!")
        print("\nNext steps:")
        print("1. Run the profiler agent to create user profiles")
        print("2. Run the hunter agent to generate candidates and embeddings") 
        print("3. Start swiping to see personalized recommendations!")
        
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        print("You may need to manually create the tables in Supabase")

if __name__ == "__main__":
    print("🚀 Setting up embedding database tables...")
    print(f"Database URL: {os.getenv('SUPABASE_URL', 'Not set')}")
    
    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_SERVICE_ROLE_KEY'):
        print("❌ Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables")
        sys.exit(1)
    
    setup_embedding_tables()
    verify_tables()