#!/usr/bin/env python3
"""
Minimal Streamlit test for sync_status error
"""

import streamlit as st
import traceback

def test_sync_in_streamlit():
    """Test sync status in Streamlit environment"""
    st.title("🔍 Sync Status Debug Test")
    
    try:
        st.write("🔍 Importing HybridDatabaseManager...")
        from supabase_integration import HybridDatabaseManager
        st.write("✅ Import successful")
        
        st.write("🔍 Initializing HybridDatabaseManager...")
        db_manager = HybridDatabaseManager()
        st.write("✅ Initialization successful")
        
        st.write("🔍 Calling get_sync_status...")
        status = db_manager.get_sync_status()
        st.write("✅ get_sync_status successful")
        st.json(status)
        
    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.code(traceback.format_exc())
        
        # Test database directly
        st.write("🔍 Testing database directly...")
        try:
            import sqlite3
            with sqlite3.connect("voc_pipeline.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT sync_status, COUNT(*) FROM core_responses GROUP BY sync_status")
                result = cursor.fetchall()
                st.write(f"core_responses: {result}")
                
                cursor.execute("SELECT sync_status, COUNT(*) FROM quote_analysis GROUP BY sync_status")
                result = cursor.fetchall()
                st.write(f"quote_analysis: {result}")
                
        except Exception as db_error:
            st.error(f"❌ Database error: {db_error}")

if __name__ == "__main__":
    test_sync_in_streamlit() 