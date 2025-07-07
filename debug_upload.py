#!/usr/bin/env python3
"""
Debug script to diagnose upload issues with Leila's file
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
import tiktoken
from voc_pipeline.modular_processor import ModularProcessor

def analyze_transcript(transcript_path: str):
    """Analyze a transcript file to understand chunking and processing"""
    
    print(f"🔍 Analyzing transcript: {transcript_path}")
    print("=" * 60)
    
    # Check if file exists
    if not os.path.exists(transcript_path):
        print(f"❌ File not found: {transcript_path}")
        return
    
    # Load transcript content
    if transcript_path.lower().endswith(".docx"):
        try:
            from docx import Document
            doc = Document(transcript_path)
            full_text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            print(f"📄 Loaded DOCX file with {len(full_text)} characters")
        except ImportError:
            print("❌ python-docx not available")
            return
    else:
        with open(transcript_path, encoding="utf-8") as f:
            full_text = f.read()
        print(f"📄 Loaded text file with {len(full_text)} characters")
    
    # Token analysis
    encoding = tiktoken.get_encoding("cl100k_base")
    total_tokens = len(encoding.encode(full_text))
    print(f"🔢 Total tokens: {total_tokens:,}")
    
    # Text preview
    print(f"\n📝 Text preview (first 500 chars):")
    print("-" * 40)
    print(full_text[:500])
    print("-" * 40)
    
    # Check for Q&A patterns
    qa_patterns = [
        r'Q:\s*', r'Question:\s*', r'Interviewer:\s*', r'Interviewee:\s*',
        r'Speaker \d+', r'\n[A-Za-z\s]+:\s*'
    ]
    
    import re
    found_patterns = []
    for pattern in qa_patterns:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        if matches:
            found_patterns.append((pattern, len(matches)))
    
    print(f"\n🎯 Q&A Patterns found:")
    for pattern, count in found_patterns:
        print(f"  {pattern}: {count} matches")
    
    # Test chunking
    print(f"\n✂️ Testing chunking...")
    processor = ModularProcessor()
    chunks = processor._create_chunks(full_text, target_tokens=2000, overlap_tokens=200)
    
    print(f"📦 Created {len(chunks)} chunks")
    print(f"📊 Average chunk size: {sum(len(encoding.encode(chunk)) for chunk in chunks) // len(chunks)} tokens")
    
    # Show chunk previews
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        print(f"\n📋 Chunk {i+1} preview (first 200 chars):")
        print("-" * 30)
        print(chunk[:200])
        print("-" * 30)
    
    # Test processing one chunk
    print(f"\n🧪 Testing processing of first chunk...")
    try:
        from prompts.core_extraction import CORE_EXTRACTION_PROMPT
        from langchain.prompts import PromptTemplate
        from langchain_openai import ChatOpenAI
        
        # Create LLM
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo-16k",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=4096,
            temperature=0.1
        )
        
        # Process first chunk
        chunk_id = f"test_company_test_interviewee_1"
        prompt_template = PromptTemplate(
            input_variables=["response_id", "company", "interviewee_name", "deal_status", "date_of_interview", "chunk_text"],
            template=CORE_EXTRACTION_PROMPT
        )
        chain = prompt_template | llm
        
        result = chain.invoke({
            "response_id": chunk_id,
            "company": "Test Company",
            "interviewee_name": "Test Interviewee",
            "deal_status": "closed_won",
            "date_of_interview": "2024-01-01",
            "chunk_text": chunks[0] if chunks else "Test content"
        })
        
        if hasattr(result, 'content'):
            response_text = result.content.strip()
        else:
            response_text = str(result).strip()
        
        print(f"✅ LLM response received ({len(response_text)} chars)")
        print(f"📄 Response preview:")
        print("-" * 30)
        print(response_text[:500])
        print("-" * 30)
        
        # Try to parse JSON
        try:
            responses = json.loads(response_text)
            if isinstance(responses, list):
                print(f"✅ Parsed {len(responses)} responses from JSON")
                for i, resp in enumerate(responses[:2]):  # Show first 2
                    print(f"  Response {i+1}: {resp.get('subject', 'No subject')}")
            else:
                print(f"✅ Parsed 1 response from JSON")
                print(f"  Subject: {responses.get('subject', 'No subject')}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"Raw response: {response_text}")
            
    except Exception as e:
        print(f"❌ Processing test failed: {e}")

def check_supabase_data():
    """Check what's currently in Supabase"""
    print(f"\n🗄️ Checking Supabase data...")
    print("=" * 60)
    
    try:
        from supabase_database import SupabaseDatabase
        db = SupabaseDatabase()
        
        # Get all core responses
        responses = db.get_core_responses()
        print(f"📊 Total core responses in database: {len(responses)}")
        
        if len(responses) > 0:
            print(f"📋 Sample response:")
            sample = responses.iloc[0]
            print(f"  ID: {sample.get('response_id', 'N/A')}")
            print(f"  Company: {sample.get('company', 'N/A')}")
            print(f"  Interviewee: {sample.get('interviewee_name', 'N/A')}")
            print(f"  Subject: {sample.get('subject', 'N/A')}")
            print(f"  Verbatim preview: {sample.get('verbatim_response', 'N/A')[:100]}...")
        
        # Check for Leila specifically
        leila_responses = [r for r in responses.to_dict('records') if 'Leila' in str(r.get('interviewee_name', ''))]
        print(f"👤 Leila responses found: {len(leila_responses)}")
        
    except Exception as e:
        print(f"❌ Supabase check failed: {e}")

def main():
    """Main diagnostic function"""
    print("🔧 VOC Pipeline Upload Diagnostic")
    print("=" * 60)
    
    # Check for uploaded files
    upload_dir = "uploads"
    if os.path.exists(upload_dir):
        files = [f for f in os.listdir(upload_dir) if f.endswith(('.docx', '.txt'))]
        print(f"📁 Found {len(files)} files in uploads directory:")
        for f in files:
            print(f"  - {f}")
        
        # Analyze first file that might be Leila's
        leila_files = [f for f in files if 'leila' in f.lower() or 'vaez' in f.lower()]
        if leila_files:
            analyze_transcript(os.path.join(upload_dir, leila_files[0]))
        elif files:
            analyze_transcript(os.path.join(upload_dir, files[0]))
    else:
        print(f"❌ Uploads directory not found: {upload_dir}")
    
    # Check Supabase
    check_supabase_data()
    
    print(f"\n💡 Recommendations:")
    print("1. Check if the transcript file contains sufficient Q&A content")
    print("2. Verify the chunking is creating multiple chunks")
    print("3. Ensure the LLM is returning valid JSON responses")
    print("4. Check for any processing errors in the logs")

if __name__ == "__main__":
    main() 