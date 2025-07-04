import sqlite3
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class VOCDatabase:
    def __init__(self, db_path: str = "voc_pipeline.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def init_database(self):
        """Initialize database with all required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Core responses table (source of truth)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                response_id VARCHAR(255) PRIMARY KEY,
                verbatim_response TEXT NOT NULL,
                subject VARCHAR(500),
                question VARCHAR(1000),
                deal_status VARCHAR(100),
                company VARCHAR(255),
                interviewee_name VARCHAR(255),
                date_of_interview DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Labels/annotations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS response_labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id VARCHAR(255) NOT NULL,
                label_type VARCHAR(100) NOT NULL,
                label_value VARCHAR(255) NOT NULL,
                confidence_score REAL,
                labeled_by VARCHAR(100),
                labeled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (response_id) REFERENCES responses(response_id) ON DELETE CASCADE,
                UNIQUE(response_id, label_type, label_value)
            )
        """)
        
        # Analysis results table (AI-generated insights)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id VARCHAR(255) NOT NULL,
                analysis_type VARCHAR(100) NOT NULL,
                analysis_text TEXT,
                confidence_score REAL,
                model_version VARCHAR(50),
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (response_id) REFERENCES responses(response_id) ON DELETE CASCADE
            )
        """)
        
        # Quality metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id VARCHAR(255) NOT NULL,
                metric_type VARCHAR(100) NOT NULL,
                metric_value REAL,
                metric_details TEXT, -- JSON as text for SQLite
                evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (response_id) REFERENCES responses(response_id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_responses_company ON responses(company)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_responses_deal_status ON responses(deal_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_responses_date ON responses(date_of_interview)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_responses_subject ON responses(subject)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_responses_created_at ON responses(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_responses_interviewee ON responses(interviewee_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_labels_type ON response_labels(label_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_labels_value ON response_labels(label_value)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_labels_confidence ON response_labels(confidence_score)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_type ON analysis_results(analysis_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_confidence ON analysis_results(confidence_score)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_type ON quality_metrics(metric_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_value ON quality_metrics(metric_value)")
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def save_response(self, response_data: Dict[str, Any]) -> bool:
        """Save a response to the database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Insert core response
            cursor.execute("""
                INSERT OR REPLACE INTO responses (
                    response_id, verbatim_response, subject, question,
                    deal_status, company, interviewee_name, date_of_interview
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                response_data.get('response_id'),
                response_data.get('verbatim_response'),
                response_data.get('subject'),
                response_data.get('question'),
                response_data.get('deal_status'),
                response_data.get('company'),
                response_data.get('interviewee_name'),
                response_data.get('date_of_interview')
            ))
            
            # Insert analysis results if present
            analysis_fields = [
                'findings', 'value_realization', 'implementation_experience',
                'risk_mitigation', 'competitive_advantage', 'customer_success',
                'product_feedback', 'service_quality', 'decision_factors',
                'pain_points', 'success_metrics', 'future_plans', 'key_insight'
            ]
            
            for field in analysis_fields:
                if field in response_data and response_data[field] and response_data[field] != 'N/A':
                    cursor.execute("""
                        INSERT OR REPLACE INTO analysis_results (
                            response_id, analysis_type, analysis_text, model_version
                        ) VALUES (?, ?, ?, ?)
                    """, (
                        response_data['response_id'],
                        field,
                        response_data[field],
                        'gpt-4o-mini-v1'  # Current model version
                    ))
            
            conn.commit()
            conn.close()
            logger.info(f"Successfully saved response {response_data.get('response_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving response {response_data.get('response_id')}: {e}")
            return False
    
    def get_responses(self, filters: Optional[Dict] = None) -> pd.DataFrame:
        """Get responses with optional filtering"""
        conn = self.get_connection()
        
        query = """
            SELECT r.*, 
                   GROUP_CONCAT(DISTINCT al.analysis_type || ': ' || al.analysis_text) as analyses,
                   GROUP_CONCAT(DISTINCT qm.metric_type || ': ' || qm.metric_value) as quality_metrics
            FROM responses r
            LEFT JOIN analysis_results al ON r.response_id = al.response_id
            LEFT JOIN quality_metrics qm ON r.response_id = qm.response_id
        """
        
        params = []
        if filters:
            conditions = []
            for key, value in filters.items():
                if key in ['company', 'deal_status', 'subject']:
                    conditions.append(f"r.{key} = ?")
                    params.append(value)
                elif key == 'date_from':
                    conditions.append("r.date_of_interview >= ?")
                    params.append(value)
                elif key == 'date_to':
                    conditions.append("r.date_of_interview <= ?")
                    params.append(value)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        query += " GROUP BY r.response_id ORDER BY r.created_at DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    
    def get_response_by_id(self, response_id: str) -> Optional[Dict]:
        """Get a single response with all its data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get core response
        cursor.execute("SELECT * FROM responses WHERE response_id = ?", (response_id,))
        response = cursor.fetchone()
        
        if not response:
            conn.close()
            return None
        
        # Get analysis results
        cursor.execute("SELECT analysis_type, analysis_text FROM analysis_results WHERE response_id = ?", (response_id,))
        analyses = {row['analysis_type']: row['analysis_text'] for row in cursor.fetchall()}
        
        # Get labels
        cursor.execute("SELECT label_type, label_value, confidence_score FROM response_labels WHERE response_id = ?", (response_id,))
        labels = {row['label_type']: {'value': row['label_value'], 'confidence': row['confidence_score']} for row in cursor.fetchall()}
        
        # Get quality metrics
        cursor.execute("SELECT metric_type, metric_value, metric_details FROM quality_metrics WHERE response_id = ?", (response_id,))
        metrics = {row['metric_type']: {'value': row['metric_value'], 'details': row['metric_details']} for row in cursor.fetchall()}
        
        conn.close()
        
        # Combine all data
        result = dict(response)
        result['analyses'] = analyses
        result['labels'] = labels
        result['quality_metrics'] = metrics
        
        return result
    
    def add_label(self, response_id: str, label_type: str, label_value: str, 
                  confidence_score: Optional[float] = None, labeled_by: str = 'ai_model') -> bool:
        """Add a label to a response"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO response_labels (
                    response_id, label_type, label_value, confidence_score, labeled_by
                ) VALUES (?, ?, ?, ?, ?)
            """, (response_id, label_type, label_value, confidence_score, labeled_by))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error adding label: {e}")
            return False
    
    def add_quality_metric(self, response_id: str, metric_type: str, metric_value: float, 
                          metric_details: Optional[Dict] = None) -> bool:
        """Add a quality metric to a response"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            details_json = json.dumps(metric_details) if metric_details else None
            
            cursor.execute("""
                INSERT OR REPLACE INTO quality_metrics (
                    response_id, metric_type, metric_value, metric_details
                ) VALUES (?, ?, ?, ?)
            """, (response_id, metric_type, metric_value, details_json))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error adding quality metric: {e}")
            return False
    
    def migrate_csv_to_db(self, csv_path: str) -> int:
        """Migrate existing CSV data to database"""
        try:
            df = pd.read_csv(csv_path)
            migrated_count = 0
            
            for _, row in df.iterrows():
                response_data = {
                                'response_id': row.get('response_id', f"migrated_{migrated_count}"),
            'verbatim_response': row.get('verbatim_response', ''),
            'subject': row.get('subject', ''),
            'question': row.get('question', ''),
            'deal_status': row.get('deal_status', ''),
            'company': row.get('company', ''),
            'interviewee_name': row.get('interviewee_name', ''),
                    'date_of_interview': row.get('Date of Interview', ''),
                }
                
                # Add analysis fields - check if they exist in the CSV
                analysis_fields = [
                    'Findings', 'Value_Realization', 'Implementation_Experience',
                    'Risk_Mitigation', 'Competitive_Advantage', 'Customer_Success',
                    'Product_Feedback', 'Service_Quality', 'Decision_Factors',
                    'Pain_Points', 'Success_Metrics', 'Future_Plans'
                ]
                
                for field in analysis_fields:
                    if field in df.columns and pd.notna(row[field]) and row[field] != 'N/A' and str(row[field]).strip():
                        response_data[field.lower()] = str(row[field])
                
                if self.save_response(response_data):
                    migrated_count += 1
            
            logger.info(f"Migrated {migrated_count} responses from {csv_path}")
            return migrated_count
            
        except Exception as e:
            logger.error(f"Error migrating CSV: {e}")
            return 0
    
    def export_to_csv(self, output_path: str, filters: Optional[Dict] = None) -> bool:
        """Export database data to CSV format"""
        try:
            df = self.get_responses(filters)
            df.to_csv(output_path, index=False)
            logger.info(f"Exported {len(df)} responses to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Count responses
        cursor.execute("SELECT COUNT(*) FROM responses")
        stats['total_responses'] = cursor.fetchone()[0]
        
        # Count by company
        cursor.execute("SELECT company, COUNT(*) FROM responses GROUP BY company")
        stats['responses_by_company'] = dict(cursor.fetchall())
        
        # Count by deal status
        cursor.execute("SELECT deal_status, COUNT(*) FROM responses GROUP BY deal_status")
        stats['responses_by_status'] = dict(cursor.fetchall())
        
        # Count analysis results
        cursor.execute("SELECT COUNT(*) FROM analysis_results")
        stats['total_analyses'] = cursor.fetchone()[0]
        
        # Count labels
        cursor.execute("SELECT COUNT(*) FROM response_labels")
        stats['total_labels'] = cursor.fetchone()[0]
        
        conn.close()
        return stats 