#!/usr/bin/env python3
"""
Simple database explorer for VOC Pipeline
"""

import sqlite3
import pandas as pd

def explore_database():
    """Explore the VOC pipeline database"""
    
    with sqlite3.connect("voc_pipeline.db") as conn:
        print("🗄️ VOC Pipeline Database Explorer")
        print("=" * 50)
        
        # Show tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📋 Tables found: {len(tables)}")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} records")
        
        print("\n" + "=" * 50)
        
        # Show sample data from main tables
        print("📊 Sample Data from core_responses:")
        df = pd.read_sql_query("SELECT * FROM core_responses LIMIT 3", conn)
        print(df[['response_id', 'subject', 'company', 'deal_status']].to_string())
        
        print("\n📊 Sample Data from quote_analysis:")
        df = pd.read_sql_query("SELECT * FROM quote_analysis LIMIT 5", conn)
        print(df[['quote_id', 'criterion', 'score', 'deal_weighted_score']].to_string())
        
        print("\n📈 Summary Statistics:")
        cursor.execute("""
            SELECT 
                criterion,
                COUNT(*) as mentions,
                AVG(deal_weighted_score) as avg_score,
                MIN(deal_weighted_score) as min_score,
                MAX(deal_weighted_score) as max_score
            FROM quote_analysis 
            GROUP BY criterion
            ORDER BY avg_score DESC
        """)
        
        results = cursor.fetchall()
        print(f"{'Criterion':<25} {'Mentions':<8} {'Avg Score':<10} {'Range':<10}")
        print("-" * 55)
        for row in results:
            criterion, mentions, avg_score, min_score, max_score = row
            print(f"{criterion:<25} {mentions:<8} {avg_score:<10.2f} {min_score}-{max_score:<6}")

if __name__ == "__main__":
    explore_database() 