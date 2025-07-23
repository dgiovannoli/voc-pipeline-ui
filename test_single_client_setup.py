#!/usr/bin/env python3
"""
Test script for single client setup
Verifies data access, client ID validation, and response quality
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client
from client_config import validate_client_id, get_client_info, parse_client_id

# Load environment variables
load_dotenv()

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def test_client_configuration():
    """Test client configuration setup"""
    print("🔧 Testing Client Configuration")
    print("=" * 50)
    
    # Test client ID validation
    test_ids = [
        "rev_winloss_2024",
        "acme_product_2024", 
        "techstartup_ux_2024",
        "invalid_id",
        "no_underscore",
        ""
    ]
    
    for client_id in test_ids:
        is_valid = validate_client_id(client_id)
        print(f"Client ID: '{client_id}' -> Valid: {is_valid}")
    
    # Test client ID parsing
    print("\n📝 Testing Client ID Parsing:")
    for client_id in ["rev_winloss_2024", "acme_product_2024"]:
        parsed = parse_client_id(client_id)
        print(f"'{client_id}' -> {parsed}")
    
    # Test client info
    print("\n🏢 Testing Client Info:")
    client_info = get_client_info("rev_winloss_2024")
    if client_info:
        print(f"Company: {client_info.get('company')}")
        print(f"Project: {client_info.get('project')}")
        print(f"Year: {client_info.get('year')}")
        print(f"Description: {client_info.get('description')}")
    else:
        print("❌ No client info found")

def test_database_connection():
    """Test database connection and data access"""
    print("\n🗄️ Testing Database Connection")
    print("=" * 50)
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Missing Supabase configuration")
        return False
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase connection successful")
        
        # Test data access for different client IDs
        test_client_ids = ["rev_winloss_2024", "demo_client", "test_client"]
        
        for client_id in test_client_ids:
            print(f"\n📊 Testing data access for '{client_id}':")
            
            # Test themes
            try:
                themes = supabase.table('stage4_themes').select('count').eq('client_id', client_id).execute()
                theme_count = len(themes.data) if themes.data else 0
                print(f"  Themes: {theme_count}")
            except Exception as e:
                print(f"  Themes: Error - {e}")
            
            # Test findings
            try:
                findings = supabase.table('stage3_findings').select('count').eq('client_id', client_id).execute()
                finding_count = len(findings.data) if findings.data else 0
                print(f"  Findings: {finding_count}")
            except Exception as e:
                print(f"  Findings: Error - {e}")
            
            # Test responses
            try:
                responses = supabase.table('stage1_data_responses').select('count').eq('client_id', client_id).execute()
                response_count = len(responses.data) if responses.data else 0
                print(f"  Responses: {response_count}")
            except Exception as e:
                print(f"  Responses: Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_data_quality():
    """Test data quality and structure"""
    print("\n📈 Testing Data Quality")
    print("=" * 50)
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Missing Supabase configuration")
        return
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Test for client with data
        client_id = "rev_winloss_2024"
        
        # Check themes quality
        themes = supabase.table('stage4_themes').select('*').eq('client_id', client_id).limit(5).execute()
        if themes.data:
            print(f"✅ Found {len(themes.data)} themes")
            
            # Check theme structure
            sample_theme = themes.data[0]
            required_fields = ['theme_title', 'theme_statement', 'theme_strength']
            missing_fields = [field for field in required_fields if not sample_theme.get(field)]
            
            if missing_fields:
                print(f"⚠️ Missing theme fields: {missing_fields}")
            else:
                print("✅ Theme structure looks good")
        else:
            print("❌ No themes found")
        
        # Check findings quality
        findings = supabase.table('stage3_findings').select('*').eq('client_id', client_id).limit(5).execute()
        if findings.data:
            print(f"✅ Found {len(findings.data)} findings")
            
            # Check finding structure
            sample_finding = findings.data[0]
            required_fields = ['finding_statement', 'enhanced_confidence', 'impact_score']
            missing_fields = [field for field in required_fields if not sample_finding.get(field)]
            
            if missing_fields:
                print(f"⚠️ Missing finding fields: {missing_fields}")
            else:
                print("✅ Finding structure looks good")
        else:
            print("❌ No findings found")
        
        # Check responses quality
        responses = supabase.table('stage1_data_responses').select('*').eq('client_id', client_id).limit(5).execute()
        if responses.data:
            print(f"✅ Found {len(responses.data)} responses")
            
            # Check response structure
            sample_response = responses.data[0]
            required_fields = ['verbatim_response', 'company', 'interviewee_name']
            missing_fields = [field for field in required_fields if not sample_response.get(field)]
            
            if missing_fields:
                print(f"⚠️ Missing response fields: {missing_fields}")
            else:
                print("✅ Response structure looks good")
        else:
            print("❌ No responses found")
            
    except Exception as e:
        print(f"❌ Data quality test failed: {e}")

def test_openai_connection():
    """Test OpenAI connection"""
    print("\n🤖 Testing OpenAI Connection")
    print("=" * 50)
    
    if not OPENAI_API_KEY:
        print("❌ Missing OpenAI API key")
        return False
    
    try:
        import openai
        openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Simple test
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        print("✅ OpenAI connection successful")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False

def test_sample_response():
    """Test generating a sample response"""
    print("\n💬 Testing Sample Response Generation")
    print("=" * 50)
    
    if not SUPABASE_URL or not SUPABASE_KEY or not OPENAI_API_KEY:
        print("❌ Missing required configuration")
        return
    
    try:
        from enhanced_client_chat_interface import get_client_data, chat_with_enhanced_data
        
        # Get data for a client
        client_id = "rev_winloss_2024"
        client_data = get_client_data(client_id)
        
        if not client_data or not any([client_data.get('themes'), client_data.get('findings'), client_data.get('responses')]):
            print(f"❌ No data found for client: {client_id}")
            return
        
        print(f"✅ Loaded data for {client_id}:")
        print(f"  Themes: {len(client_data.get('themes', []))}")
        print(f"  Findings: {len(client_data.get('findings', []))}")
        print(f"  Responses: {len(client_data.get('responses', []))}")
        
        # Test a sample question
        test_question = "What are the main themes from our customer interviews?"
        print(f"\n🤔 Testing question: '{test_question}'")
        
        response = chat_with_enhanced_data(test_question, client_data)
        
        print("✅ Response generated successfully!")
        print(f"Response length: {len(response)} characters")
        print(f"Response preview: {response[:200]}...")
        
    except Exception as e:
        print(f"❌ Sample response test failed: {e}")

def main():
    """Run all tests"""
    print("🧪 Single Client Setup Test Suite")
    print("=" * 60)
    
    # Test configuration
    test_client_configuration()
    
    # Test database
    db_ok = test_database_connection()
    
    if db_ok:
        test_data_quality()
    
    # Test OpenAI
    openai_ok = test_openai_connection()
    
    # Test sample response
    if db_ok and openai_ok:
        test_sample_response()
    
    print("\n" + "=" * 60)
    print("🎉 Test suite completed!")
    
    if db_ok and openai_ok:
        print("✅ All systems ready for deployment")
    else:
        print("⚠️ Some issues found - check configuration")

if __name__ == "__main__":
    main() 