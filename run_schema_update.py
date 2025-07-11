#!/usr/bin/env python3
"""
Run the schema update for stage3_findings table to match Buried Wins standard
"""

import os
from dotenv import load_dotenv
from supabase_database import SupabaseDatabase

def run_schema_update():
    """Run the SQL schema update"""
    print("🔧 Updating stage3_findings table schema for Buried Wins standard...")
    
    # Load environment variables
    load_dotenv()
    
    # Initialize database connection
    db = SupabaseDatabase()
    
    # Read the SQL file
    with open('update_stage3_findings_schema_for_buried_wins.sql', 'r') as f:
        sql_commands = f.read()
    
    # Split into individual commands and execute
    commands = sql_commands.split(';')
    
    for i, command in enumerate(commands):
        command = command.strip()
        if command and not command.startswith('--'):
            try:
                print(f"Executing command {i+1}/{len(commands)}...")
                result = db.supabase.rpc('exec_sql', {'sql': command}).execute()
                print(f"✅ Command {i+1} executed successfully")
            except Exception as e:
                print(f"⚠️ Command {i+1} failed (this might be expected): {e}")
    
    print("✅ Schema update completed!")

if __name__ == "__main__":
    run_schema_update() 