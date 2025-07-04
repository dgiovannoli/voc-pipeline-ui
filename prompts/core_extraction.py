"""
Core Extraction Prompt - Stage 1
Extracts only essential verbatim responses and metadata from interview transcripts.
This is the source of truth and should focus on quality verbatim extraction.
"""

CORE_EXTRACTION_PROMPT = """
CRITICAL INSTRUCTIONS FOR ENHANCED QUALITY ANALYSIS:
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

Analyze the provided interview chunk and extract the 1-2 RICHEST, MOST COMPREHENSIVE verbatim responses. Return ONLY a JSON array containing one or two objects with the following fields:

[
  {{
    "response_id": "{response_id}_1",
    "verbatim_response": "first_complete_verbatim_response_with_full_context_and_specific_examples",
    "subject": "brief_subject_description_1",
    "question": "what_question_this_answers_1",
    "deal_status": "{deal_status}",
    "company": "{company}",
    "interviewee_name": "{interviewee_name}",
    "date_of_interview": "{date_of_interview}"
  }},
  {{
    "response_id": "{response_id}_2",
    "verbatim_response": "second_complete_verbatim_response_with_full_context_and_specific_examples",
    "subject": "brief_subject_description_2",
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
- Prioritize responses that show different aspects of similar topics (e.g., different use cases, workflows, or specific pain points)

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