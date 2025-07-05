#!/usr/bin/env python3
"""
Test script for the VOC database functionality
"""
import os
import sys
import pandas as pd
from database import VOCDatabase

def test_database():
    print("🧪 Testing VOC Database...")
    
    # Initialize database
    db = VOCDatabase("test_voc_pipeline.db")
    print("✅ Database initialized")
    
    # Test saving a response
    test_response = {
        'response_id': 'test_001',
        'verbatim_response': 'This is a test response about product features.',
        'subject': 'Product Features',
        'question': 'What did you think about the product features?',
        'deal_status': 'closed_won',
        'company': 'Test Company',
        'interviewee_name': 'Test User',
        'date_of_interview': '2024-01-15',
        'findings': 'Customer found the features very useful',
        'value_realization': 'Improved efficiency by 40%',
        'implementation_experience': 'Smooth onboarding process'
    }
    
    success = db.save_response(test_response)
    print(f"✅ Save response: {'SUCCESS' if success else 'FAILED'}")
    
    # Test adding a label
    success = db.add_label('test_001', 'sentiment', 'positive', 0.9)
    print(f"✅ Add label: {'SUCCESS' if success else 'FAILED'}")
    
    # Test adding quality metric
    success = db.add_quality_metric('test_001', 'word_count', 15.0, {'details': 'Good length'})
    print(f"✅ Add quality metric: {'SUCCESS' if success else 'FAILED'}")
    
    # Test getting responses
    df = db.get_responses()
    print(f"✅ Get responses: Found {len(df)} responses")
    
    # Test getting specific response
    response = db.get_response_by_id('test_001')
    if response:
        print(f"✅ Get response by ID: Found response with {len(response.get('analyses', {}))} analyses")
    else:
        print("❌ Get response by ID: FAILED")
    
    # Test statistics
    stats = db.get_stats()
    print(f"✅ Get stats: {stats['total_responses']} responses, {stats['total_analyses']} analyses")
    
    # Test filtering
    filtered_df = db.get_responses({'company': 'Test Company'})
    print(f"✅ Filter responses: Found {len(filtered_df)} responses for Test Company")
    
    # Test CSV export
    success = db.export_to_csv('test_export.csv')
    print(f"✅ Export to CSV: {'SUCCESS' if success else 'FAILED'}")
    
    # Clean up
    if os.path.exists('test_voc_pipeline.db'):
        os.remove('test_voc_pipeline.db')
    if os.path.exists('test_export.csv'):
        os.remove('test_export.csv')
    
    print("🎉 Database test completed successfully!")

if __name__ == "__main__":
    test_database() 