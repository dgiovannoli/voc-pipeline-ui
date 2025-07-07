#!/usr/bin/env python3

import docx
import os

def extract_word_content(filename):
    """Extract text from a Word document"""
    try:
        doc = docx.Document(filename)
        full_text = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                full_text.append(paragraph.text.strip())
        
        return '\n'.join(full_text)
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return None

def analyze_cyrus_transcript():
    filename = "uploads/Interview with Cyrus Nazarian, Attorney at Altair Law.docx"
    
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return
    
    print("EXTRACTING ORIGINAL TRANSCRIPT:")
    print("="*80)
    
    content = extract_word_content(filename)
    if content:
        print(content)
        print("\n" + "="*80)
        print(f"Total characters: {len(content)}")
        print(f"Total lines: {len(content.split(chr(10)))}")
        
        # Try to identify potential Q&A sections
        lines = content.split(chr(10))
        qa_sections = []
        current_section = []
        
        for line in lines:
            if line.strip():
                current_section.append(line)
            elif current_section:
                qa_sections.append('\n'.join(current_section))
                current_section = []
        
        if current_section:
            qa_sections.append('\n'.join(current_section))
        
        print(f"\nPotential Q&A sections identified: {len(qa_sections)}")
        
        for i, section in enumerate(qa_sections[:5]):  # Show first 5 sections
            print(f"\n--- Section {i+1} ---")
            print(section[:200] + "..." if len(section) > 200 else section)
    else:
        print("Failed to extract content")

if __name__ == "__main__":
    analyze_cyrus_transcript() 