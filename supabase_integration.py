#!/usr/bin/env python3
"""
Hybrid SQLite + Supabase Integration for VOC Pipeline
Provides sync functionality between local SQLite and cloud Supabase
"""

import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dotenv import load_dotenv
import json

# Supabase imports (install with: pip install supabase)
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase not available. Install with: pip install supabase")

load_dotenv()

logger = logging.getLogger(__name__)

class HybridDatabaseManager:
    """
    Manages hybrid SQLite (local) + Supabase (cloud) database setup
    """
    
    def __init__(self, 
                 sqlite_path: str = "voc_pipeline.db",
                 supabase_url: Optional[str] = None,
                 supabase_key: Optional[str] = None):
        
        self.sqlite_path = sqlite_path
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_ANON_KEY")
        
        # Initialize SQLite
        self.init_sqlite()
        
        # Initialize Supabase if available
        self.supabase = None
        if SUPABASE_AVAILABLE and self.supabase_url and self.supabase_key:
            try:
                self.supabase = create_client(self.supabase_url, self.supabase_key)
                self.init_supabase()
                logger.info("✅ Supabase connection established")
            except Exception as e:
                logger.warning(f"⚠️ Supabase connection failed: {e}")
        else:
            logger.info("ℹ️ Supabase not configured - running in local-only mode")
    
    def init_sqlite(self):
        """Initialize local SQLite database"""
        with sqlite3.connect(self.sqlite_path) as conn:
            cursor = conn.cursor()
            
            # Core responses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS core_responses (
                    response_id VARCHAR PRIMARY KEY,
                    verbatim_response TEXT,
                    subject VARCHAR,
                    question TEXT,
                    deal_status VARCHAR,
                    company VARCHAR,
                    interviewee_name VARCHAR,
                    interview_date DATE,
                    file_source VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sync_status VARCHAR DEFAULT 'local_only'
                )
            """)
            
            # Quote analysis table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quote_analysis (
                    analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quote_id VARCHAR,
                    criterion VARCHAR NOT NULL,
                    score DECIMAL(3,2),
                    priority VARCHAR CHECK (priority IN ('critical', 'high', 'medium', 'low')),
                    confidence VARCHAR CHECK (confidence IN ('high', 'medium', 'low')),
                    relevance_explanation TEXT,
                    deal_weighted_score DECIMAL(3,2),
                    context_keywords TEXT,
                    question_relevance VARCHAR CHECK (question_relevance IN ('direct', 'indirect', 'unrelated')),
                    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sync_status VARCHAR DEFAULT 'local_only',
                    FOREIGN KEY (quote_id) REFERENCES core_responses(response_id),
                    UNIQUE(quote_id, criterion)
                )
            """)
            
            # Sync tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_tracking (
                    sync_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name VARCHAR NOT NULL,
                    record_id VARCHAR NOT NULL,
                    sync_direction VARCHAR CHECK (sync_direction IN ('to_cloud', 'from_cloud')),
                    sync_status VARCHAR CHECK (sync_status IN ('pending', 'success', 'failed')),
                    sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT
                )
            """)
            
            conn.commit()
            logger.info(f"✅ SQLite database initialized at {self.sqlite_path}")
    
    def init_supabase(self):
        """Initialize Supabase tables (if they don't exist)"""
        if not self.supabase:
            return
        
        try:
            # Note: Supabase tables should be created via the dashboard or migrations
            # This is just a verification that the connection works
            result = self.supabase.table('core_responses').select('count').limit(1).execute()
            logger.info("✅ Supabase tables verified")
        except Exception as e:
            logger.warning(f"⚠️ Supabase table verification failed: {e}")
            logger.info("💡 Create tables in Supabase dashboard or run migrations")
    
    def save_to_sqlite(self, table: str, data: Dict[str, Any]) -> bool:
        """Save data to local SQLite database"""
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                
                if table == 'core_responses':
                    cursor.execute("""
                        INSERT OR REPLACE INTO core_responses 
                        (response_id, verbatim_response, subject, question, deal_status, 
                         company, interviewee_name, interview_date, file_source, sync_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        data.get('response_id'),
                        data.get('verbatim_response'),
                        data.get('subject'),
                        data.get('question'),
                        data.get('deal_status'),
                        data.get('company'),
                        data.get('interviewee_name'),
                        data.get('interview_date'),
                        data.get('file_source'),
                        'local_only'
                    ))
                
                elif table == 'quote_analysis':
                    cursor.execute("""
                        INSERT OR REPLACE INTO quote_analysis 
                        (quote_id, criterion, score, priority, confidence, relevance_explanation,
                         deal_weighted_score, context_keywords, question_relevance, sync_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        data.get('quote_id'),
                        data.get('criterion'),
                        data.get('score'),
                        data.get('priority'),
                        data.get('confidence'),
                        data.get('relevance_explanation'),
                        data.get('deal_weighted_score'),
                        data.get('context_keywords'),
                        data.get('question_relevance'),
                        'local_only'
                    ))
                
                conn.commit()
                logger.info(f"✅ Saved to SQLite: {table}")
                return True
                
        except Exception as e:
            logger.error(f"❌ SQLite save failed: {e}")
            return False
    
    def sync_to_supabase(self, table: str, record_id: str) -> bool:
        """Sync a single record from SQLite to Supabase"""
        if not self.supabase:
            logger.warning("⚠️ Supabase not available for sync")
            return False
        
        try:
            # Get data from SQLite
            with sqlite3.connect(self.sqlite_path) as conn:
                if table == 'core_responses':
                    cursor = conn.execute(
                        "SELECT * FROM core_responses WHERE response_id = ?", 
                        (record_id,)
                    )
                elif table == 'quote_analysis':
                    cursor = conn.execute(
                        "SELECT * FROM quote_analysis WHERE analysis_id = ?", 
                        (record_id,)
                    )
                
                row = cursor.fetchone()
                if not row:
                    logger.warning(f"⚠️ Record not found: {table}.{record_id}")
                    return False
                
                # Convert to dict
                columns = [description[0] for description in cursor.description]
                data = dict(zip(columns, row))
                
                # Remove SQLite-specific fields
                data.pop('sync_status', None)
                if 'analysis_id' in data:
                    data.pop('analysis_id')  # Let Supabase generate this
            
            # Upload to Supabase
            result = self.supabase.table(table).upsert(data).execute()
            
            # Update sync status in SQLite
            with sqlite3.connect(self.sqlite_path) as conn:
                conn.execute(
                    f"UPDATE {table} SET sync_status = 'synced' WHERE response_id = ?",
                    (record_id,)
                )
                conn.commit()
            
            logger.info(f"✅ Synced to Supabase: {table}.{record_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Supabase sync failed: {e}")
            return False
    
    def sync_all_to_supabase(self) -> Dict[str, int]:
        """Sync all local-only records to Supabase"""
        if not self.supabase:
            return {"error": "Supabase not available"}
        
        stats = {"core_responses": 0, "quote_analysis": 0, "errors": 0}
        
        try:
            # Sync core_responses
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.execute(
                    "SELECT response_id FROM core_responses WHERE sync_status = 'local_only'"
                )
                response_ids = [row[0] for row in cursor.fetchall()]
                
                for response_id in response_ids:
                    if self.sync_to_supabase('core_responses', response_id):
                        stats["core_responses"] += 1
                    else:
                        stats["errors"] += 1
                
                # Sync quote_analysis
                cursor = conn.execute(
                    "SELECT analysis_id FROM quote_analysis WHERE sync_status = 'local_only'"
                )
                analysis_ids = [row[0] for row in cursor.fetchall()]
                
                for analysis_id in analysis_ids:
                    if self.sync_to_supabase('quote_analysis', str(analysis_id)):
                        stats["quote_analysis"] += 1
                    else:
                        stats["errors"] += 1
            
            logger.info(f"📊 Sync complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Bulk sync failed: {e}")
            return {"error": str(e)}
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status summary"""
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                
                # Count by sync status - with debugging
                logger.info("🔍 Querying core_responses sync_status...")
                cursor.execute("""
                    SELECT sync_status, COUNT(*) 
                    FROM core_responses 
                    GROUP BY sync_status
                """)
                response_sync = dict(cursor.fetchall())
                logger.info(f"✅ core_responses sync_status: {response_sync}")
                
                logger.info("🔍 Querying quote_analysis sync_status...")
                cursor.execute("""
                    SELECT sync_status, COUNT(*) 
                    FROM quote_analysis 
                    GROUP BY sync_status
                """)
                analysis_sync = dict(cursor.fetchall())
                logger.info(f"✅ quote_analysis sync_status: {analysis_sync}")
                
                return {
                    "supabase_available": bool(self.supabase),
                    "core_responses": response_sync,
                    "quote_analysis": analysis_sync,
                    "total_local_responses": sum(response_sync.values()),
                    "total_local_analyses": sum(analysis_sync.values())
                }
                
        except Exception as e:
            logger.error(f"❌ Sync status check failed: {e}")
            logger.error(f"❌ Error type: {type(e)}")
            logger.error(f"❌ Error args: {e.args}")
            return {"error": str(e)}
    
    def get_data_for_sharing(self, filters: Optional[Dict] = None) -> pd.DataFrame:
        """Get data optimized for web sharing (from Supabase if available, otherwise SQLite)"""
        if self.supabase:
            try:
                # Try to get from Supabase first
                query = self.supabase.table('core_responses').select('*')
                
                if filters:
                    for key, value in filters.items():
                        if key in ['company', 'deal_status']:
                            query = query.eq(key, value)
                
                result = query.execute()
                df = pd.DataFrame(result.data)
                
                if not df.empty:
                    logger.info(f"📊 Retrieved {len(df)} records from Supabase")
                    return df
                    
            except Exception as e:
                logger.warning(f"⚠️ Supabase query failed, falling back to SQLite: {e}")
        
        # Fallback to SQLite
        with sqlite3.connect(self.sqlite_path) as conn:
            query = "SELECT * FROM core_responses"
            params = []
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    if key in ['company', 'deal_status']:
                        conditions.append(f"{key} = ?")
                        params.append(value)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            df = pd.read_sql_query(query, conn, params=params)
            logger.info(f"📊 Retrieved {len(df)} records from SQLite")
            return df

# Usage examples
def setup_hybrid_database():
    """Setup hybrid database with environment variables"""
    return HybridDatabaseManager()

def sync_and_share():
    """Sync local data to cloud and get sharing URL"""
    db = setup_hybrid_database()
    
    # Sync all local data
    sync_stats = db.sync_all_to_supabase()
    
    # Get sync status
    status = db.get_sync_status()
    
    return {
        "sync_stats": sync_stats,
        "status": status,
        "supabase_available": bool(db.supabase)
    }

if __name__ == "__main__":
    # Test the hybrid setup
    db = setup_hybrid_database()
    status = db.get_sync_status()
    print("🔍 Hybrid Database Status:")
    print(json.dumps(status, indent=2)) 