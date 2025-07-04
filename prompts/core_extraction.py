"""
Core Extraction Prompt - Stage 1
Extracts only essential verbatim responses and metadata from interview transcripts.
This is the source of truth and should focus on quality verbatim extraction.
"""

CORE_EXTRACTION_PROMPT = """
CRITICAL INSTRUCTIONS FOR CORE RESPONSE EXTRACTION:
- Extract ONLY the essential verbatim responses and metadata
- NO analysis, insights, or enrichment fields
- Focus on clean, complete verbatim responses with proper context
- Ensure accurate metadata assignment

EXTRACTION STRATEGY:
- Identify the 1-2 richest, most detailed customer responses in this chunk
- Extract the COMPLETE verbatim response for each with full context
- Create a brief, factual subject description
- Focus on responses that provide complete context and detailed explanations
- Choose responses that cover different aspects or themes when possible
- If only one high-quality response exists, extract just that one

VERBATIM RESPONSE RULES:
- Include the COMPLETE response text (300-800 words for optimal context)
- Preserve ALL context, examples, specific details, and quantitative information
- Include relevant parts of the conversation flow for better understanding
- Include follow-up questions and clarifications that add context
- Remove only speaker labels, timestamps, and interviewer prompts
- Keep filler words if they add emphasis or meaning
- Maintain the natural flow and structure of the response
- Include specific examples, metrics, detailed explanations, and follow-up context

METADATA ASSIGNMENT:
- Subject: Brief factual description (e.g., "Product Integration", "Workflow Optimization")
- Question: What question this response answers
- Deal Status: Use provided deal status
- Company: Use provided company name
- Interviewee: Use provided interviewee name
- Date: Use provided interview date

Analyze the provided interview chunk and extract the 1-2 RICHEST, MOST COMPREHENSIVE verbatim responses. Return ONLY a JSON array containing one or two objects:

[
  {{
    "response_id": "{response_id}_1",
    "verbatim_response": "first_complete_verbatim_response_with_full_context_and_specific_examples",
    "subject": "brief_factual_subject_description_1",
    "question": "what_question_this_answers_1",
    "deal_status": "{deal_status}",
    "company": "{company}",
    "interviewee_name": "{interviewee_name}",
    "date_of_interview": "{date_of_interview}"
  }},
  {{
    "response_id": "{response_id}_2",
    "verbatim_response": "second_complete_verbatim_response_with_full_context_and_specific_examples",
    "subject": "brief_factual_subject_description_2",
    "question": "what_question_this_answers_2",
    "deal_status": "{deal_status}",
    "company": "{company}",
    "interviewee_name": "{interviewee_name}",
    "date_of_interview": "{date_of_interview}"
  }}
]

Guidelines:
- Extract the 1-2 richest, most comprehensive verbatim responses per chunk
- Subject categories: Product Features, Process, Pricing, Support, Integration, Decision Making, Workflow Optimization
- Use "N/A" for fields that don't apply
- Return ONLY the JSON array, no other text
- Focus on responses with specific examples, metrics, detailed explanations, and full context
- Choose responses that provide the most complete picture of customer experiences
- If only one rich response exists, return an array with just one object
- Skip chunks that only contain low-quality content (acknowledgments, thank yous, etc.)

Interview chunk to analyze:
{chunk_text}
"""

def get_core_extraction_prompt(response_id: str, company: str, interviewee_name: str, 
                              deal_status: str, date_of_interview: str, chunk_text: str) -> str:
    """Generate the core extraction prompt with the provided parameters."""
    return CORE_EXTRACTION_PROMPT.format(
        response_id=response_id,
        company=company,
        interviewee_name=interviewee_name,
        deal_status=deal_status,
        date_of_interview=date_of_interview,
        chunk_text=chunk_text
    ) 