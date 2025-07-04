import os
import sys
import logging
import click
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.document_loaders import Docx2txtLoader
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_text_splitters import RecursiveCharacterTextSplitter, TokenTextSplitter
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import csv
from io import StringIO
import math
import tiktoken

# Add database import
try:
    from database import VOCDatabase
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# Set up logging
logging.basicConfig(filename="qc.log",
                    level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

def normalize_response_id(company: str, interviewee: str, chunk_index: int) -> str:
    """Create normalized, unique Response ID"""
    parts = []
    if company:
        parts.append(re.sub(r'[^a-zA-Z0-9]', '', company))
    if interviewee:
        parts.append(re.sub(r'[^a-zA-Z0-9]', '', interviewee))
    if not parts:
        parts.append("Response")
    return f"{'_'.join(parts)}_{chunk_index + 1}"

def extract_qa_segments(text: str) -> list:
    """Extract Q&A segments from transcript text"""
    segments = []
    found_qa = False
    # Split on common Q&A patterns
    qa_patterns = [
        r'Q:\s*(.*?)(?=A:\s*)',
        r'Question:\s*(.*?)(?=Answer:\s*)',
        r'Interviewer:\s*(.*?)(?=Interviewee:\s*)',
        r'Drew Giovannoli:\s*(.*?)(?=Yusuf Elmarakby:\s*)',
        r'Yusuf Elmarakby:\s*(.*?)(?=Drew Giovannoli:\s*)'
    ]
    for pattern in qa_patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            found_qa = True
            for match in matches:
                if len(match.strip()) > 20:
                    segments.append(match.strip())
            break
    # If no Q&A patterns found, split on speaker turns
    if not segments:
        # Speaker X (00:00): or Speaker X:
        speaker_pattern = r'(Speaker \d+ \(\d{2}:\d{2}\):|Speaker \d+:|[A-Za-z\s]+:)\s*'
        parts = re.split(speaker_pattern, text)
        # parts alternates: [pre, speaker, text, speaker, text, ...]
        for i in range(1, len(parts), 2):
            speaker = parts[i]
            content = parts[i+1] if i+1 < len(parts) else ''
            chunk = f"{speaker} {content}".strip()
            if len(chunk) > 20:
                segments.append(chunk)
    print(f"[DEBUG] Extracted {len(segments)} segments from transcript.", file=sys.stderr)
    return segments, found_qa

def create_qa_aware_chunks(text: str, target_tokens: int = 8000, overlap_tokens: int = 600) -> list:
    """
    Create Q&A-aware chunks optimized for quality over quantity.
    
    Strategy:
    1. First extract Q&A segments to preserve conversation flow
    2. Group Q&A segments into larger chunks (~8K tokens) for better context
    3. Use token-based splitting to respect the 16K limit
    4. Preserve Q&A boundaries - never split mid-Q&A
    5. Focus on quality: fewer chunks but richer insights
    """
    # Initialize tokenizer for gpt-3.5-turbo-16k
    try:
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo-16k")
    except:
        # Fallback to cl100k_base encoding
        encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(text: str) -> int:
        """Count tokens in text"""
        return len(encoding.encode(text))
    
    # Step 1: Extract Q&A segments
    qa_segments, found_qa = extract_qa_segments(text)
    
    if not qa_segments:
        # Fallback: split by speaker turns or sentences
        speaker_pattern = r'(Speaker \d+ \(\d{2}:\d{2}\):|Speaker \d+:|[A-Za-z\s]+:)\s*'
        parts = re.split(speaker_pattern, text)
        qa_segments = []
        for i in range(1, len(parts), 2):
            speaker = parts[i] if i < len(parts) else ''
            content = parts[i+1] if i+1 < len(parts) else ''
            chunk = f"{speaker} {content}".strip()
            if len(chunk) > 20:
                qa_segments.append(chunk)
    
    # Step 2: Group Q&A segments into larger chunks for better context
    chunks = []
    current_chunk = ""
    current_tokens = 0
    segments_in_chunk = 0
    
    for segment in qa_segments:
        segment_tokens = count_tokens(segment)
        
        # Start new chunk if:
        # 1. Adding this segment would exceed target tokens, OR
        # 2. We already have 8-10 segments in current chunk (for better context)
        if ((current_tokens + segment_tokens > target_tokens and current_chunk) or 
            (segments_in_chunk >= 10 and current_chunk)):
            chunks.append(current_chunk.strip())
            
            # Start new chunk with overlap from previous chunk
            if overlap_tokens > 0:
                # Find a good overlap point (preferably at Q&A boundary)
                overlap_text = current_chunk[-overlap_tokens*4:]  # Rough character estimate
                # Try to find a Q&A boundary in the overlap
                qa_boundary_patterns = [
                    r'Q:\s*',
                    r'Question:\s*',
                    r'Interviewer:\s*',
                    r'Speaker \d+',
                    r'\n[A-Za-z\s]+:\s*'
                ]
                
                overlap_start = 0
                for pattern in qa_boundary_patterns:
                    match = re.search(pattern, overlap_text, re.IGNORECASE)
                    if match:
                        overlap_start = match.start()
                        break
                
                current_chunk = overlap_text[overlap_start:] + "\n\n" + segment
                current_tokens = count_tokens(current_chunk)
                segments_in_chunk = 1
            else:
                current_chunk = segment
                current_tokens = segment_tokens
                segments_in_chunk = 1
        else:
            # Add to current chunk
            if current_chunk:
                current_chunk += "\n\n" + segment
            else:
                current_chunk = segment
            current_tokens += segment_tokens
            segments_in_chunk += 1
    
    # Add the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # Step 3: If we still have very large chunks, use token-based splitting
    final_chunks = []
    for chunk in chunks:
        chunk_tokens = count_tokens(chunk)
        
        if chunk_tokens <= target_tokens:
            final_chunks.append(chunk)
        else:
            # Use token-based splitter for oversized chunks
            splitter = TokenTextSplitter(
                encoding=encoding,
                chunk_size=target_tokens,
                chunk_overlap=overlap_tokens,
                separators=['\n\n', '\n', '. ', '? ', '! ', ' ']
            )
            sub_chunks = splitter.split_text(chunk)
            final_chunks.extend(sub_chunks)
    
    print(f"[DEBUG] Created {len(final_chunks)} chunks with Q&A-aware token-based chunking.", file=sys.stderr)
    print(f"[DEBUG] Average chunk size: {sum(count_tokens(c) for c in final_chunks) // len(final_chunks) if final_chunks else 0} tokens", file=sys.stderr)
    
    return final_chunks, found_qa

def is_qa_chunk(chunk_text: str, found_qa: bool = True) -> bool:
    """Check if chunk contains actual Q&A content"""
    if not chunk_text.strip():
        return False
    if not found_qa:
        # If no Q/A patterns found, allow all speaker turns through
        return True
    # Check for question indicators
    question_indicators = [
        '?', 'what', 'how', 'why', 'when', 'where', 'which', 'who',
        'could you', 'can you', 'would you', 'do you', 'did you',
        'tell me', 'describe', 'explain', 'walk me through'
    ]
    text_lower = chunk_text.lower()
    has_question = any(indicator in text_lower for indicator in question_indicators)
    has_content = len(chunk_text.strip()) > 50
    return has_question and has_content

def is_low_value_response(text: str) -> bool:
    """Check if response is low value (too short, vague, or non-substantive)"""
    text_clean = text.strip()
    
    # Too short responses
    if len(text_clean) < 30:  # Increased from 20 to allow more context
        return True
    
    # Very vague responses that are just acknowledgments
    acknowledgment_only = [
        'yeah',
        'yes',
        'no',
        'okay',
        'ok',
        'sure',
        'right',
        'uh huh',
        'mm hmm',
        'i see',
        'got it',
        'understood'
    ]
    
    # If response is just acknowledgments, it's low value
    words = text_clean.lower().split()
    if len(words) <= 2 and all(word in acknowledgment_only for word in words):
        return True
    
    # Extremely vague responses
    extremely_vague = [
        'nothing stands out',
        'pretty straightforward',
        'i don\'t know',
        'not really',
        'i guess',
        'maybe',
        'i think so',
        'i don\'t think so',
        'no idea',
        'not sure',
        'can\'t remember',
        'forget',
        'that was an awesome interview',
        'thank you for your time',
        'yeah, i can\'t think of anything else',
        'correct, it\'s just me',
        'i\'m the only one',
        'that\'s it',
        'that\'s all',
        'nothing else',
        'no other thoughts',
        'no other feedback'
    ]
    
    text_lower = text_clean.lower()
    for phrase in extremely_vague:
        if phrase in text_lower and len(text_clean) < 80:  # Increased threshold to allow more context
            return True
    
    # Filter out technical setup/testing quotes
    setup_phrases = [
        'can you hear me',
        'check check check',
        'one sec',
        'let me switch',
        'headphones',
        'nice to meet you',
        'how are you',
        'alright cool',
        'a b c d e f g',
        '1 2 3',
        'hello hello',
        'i can hear you',
        'now i can hear you',
        'testing testing',
        'mic check',
        'sound check'
    ]
    
    # Check if response contains multiple setup phrases
    setup_count = sum(1 for phrase in setup_phrases if phrase in text_lower)
    if setup_count >= 3:  # If 3 or more setup phrases, it's likely technical setup
        return True
    
    # Filter out responses that are mostly technical setup
    setup_words = ['hear', 'check', 'headphones', 'switch', 'sec', 'hello', 'alright', 'cool', 'testing']
    setup_word_count = sum(text_lower.count(word) for word in setup_words)
    if setup_word_count > len(text_lower.split()) * 0.4:  # More than 40% setup words
        return True
    
    # Enhanced quality check: look for specific content indicators
    quality_indicators = [
        'because', 'since', 'when', 'where', 'how', 'what', 'why',
        'for example', 'specifically', 'in particular', 'such as',
        'percent', '%', 'dollars', '$', 'hours', 'minutes', 'days',
        'workflow', 'process', 'integration', 'tool', 'software',
        'accuracy', 'efficiency', 'quality', 'speed', 'time',
        'before', 'after', 'compared', 'versus', 'vs', 'different',
        'improved', 'better', 'worse', 'faster', 'slower',
        'deposition', 'transcript', 'legal', 'court', 'attorney',
        'body cam', 'video', 'audio', 'recording', 'transcription'
    ]
    
    # If response has multiple quality indicators, it's likely valuable
    quality_count = sum(1 for indicator in quality_indicators if indicator in text_lower)
    if quality_count >= 2 and len(text_clean) > 50:
        return False  # This is likely valuable content
    
    # Check for specific examples and detailed explanations
    example_patterns = [
        r'\d+%',  # Percentages
        r'\$\d+',  # Dollar amounts
        r'\d+ hours?',  # Time periods
        r'\d+ minutes?',
        r'for example',
        r'such as',
        r'specifically',
        r'in particular',
        r'when i',
        r'where i',
        r'how i',
        r'what i'
    ]
    
    example_count = sum(1 for pattern in example_patterns if re.search(pattern, text_lower))
    if example_count >= 1 and len(text_clean) > 60:
        return False  # This has specific examples
    
    return False

def remove_disfluencies(text: str) -> str:
    # Remove common disfluencies unless they are part of a longer phrase
    disfluencies = [r'\bum\b', r'\buh\b', r'\byou know\b', r'\bso\b', r'\blike\b', r'\ber\b', r'\bwell\b']
    for pattern in disfluencies:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    # Remove extra spaces left behind
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_verbatim_response(text: str, interviewer_names=None) -> str:
    if interviewer_names is None:
        interviewer_names = ["Q:", "A:", "Interviewer:", "Drew Giovannoli:", "Brian:", "Yusuf Elmarakby:"]
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        l = line.strip()
        # Remove interview titles/headings
        if l.lower().startswith("an interview with") or l.lower().startswith("interview with"):
            continue
        # Remove speaker labels, timestamps, Q:/A: tags
        if any(l.startswith(name) for name in interviewer_names):
            continue
        if re.match(r'^Speaker \d+ \(\d{2}:\d{2}\):', l):
            continue
        if re.match(r'^\(\d{2}:\d{2}\):', l):
            continue
        # Skip lines that are just questions (but keep questions that are part of longer content)
        if l.endswith("?") and len(l) < 50:
            continue
        cleaned_lines.append(line)
    cleaned = " ".join(cleaned_lines).strip()
    # Remove leading speaker timestamps like "Speaker 1 (01:52):"
    cleaned = re.sub(r'^Speaker \d+ \(\d{2}:\d{2}\):\s*', '', cleaned)
    # Remove trailing timestamps like "(03:07):"
    cleaned = re.sub(r'\(\d{2}:\d{2}\):\s*$', '', cleaned)
    # Remove speaker labels at start of lines: "Drew Giovannoli:", etc.
    # But be more careful not to remove content that looks like speaker labels
    cleaned = re.sub(r'^(Speaker \d+|Drew Giovannoli|Brian|Yusuf Elmarakby):\s*', '', cleaned, flags=re.MULTILINE)
    # Remove question context - look for patterns like "Q: What do you think?" and remove
    cleaned = re.sub(r'^Q:\s*[^A]*?(?=A:|$)', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'^Question:\s*[^A]*?(?=Answer:|$)', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    # Remove interviewer questions that might be mixed in
    cleaned = re.sub(r'Interviewer:\s*[^I]*?(?=Interviewee:|$)', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    # Clean up extra whitespace and newlines, but preserve paragraph breaks
    cleaned = re.sub(r'\n+', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    # Remove disfluencies
    cleaned = remove_disfluencies(cleaned)
    # Ensure we have meaningful content (be less strict)
    if len(cleaned) < 5:
        return ""
    return cleaned

def format_date(date_str: str) -> str:
    """Format date to MM/DD/YYYY"""
    try:
        # Try to parse various date formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d', '%m-%d-%Y']:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%m/%d/%Y')
            except ValueError:
                continue
        # If no format works, return original
        return date_str
    except:
        return date_str

def normalize_deal_status(status: str) -> str:
    """Normalize deal status to standard format"""
    status_lower = status.lower().strip()
    if 'won' in status_lower:
        return 'closed won'
    elif 'lost' in status_lower:
        return 'closed lost'
    else:
        return 'no decision'

def infer_subject_from_text(text: str) -> str:
    """Infer subject from text content"""
    text_lower = text.lower()
    
    # Keyword-based subject inference
    if any(word in text_lower for word in ['product', 'feature', 'functionality', 'tool']):
        return 'Product Features'
    elif any(word in text_lower for word in ['price', 'cost', 'expensive', 'cheap', 'budget']):
        return 'Pricing'
    elif any(word in text_lower for word in ['implement', 'setup', 'onboard', 'deploy']):
        return 'Implementation'
    elif any(word in text_lower for word in ['support', 'service', 'help', 'assist']):
        return 'Support'
    elif any(word in text_lower for word in ['integrate', 'connect', 'api', 'database']):
        return 'Integration'
    elif any(word in text_lower for word in ['decision', 'choose', 'select', 'evaluate']):
        return 'Decision Making'
    else:
        return 'General Feedback'

def _process_transcript_impl(
    transcript_path: str,
    client: str,
    company: str,
    interviewee: str,
    deal_status: str,
    date_of_interview: str,
) -> None:
    """
    Load the transcript, run the full Response Data Table prompt,
    and emit raw CSV to stdout.
    """
    # Load environment variables
    load_dotenv()
    
    # Debug: Check if API key is loaded
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment")
        return
    
    # Load transcript
    if transcript_path.lower().endswith(".docx"):
        loader = Docx2txtLoader(transcript_path)
        # 1) Load full transcript
        docs = loader.load()
        full_text = docs[0].page_content
    else:
        full_text = open(transcript_path, encoding="utf-8").read()
    
    if not full_text.strip():
        print("ERROR: Transcript is empty")
        return
    
    # Create enhanced prompt template optimized for quality over quantity
    prompt_template = PromptTemplate(
        input_variables=["response_id", "key_insight", "chunk_text", "company", "company_name", "interviewee_name", "deal_status", "date_of_interview"],
        template="""CRITICAL INSTRUCTIONS FOR ENHANCED QUALITY ANALYSIS:
- You have access to focused context windows (~7K tokens) containing 6-8 Q&A exchanges.
- Extract the 1-2 RICHEST, MOST DETAILED insights from this chunk, prioritizing:
  1. **Comprehensive Customer Experiences**: Complete scenarios with full context, specific examples, detailed explanations, and quantitative details
  2. **Quantitative Feedback**: Specific metrics, timelines, ROI discussions, pricing details, accuracy percentages, workload distributions
  3. **Comparative Analysis**: Before/after comparisons, competitive evaluations with specific differentiators and performance metrics
  4. **Integration Requirements**: Workflow details, tool integration needs, process changes, technical specifications
  5. **Strategic Perspectives**: Decision factors, risk assessments, future planning, business impact

EXTRACTION STRATEGY:
- Identify the 1-2 richest, most comprehensive responses in this chunk
- Extract the COMPLETE verbatim response for each with full context and conversation flow
- Create comprehensive key insights that capture the main themes and specific details
- Focus on responses that provide complete context and detailed explanations
- Choose responses that cover different aspects or themes when possible
- If only one high-quality response exists, extract just that one
- Prioritize responses with specific examples, metrics, and actionable insights

VERBATIM RESPONSE RULES:
- Include the COMPLETE response text (300-800 words for optimal context and richness)
- Preserve ALL context, examples, specific details, and quantitative information
- Include relevant parts of the conversation flow for better understanding
- Include follow-up questions and clarifications that add context
- Remove only speaker labels, timestamps, and interviewer prompts
- Keep filler words if they add emphasis or meaning
- Maintain the natural flow and structure of the response
- Include specific examples, metrics, detailed explanations, and follow-up context
- Preserve comparative language and specific differentiators
- Include workflow details, process descriptions, and technical specifications

QUALITY-FOCUSED INSIGHTS:
- Extract the 1-2 most comprehensive insights from the richest responses
- Focus on responses that provide complete context and detailed explanations
- Ensure each verbatim response captures the full conversation context
- Choose responses that cover different topics or perspectives when possible
- Only extract if the response contains substantial, actionable content
- Prioritize responses with specific metrics, examples, and detailed workflows

DIFFERENTIATION STRATEGY:
- When multiple responses cover similar topics, extract the most detailed and specific one
- Focus on responses that provide unique perspectives or specific examples
- Include responses that show different aspects of the same topic (e.g., different use cases, workflows, or pain points)
- Prioritize responses with quantitative details, specific processes, or technical specifications
- Choose responses that provide the most complete picture of customer experiences

Analyze the provided interview chunk and extract the 1-2 RICHEST, MOST COMPREHENSIVE insights from the most detailed responses. Return ONLY a JSON array containing one or two objects:

[
  {{
    "response_id": "{response_id}_1",
    "key_insight": "first_comprehensive_insight_summary_with_specific_details",
    "verbatim_response": "first_complete_verbatim_response_with_full_context_and_specific_examples",
    "subject": "brief_subject_description_1",
    "question": "what_question_this_answers_1",
    "deal_status": "{deal_status}",
    "company": "{company}",
    "interviewee_name": "{interviewee_name}",
    "date_of_interview": "{date_of_interview}",
    "findings": "key_finding_summary_with_specific_details_1",
    "value_realization": "value_or_roi_metrics_with_quantitative_details_1",
    "implementation_experience": "implementation_details_with_workflow_specifics_1",
    "risk_mitigation": "risk_mitigation_approaches_with_specific_strategies_1",
    "competitive_advantage": "competitive_positioning_with_specific_differentiators_1",
    "customer_success": "customer_success_factors_with_measurable_outcomes_1",
    "product_feedback": "product_feature_feedback_with_specific_examples_1",
    "service_quality": "service_quality_assessment_with_quantitative_metrics_1",
    "decision_factors": "decision_influencing_factors_with_specific_criteria_1",
    "pain_points": "challenges_or_pain_points_with_detailed_context_1",
    "success_metrics": "success_criteria_and_metrics_with_specific_measurements_1",
    "future_plans": "future_plans_or_expansion_with_specific_timelines_1"
  }},
  {{
    "response_id": "{response_id}_2",
    "key_insight": "second_comprehensive_insight_summary_with_specific_details",
    "verbatim_response": "second_complete_verbatim_response_with_full_context_and_specific_examples",
    "subject": "brief_subject_description_2",
    "question": "what_question_this_answers_2",
    "deal_status": "{deal_status}",
    "company": "{company}",
    "interviewee_name": "{interviewee_name}",
    "date_of_interview": "{date_of_interview}",
    "findings": "key_finding_summary_with_specific_details_2",
    "value_realization": "value_or_roi_metrics_with_quantitative_details_2",
    "implementation_experience": "implementation_details_with_workflow_specifics_2",
    "risk_mitigation": "risk_mitigation_approaches_with_specific_strategies_2",
    "competitive_advantage": "competitive_positioning_with_specific_differentiators_2",
    "customer_success": "customer_success_factors_with_measurable_outcomes_2",
    "product_feedback": "product_feature_feedback_with_specific_examples_2",
    "service_quality": "service_quality_assessment_with_quantitative_metrics_2",
    "decision_factors": "decision_influencing_factors_with_specific_criteria_2",
    "pain_points": "challenges_or_pain_points_with_detailed_context_2",
    "success_metrics": "success_criteria_and_metrics_with_specific_measurements_2",
    "future_plans": "future_plans_or_expansion_with_specific_timelines_2"
  }}
]

Guidelines:
- Extract the 1-2 richest, most comprehensive insights per chunk
- Subject categories: Product Features, Process, Pricing, Support, Integration, Decision Making, Workflow Optimization
- Use "N/A" for fields that don't apply
- Ensure all fields are populated with specific, actionable content
- Return ONLY the JSON array, no other text
- Focus on responses with specific examples, metrics, detailed explanations, and full context
- Choose responses that provide the most complete picture and actionable insights
- If only one rich insight exists, return an array with just one object
- Skip chunks that only contain low-quality content (acknowledgments, thank yous, etc.)
- Prioritize responses that show different aspects of similar topics (e.g., different use cases, workflows, or specific pain points)

Interview chunk to analyze:
{chunk_text}"""
    )
    
    # Create LLM chain (RunnableSequence) - using ChatOpenAI for gpt-3.5-turbo-16k
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo-16k",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        max_tokens=4096,
        temperature=0.1
    )
    chain = prompt_template | llm
    
    # 2) Use quality-focused chunking targeting ~5 insights per interview (7K tokens)
    # Balance between context and granularity for consistent high-quality insights
    qa_segments, found_qa = create_qa_aware_chunks(full_text, target_tokens=7000, overlap_tokens=600)
    print(f"[DEBUG] Passing {len(qa_segments)} chunks to LLM with quality-focused chunking targeting ~5 insights.", file=sys.stderr)
    
    # 3) Run the single-row-per-chunk processing
    chunk_results = []
    quality_rows = []
    
    def process_chunk(chunk_index, chunk):
        try:
            # Filter out non-Q&A chunks
            if not is_qa_chunk(chunk, found_qa):
                logging.info(f"Chunk {chunk_index} filtered out: not Q&A content")
                return (chunk_index, [])
            
            # Clean the chunk text (but be less aggressive for speaker-based transcripts)
            if found_qa:
                # For Q&A format, clean aggressively
                cleaned_chunk = clean_verbatim_response(chunk)
                if not cleaned_chunk:
                    logging.info(f"Chunk {chunk_index} filtered out: no content after cleaning")
                    return (chunk_index, [])
            else:
                # For speaker-based transcripts, just remove speaker labels and timestamps
                cleaned_chunk = re.sub(r'^Speaker \d+ \(\d{2}:\d{2}\):\s*', '', chunk)
                cleaned_chunk = re.sub(r'\(\d{2}:\d{2}\):\s*', '', cleaned_chunk)
                cleaned_chunk = cleaned_chunk.strip()
                if len(cleaned_chunk) < 5:
                    logging.info(f"Chunk {chunk_index} filtered out: too short after minimal cleaning")
                    return (chunk_index, [])
            
            # Skip low-value responses
            if is_low_value_response(cleaned_chunk):
                logging.info(f"Chunk {chunk_index} filtered out: low-value response - {cleaned_chunk[:50]}...")
                return (chunk_index, [])
            
            # Prepare input for the chain
            base_response_id = normalize_response_id(company, interviewee, chunk_index)
            chain_input = {
                "chunk_text": cleaned_chunk,
                "response_id": base_response_id,
                "key_insight": "",  # Let the LLM fill this in
                "company": company,
                "company_name": company,
                "interviewee_name": interviewee,
                "deal_status": deal_status,
                "date_of_interview": date_of_interview
            }
            
            # Get response from LLM
            raw = ""
            # up to 3 attempts to get valid JSON
            for _ in range(3):
                response = chain.invoke(chain_input)
                # Extract content from AIMessage object
                if hasattr(response, 'content'):
                    raw = response.content.strip()
                else:
                    raw = str(response).strip()
                if not raw:
                    continue
                try:
                    # Parse response - could be single object or array
                    parsed = json.loads(raw)
                    
                    # Handle both single object and array responses
                    if isinstance(parsed, list):
                        objects = parsed
                    else:
                        objects = [parsed]
                    
                    csv_rows = []
                    
                    for i, obj in enumerate(objects):
                        # Validate required fields
                        required_fields = ["response_id", "verbatim_response", "subject", "question", 
                                         "deal_status", "company", "interviewee_name", "date_of_interview", "key_insight"]
                        for field in required_fields:
                            if field not in obj:
                                if field == "key_insight":
                                    obj["key_insight"] = "N/A"
                                else:
                                    raise ValueError(f"Missing required field: {field}")
                        
                        # Ensure metadata is populated everywhere
                        obj["deal_status"] = normalize_deal_status(deal_status)
                        obj["company"] = company
                        obj["interviewee_name"] = interviewee
                        obj["date_of_interview"] = format_date(date_of_interview)
                        
                        # Fill missing questions/subjects
                        if not obj.get("question") or obj["question"] == "N/A":
                            obj["question"] = "What insights did the interviewee share?"
                        
                        if not obj.get("subject") or obj["subject"] == "N/A":
                            obj["subject"] = infer_subject_from_text(cleaned_chunk)
                        
                        # Clean verbatim response again to ensure it's clean
                        original_len = len(cleaned_chunk.split())
                        obj["verbatim_response"] = clean_verbatim_response(obj["verbatim_response"])
                        cleaned_len = len(obj["verbatim_response"].split())
                        
                        # Quality check: flag if >80% of chunk was dropped
                        if original_len > 0:
                            drop_ratio = 1 - (cleaned_len / original_len)
                            if drop_ratio > 0.8:
                                quality_rows.append({
                                    "response_id": obj.get("response_id", ""),
                                    "grade": "LOW",
                                    "notes": f"{math.floor(drop_ratio*100)}% of original chunk dropped after cleaning."
                                })
                            else:
                                quality_rows.append({
                                    "response_id": obj.get("response_id", ""),
                                    "grade": "OK",
                                    "notes": ""
                                })
                        
                        # Convert to CSV row
                        csv_row = [
                            obj.get("response_id", ""),
                            obj.get("key_insight", ""),
                            obj.get("verbatim_response", ""),
                            obj.get("subject", ""),
                            obj.get("question", ""),
                            obj.get("deal_status", ""),
                            obj.get("company", ""),
                            obj.get("interviewee_name", ""),
                            obj.get("date_of_interview", ""),
                            obj.get("findings", ""),
                            obj.get("value_realization", ""),
                            obj.get("implementation_experience", ""),
                            obj.get("risk_mitigation", ""),
                            obj.get("competitive_advantage", ""),
                            obj.get("customer_success", ""),
                            obj.get("product_feedback", ""),
                            obj.get("service_quality", ""),
                            obj.get("decision_factors", ""),
                            obj.get("pain_points", ""),
                            obj.get("success_metrics", ""),
                            obj.get("future_plans", "")
                        ]
                        
                        csv_rows.append(csv_row)
                    
                    return (chunk_index, csv_rows)
                except Exception as e:
                    # malformed JSON, retry
                    continue
            
            # if we reach here, skip this chunk
            logging.warning(f"Chunk {chunk_index} dropped: no valid LLM output — text: {chunk[:60].replace(chr(10), ' ')}")
            return (chunk_index, [])
            
        except Exception as e:
            logging.warning(f"Chunk {chunk_index} dropped: {e} — text: {chunk[:100]!r}")
            return (chunk_index, [])
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_chunk = {executor.submit(process_chunk, i, chunk): (i, chunk) for i, chunk in enumerate(qa_segments)}
        for future in as_completed(future_to_chunk):
            try:
                chunk_index, results = future.result()
                if results:  # Only add successful results
                    for result in results:
                        chunk_results.append((chunk_index, result))
            except Exception as e:
                print(f"Error processing chunk: {e}")
    
    # 4) Sort by chunk index and deduplicate results
    chunk_results.sort(key=lambda x: x[0])
    
    # Enhanced deduplication based on key insight and verbatim response similarity
    def is_similar_response(row1, row2, similarity_threshold=0.8):  # Increased threshold for more nuanced deduplication
        """Check if two responses are similar enough to be considered duplicates"""
        import difflib
        
        # Ensure we have enough columns
        if len(row1) < 3 or len(row2) < 3:
            return False
        
        # Get key insight and verbatim response
        insight1 = str(row1[1]).lower().strip()  # Key Insight
        insight2 = str(row2[1]).lower().strip()
        verbatim1 = str(row1[2]).lower().strip()  # Verbatim Response
        verbatim2 = str(row2[2]).lower().strip()
        
        # Check for exact matches first (most common case)
        if insight1 == insight2 and verbatim1 == verbatim2:
            return True
        
        # Check if insights are very similar (increased threshold for more nuanced deduplication)
        insight_similarity = difflib.SequenceMatcher(None, insight1, insight2).ratio()
        
        # Check if verbatim responses are very similar (first 400 chars for better detection)
        verbatim1_short = verbatim1[:400]
        verbatim2_short = verbatim2[:400]
        verbatim_similarity = difflib.SequenceMatcher(None, verbatim1_short, verbatim2_short).ratio()
        
        # Check for common phrases that indicate duplicates
        common_phrases = [
            "turbo scribe", "rev", "transcription", "legal", "deposition",
            "body cam", "court", "attorney", "paralegal", "law firm"
        ]
        
        # If both responses contain the same key phrases, they're likely duplicates
        phrase_match = 0
        for phrase in common_phrases:
            if phrase in insight1 and phrase in insight2:
                phrase_match += 1
        
        # Enhanced deduplication: check for specific differentiators
        specific_indicators = [
            r'\d+%',  # Percentages
            r'\$\d+',  # Dollar amounts
            r'\d+ hours?',  # Time periods
            r'\d+ minutes?',
            r'for example',
            r'such as',
            r'specifically',
            r'in particular',
            r'workflow',
            r'process',
            r'integration',
            r'accuracy',
            r'efficiency',
            r'before',
            r'after',
            r'compared',
            r'different',
            r'improved',
            r'better',
            r'worse'
        ]
        
        # Count specific indicators in each response
        indicators1 = sum(1 for pattern in specific_indicators if re.search(pattern, verbatim1))
        indicators2 = sum(1 for pattern in specific_indicators if re.search(pattern, verbatim2))
        
        # If responses have significantly different specific indicators, they're likely different
        if abs(indicators1 - indicators2) >= 2:
            return False
        
        # More nuanced deduplication: if either insight or verbatim is similar, OR if they share key phrases
        return (insight_similarity > similarity_threshold or 
                verbatim_similarity > similarity_threshold or 
                phrase_match >= 3)  # Increased threshold for phrase matching
    
    # Enhanced duplicate removal with multiple strategies
    unique_results = []
    seen_responses = set()
    seen_content_patterns = set()
    
    for chunk_index, row in chunk_results:
        # Create multiple hashes for better detection
        insight_hash = str(row[1]).lower().replace(" ", "")[:100]
        verbatim_hash = str(row[2]).lower().replace(" ", "")[:200]
        combined_hash = f"{insight_hash}_{verbatim_hash}"
        
        # Create content pattern hash (first 50 chars of each)
        content_pattern = f"{str(row[1])[:50]}_{str(row[2])[:50]}".lower().replace(" ", "")
        
        # Check if we've seen a similar response
        is_duplicate = False
        for existing_row in unique_results:
            if is_similar_response(row, existing_row):
                is_duplicate = True
                break
        
        # Additional check: if content pattern is very similar, it's likely a duplicate
        if content_pattern in seen_content_patterns:
            is_duplicate = True
        
        if not is_duplicate and combined_hash not in seen_responses:
            unique_results.append((chunk_index, row))
            seen_responses.add(combined_hash)
            seen_content_patterns.add(content_pattern)
    
    print(f"[DEBUG] Removed {len(chunk_results) - len(unique_results)} duplicate responses", file=sys.stderr)
    
    # Additional post-processing: remove responses that start with identical phrases
    final_results = []
    seen_starts = set()
    
    for chunk_index, row in unique_results:
        # Get the first 100 characters of the verbatim response
        response_start = str(row[2])[:100].lower().strip()
        
        # If we've seen this exact start before, skip it
        if response_start in seen_starts:
            continue
        
        # Check if this response starts with common duplicate patterns
        duplicate_patterns = [
            "before turbo scribe, we used rev",
            "turbo scribe has significantly improved",
            "i've had a subscription with westlaw",
            "i mainly use it for depositions",
            "also, i was wondering on the subject",
            "maybe if it's, for example, specifically",
            "i mean, the accuracy could be improved",
            # Technical setup patterns
            "hi drew, can you hear me",
            "can you hear me",
            "check check check",
            "one sec",
            "let me switch",
            "alright cool",
            "nice to meet you"
        ]
        
        is_duplicate_start = any(response_start.startswith(pattern) for pattern in duplicate_patterns)
        
        if not is_duplicate_start:
            final_results.append((chunk_index, row))
            seen_starts.add(response_start)
    
    print(f"[DEBUG] Post-processing removed {len(unique_results) - len(final_results)} additional duplicates", file=sys.stderr)
    
    # Write CSV header (no auto-index column)
    header = ["Response ID", "Key Insight", "Verbatim Response", "Subject", "Question", "Deal Status", 
              "Company Name", "Interviewee Name", "Date of Interview", "Findings", 
              "Value_Realization", "Implementation_Experience", "Risk_Mitigation", 
              "Competitive_Advantage", "Customer_Success", "Product_Feedback", 
              "Service_Quality", "Decision_Factors", "Pain_Points", "Success_Metrics", "Future_Plans"]
    
    output = StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)  # Quote all fields for CSV integrity
    writer.writerow(header)
    
    # Write data rows (now deduplicated) and save to database if available
    db = None
    if DB_AVAILABLE:
        try:
            db = VOCDatabase()
        except Exception as e:
            print(f"[WARNING] Database not available: {e}", file=sys.stderr)
    
    for chunk_index, row in final_results:
        writer.writerow(row)
        
        # Save to database if available
        if db:
            try:
                # Convert row to response_data format
                response_data = {
                    'response_id': row[0],  # Response ID
                    'verbatim_response': row[2],  # Verbatim Response
                    'subject': row[3],  # Subject
                    'question': row[4],  # Question
                    'deal_status': row[5],  # Deal Status
                    'company': row[6],  # Company Name
                    'interviewee_name': row[7],  # Interviewee Name
                    'date_of_interview': row[8],  # Date of Interview
                }
                
                # Add analysis fields if they exist
                if len(row) > 9:
                    analysis_fields = [
                        'findings', 'value_realization', 'implementation_experience',
                        'risk_mitigation', 'competitive_advantage', 'customer_success',
                        'product_feedback', 'service_quality', 'decision_factors',
                        'pain_points', 'success_metrics', 'future_plans'
                    ]
                    
                    for i, field in enumerate(analysis_fields):
                        if 9 + i < len(row) and row[9 + i] and row[9 + i] != 'N/A':
                            response_data[field] = row[9 + i]
                
                db.save_response(response_data)
            except Exception as e:
                print(f"[WARNING] Failed to save to database: {e}", file=sys.stderr)
    
    # Write verbatim quality log
    with open("verbatim_quality.csv", "w", newline="") as qf:
        qwriter = csv.DictWriter(qf, fieldnames=["response_id", "grade", "notes"])
        qwriter.writeheader()
        for row in quality_rows:
            qwriter.writerow(row)
    
    # Log summary
    logging.info(f"Processed {len(qa_segments)} chunks → created {len(chunk_results)} insights; dropped {len(qa_segments) - len(set(r[0] for r in chunk_results))} chunks")
    
    # Output CSV to stdout
    print(output.getvalue())


@click.command()
@click.option('--input', '-i', required=True, help='Input CSV file to validate')
@click.option('--output', '-o', required=True, help='Output CSV file for validated data')
def validate(input, output):
    """Validate processed CSV data."""
    print(f"Validating {input}...")
    
    import pandas as pd
    
    try:
        # Read the input CSV
        df = pd.read_csv(input)
        print(f"Read {len(df)} rows from {input}")
        
        # Basic validation - keep rows that have meaningful content
        if len(df) > 0:
            print(f"Columns in input file: {list(df.columns)}")
            
            # Find the verbatim response column (handle different naming)
            verbatim_col = None
            for col in df.columns:
                if 'verbatim' in col.lower() and 'response' in col.lower():
                    verbatim_col = col
                    break
            
            if verbatim_col is None:
                print("Warning: Could not find 'Verbatim Response' column")
                print(f"Available columns: {list(df.columns)}")
                # Just pass through all data
                df_valid = df
            else:
                print(f"Using verbatim column: {verbatim_col}")
                # Filter out rows with empty verbatim responses
                df_valid = df[df[verbatim_col].str.strip() != '']
            
            print(f"After validation: {len(df_valid)} rows")
            
            # Enhanced deduplication step
            if len(df_valid) > 0:
                # Remove exact duplicates based on key insight and verbatim response
                df_valid = df_valid.drop_duplicates(subset=['Key Insight', 'Verbatim Response'], keep='first')
                
                # Additional similarity-based deduplication
                import difflib
                
                def find_similar_rows(df, similarity_threshold=0.8):
                    """Find and remove rows with similar content"""
                    to_remove = []
                    
                    for i in range(len(df)):
                        for j in range(i + 1, len(df)):
                            if i in to_remove or j in to_remove:
                                continue
                            
                            # Compare key insights
                            insight1 = str(df.iloc[i]['Key Insight']).lower()
                            insight2 = str(df.iloc[j]['Key Insight']).lower()
                            insight_similarity = difflib.SequenceMatcher(None, insight1, insight2).ratio()
                            
                            # Compare verbatim responses (first 200 chars)
                            verbatim1 = str(df.iloc[i]['Verbatim Response'])[:200].lower()
                            verbatim2 = str(df.iloc[j]['Verbatim Response'])[:200].lower()
                            verbatim_similarity = difflib.SequenceMatcher(None, verbatim1, verbatim2).ratio()
                            
                            # If either is very similar, mark for removal
                            if insight_similarity > similarity_threshold or verbatim_similarity > similarity_threshold:
                                to_remove.append(j)
                    
                    return to_remove
                
                # Remove similar rows
                similar_indices = find_similar_rows(df_valid)
                if similar_indices:
                    df_valid = df_valid.drop(df_valid.index[similar_indices])
                    print(f"Removed {len(similar_indices)} similar rows during validation")
                
                print(f"After deduplication: {len(df_valid)} rows")
            
            # Save validated data
            df_valid.to_csv(output, index=False)
            print(f"Validation complete. Output saved to {output}")
        else:
            print("No data to validate")
            # Create empty file with headers
            df.to_csv(output, index=False)
            
    except Exception as e:
        print(f"Error during validation: {e}")
        # Create empty output file with headers
        pd.DataFrame(columns=[
            "Response ID","Verbatim Response","Subject","Question",
            "Deal Status","Company Name","Interviewee Name","Date of Interview","Findings",
            "Value_Realization","Implementation_Experience","Risk_Mitigation","Competitive_Advantage",
            "Customer_Success","Product_Feedback","Service_Quality","Decision_Factors",
            "Pain_Points","Success_Metrics","Future_Plans"
        ]).to_csv(output, index=False)


@click.command()
@click.option('--input', '-i', required=True, help='Input CSV file to process')
@click.option('--output', '-o', required=True, help='Output CSV file for final table')
def build_table(input, output):
    """Build final data table from processed data."""
    print(f"Building table from {input} to {output}...")
    
    import pandas as pd
    
    try:
        # Read the input CSV
        df = pd.read_csv(input)
        print(f"Read {len(df)} rows from {input}")
        
        if len(df) > 0:
            print(f"Columns in input file: {list(df.columns)}")
            
            # Reorder columns to match the expected schema
            expected_columns = [
                "Response ID","Verbatim Response","Subject","Question",
                "Deal Status","Company Name","Interviewee Name","Date of Interview","Findings",
                "Value_Realization","Implementation_Experience","Risk_Mitigation","Competitive_Advantage",
                "Customer_Success","Product_Feedback","Service_Quality","Decision_Factors",
                "Pain_Points","Success_Metrics","Future_Plans"
            ]
            
            # Map column names (handle different naming conventions)
            column_mapping = {}
            for expected_col in expected_columns:
                # Try exact match first
                if expected_col in df.columns:
                    column_mapping[expected_col] = expected_col
                else:
                    # Try case-insensitive match
                    for actual_col in df.columns:
                        if expected_col.lower() == actual_col.lower():
                            column_mapping[expected_col] = actual_col
                            break
                    # If no match found, create empty column
                    if expected_col not in column_mapping:
                        column_mapping[expected_col] = expected_col
                        df[expected_col] = ""
            
            # Reorder columns using mapping
            df_final = df[[column_mapping[col] for col in expected_columns]]
            # Rename columns to expected names
            df_final.columns = expected_columns
            
            # Save final table
            df_final.to_csv(output, index=False)
            print(f"Table building complete. Output saved to {output}")
        else:
            print("No data to process")
            # Create empty file with headers
            df.to_csv(output, index=False)
            
    except Exception as e:
        print(f"Error during table building: {e}")
        # Create empty output file with headers
        pd.DataFrame(columns=[
            "Response ID","Verbatim Response","Subject","Question",
            "Deal Status","Company Name","Interviewee Name","Date of Interview","Findings",
            "Value_Realization","Implementation_Experience","Risk_Mitigation","Competitive_Advantage",
            "Customer_Success","Product_Feedback","Service_Quality","Decision_Factors",
            "Pain_Points","Success_Metrics","Future_Plans"
        ]).to_csv(output, index=False)


@click.command("process_transcript")
@click.argument('transcript_path')
@click.argument('client')
@click.argument('company')
@click.argument('interviewee')
@click.argument('deal_status')
@click.argument('date_of_interview')
def process_transcript(transcript_path, client, company, interviewee, deal_status, date_of_interview):
    """Process a transcript and output CSV data."""
    _process_transcript_impl(transcript_path, client, company, interviewee, deal_status, date_of_interview)


if __name__ == "__main__":
    process_transcript() 