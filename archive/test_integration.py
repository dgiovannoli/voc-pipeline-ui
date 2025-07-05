#!/usr/bin/env python3

"""
Test script for Stage 2 database analyzer and Streamlit integration
"""

import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime

def test_database_creation():
    """Test database schema creation"""
    print("🧪 Testing database creation...")
    
    try:
        # Import the database initialization function
        from app import init_database
        
        success = init_database()
        if success:
            print("✅ Database created successfully")
            
            # Verify tables exist
            with sqlite3.connect("voc_pipeline.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                expected_tables = ['core_responses', 'quote_analysis', 'trend_analysis']
                for table in expected_tables:
                    if table in tables:
                        print(f"✅ Table '{table}' exists")
                    else:
                        print(f"❌ Table '{table}' missing")
                        return False
            
            return True
        else:
            print("❌ Database creation failed")
            return False
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_stage2_analyzer():
    """Test Stage 2 analyzer import and basic functionality"""
    print("\n🧪 Testing Stage 2 analyzer...")
    
    try:
        from enhanced_stage2_analyzer import DatabaseStage2Analyzer
        
        analyzer = DatabaseStage2Analyzer()
        print("✅ Stage 2 analyzer imported successfully")
        
        # Test config loading
        if hasattr(analyzer, 'config') and analyzer.config:
            print("✅ Configuration loaded successfully")
        else:
            print("❌ Configuration loading failed")
            return False
        
        # Test criteria loading
        if hasattr(analyzer, 'criteria') and analyzer.criteria:
            print(f"✅ Loaded {len(analyzer.criteria)} criteria")
        else:
            print("❌ Criteria loading failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Stage 2 analyzer test failed: {e}")
        return False

def test_csv_migration():
    """Test CSV to database migration"""
    print("\n🧪 Testing CSV migration...")
    
    try:
        # Create a test CSV file
        test_data = {
            'response_id': ['test_1', 'test_2'],
            'verbatim_response': ['Test response 1', 'Test response 2'],
            'subject': ['Test Subject 1', 'Test Subject 2'],
            'question': ['Test Question 1', 'Test Question 2'],
            'deal_status': ['closed_won', 'closed_lost'],
            'company': ['Test Company', 'Test Company'],
            'interviewee_name': ['Test Person', 'Test Person'],
            'date_of_interview': ['01/01/2024', '01/01/2024']
        }
        
        test_df = pd.DataFrame(test_data)
        test_csv = 'test_migration.csv'
        test_df.to_csv(test_csv, index=False)
        
        # Test migration
        from app import save_stage1_to_database
        
        success = save_stage1_to_database(test_csv)
        if success:
            print("✅ CSV migration successful")
            
            # Verify data in database
            with sqlite3.connect("voc_pipeline.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM core_responses")
                count = cursor.fetchone()[0]
                print(f"✅ {count} records in database")
            
            # Clean up
            os.remove(test_csv)
            return True
        else:
            print("❌ CSV migration failed")
            return False
    except Exception as e:
        print(f"❌ CSV migration test failed: {e}")
        return False

def test_stage2_analysis():
    """Test Stage 2 analysis execution"""
    print("\n🧪 Testing Stage 2 analysis...")
    
    try:
        from app import run_stage2_analysis
        
        result = run_stage2_analysis()
        print(f"✅ Stage 2 analysis completed with status: {result.get('status')}")
        
        if result.get('status') == 'success':
            print(f"✅ Processed {result.get('quotes_processed', 0)} quotes")
            print(f"✅ Analyzed {result.get('quotes_analyzed', 0)} quotes")
            return True
        elif result.get('status') == 'no_quotes':
            print("ℹ️ No quotes to process (expected for empty database)")
            return True
        else:
            print(f"❌ Stage 2 analysis failed: {result.get('message')}")
            return False
    except Exception as e:
        print(f"❌ Stage 2 analysis test failed: {e}")
        return False

def test_summary_functions():
    """Test summary and trend functions"""
    print("\n🧪 Testing summary functions...")
    
    try:
        from app import get_stage2_summary, get_trend_data
        
        # Test summary
        summary = get_stage2_summary()
        if summary:
            print("✅ Summary function works")
            print(f"   Total quotes: {summary.get('total_quotes', 0)}")
            print(f"   Coverage: {summary.get('coverage_percentage', 0)}%")
        else:
            print("ℹ️ No summary data (expected for empty database)")
        
        # Test trend data
        trend_data = get_trend_data(months=6)
        if trend_data.empty:
            print("ℹ️ No trend data (expected for empty database)")
        else:
            print(f"✅ Trend data retrieved: {len(trend_data)} records")
        
        return True
    except Exception as e:
        print(f"❌ Summary functions test failed: {e}")
        return False

def test_dependencies():
    """Test required dependencies"""
    print("🧪 Testing dependencies...")
    
    required_packages = [
        'streamlit',
        'pandas',
        'sqlite3',
        'yaml',
        'plotly',
        'langchain_openai',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'sqlite3':
                import sqlite3
            elif package == 'python-dotenv':
                import dotenv
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    else:
        print("✅ All dependencies available")
        return True

def main():
    """Run all tests"""
    print("🚀 Starting Stage 2 Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Database Creation", test_database_creation),
        ("Stage 2 Analyzer", test_stage2_analyzer),
        ("CSV Migration", test_csv_migration),
        ("Stage 2 Analysis", test_stage2_analysis),
        ("Summary Functions", test_summary_functions)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Integration is ready.")
        print("\nNext steps:")
        print("1. Run: streamlit run app.py")
        print("2. Upload files and test the workflow")
        print("3. Check Stage 2 analysis and trends")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        print("\nTroubleshooting:")
        print("1. Install missing dependencies")
        print("2. Check file permissions")
        print("3. Verify OpenAI API key")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 