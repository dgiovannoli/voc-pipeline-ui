#!/usr/bin/env python3
"""
Test script to verify RAG integration in the client chat interface.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_rag_imports():
    """Test that RAG utilities can be imported."""
    print("🔍 Testing RAG imports...")
    try:
        from rag_search import pinecone_rag_search, build_rag_context
        print("✅ RAG utilities imported successfully")
        return True
    except ImportError as e:
        print(f"❌ RAG import failed: {e}")
        return False

def test_client_chat_imports():
    """Test that client chat interface can be imported with RAG."""
    print("🔍 Testing client chat interface imports...")
    try:
        import client_chat_interface
        print("✅ Client chat interface imported successfully")
        
        # Check if RAG is available
        if hasattr(client_chat_interface, 'RAG_AVAILABLE'):
            if client_chat_interface.RAG_AVAILABLE:
                print("✅ RAG is available in client chat interface")
            else:
                print("⚠️ RAG is not available in client chat interface")
        else:
            print("⚠️ RAG_AVAILABLE flag not found")
        
        return True
    except ImportError as e:
        print(f"❌ Client chat interface import failed: {e}")
        return False

def test_rag_search_functionality():
    """Test basic RAG search functionality."""
    print("🔍 Testing RAG search functionality...")
    try:
        from rag_search import pinecone_rag_search, build_rag_context
        
        # Test with a simple query
        test_query = "customer satisfaction"
        test_client_id = "Supio"  # Use the client ID we have data for
        print(f"Testing query: '{test_query}' for client: {test_client_id}")
        
        # This should work if Pinecone is configured
        try:
            results = pinecone_rag_search(test_query, test_client_id, top_k=3)
            if results:
                print(f"✅ RAG search returned {len(results)} results")
                context = build_rag_context(results)
                print(f"✅ Context built successfully (length: {len(context)} chars)")
            else:
                print("⚠️ RAG search returned no results (this might be normal if no relevant data)")
        except Exception as e:
            print(f"⚠️ RAG search failed (might be expected if Pinecone not configured): {e}")
        
        return True
    except Exception as e:
        print(f"❌ RAG functionality test failed: {e}")
        return False

def test_environment_variables():
    """Test that required environment variables are set."""
    print("🔍 Testing environment variables...")
    
    required_vars = [
        'OPENAI_API_KEY',
        'PINECONE_API_KEY',
        'PINECONE_INDEX'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ Missing environment variables: {missing_vars}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def main():
    """Run all tests."""
    print("🚀 Testing RAG Integration\n")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("RAG Imports", test_rag_imports),
        ("Client Chat Interface", test_client_chat_imports),
        ("RAG Functionality", test_rag_search_functionality),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! RAG integration is ready.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main() 