#!/usr/bin/env python3
import sys
from pathlib import Path

print(f"Current working directory: {Path.cwd()}")
print(f"Python path: {sys.path}")
print(f"Script location: {Path(__file__).resolve()}")

try:
    from supabase_database import SupabaseDatabase
    print("✅ Import successful!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    
    # Try to add current directory to path
    current_dir = str(Path.cwd())
    print(f"Adding {current_dir} to Python path...")
    sys.path.insert(0, current_dir)
    
    try:
        from supabase_database import SupabaseDatabase
        print("✅ Import successful after path fix!")
    except ImportError as e2:
        print(f"❌ Still failed: {e2}") 