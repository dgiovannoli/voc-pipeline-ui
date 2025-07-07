"""
Core Extraction Prompt - Stage 1
Extracts only essential verbatim responses and metadata from interview transcripts.
This is the source of truth and should focus on quality verbatim extraction.
"""

CORE_EXTRACTION_PROMPT = """
CRITICAL INSTRUCTIONS FOR CONTEXT-DRIVEN EXTRACTION:
- You have access to focused context windows (~7K tokens) containing Q&A exchanges.
- Focus on COMPLETE CONTEXT and MEANINGFUL Q&A PAIRS rather than arbitrary numbers.
- Extract responses that provide complete thought processes, reasoning, and business context.
- Some chunks may have 2 valuable Q&A pairs, others may have 8 - let the content guide you.

CONTEXT-DRIVEN EXTRACTION STRATEGY:
- **Evaluate the Context**: Look for complete Q&A exchanges that provide full context
- **Preserve Thought Processes**: Capture responses that show complete reasoning and decision-making
- **Maintain Conversation Flow**: Include related follow-up questions and clarifications
- **Focus on Substance**: Prioritize responses with specific examples, metrics, and detailed explanations
- **Natural Grouping**: Group related Q&A pairs that form a complete thought or scenario
- **Quality Over Quantity**: Better to extract 2 comprehensive responses than 5 fragmented ones

EXTRACTION CRITERIA:
1. **Complete Context**: Responses that provide full background, reasoning, and implications
2. **Specific Examples**: Detailed scenarios, use cases, workflows, and quantitative details
3. **Business Impact**: ROI discussions, decision factors, risk assessments, and strategic perspectives
4. **Comparative Analysis**: Before/after comparisons, competitive evaluations, and performance metrics
5. **Integration Details**: Workflow requirements, technical specifications, and process changes
6. **Customer Experiences**: Complete scenarios with full context and specific outcomes

VERBATIM RESPONSE RULES:
- Include the COMPLETE response text with full context and conversation flow
- Preserve ALL context, examples, specific details, and quantitative information
- Include relevant follow-up questions and clarifications that add context
- Remove only speaker labels, timestamps, and interviewer prompts
- Keep filler words if they add emphasis or meaning
- Maintain the natural flow and structure of the response
- Include specific examples, metrics, detailed explanations, and follow-up context
- Preserve comparative language and specific differentiators
- Include workflow details, process descriptions, and technical specifications

CONTEXT EVALUATION:
- **High Context**: Complete scenarios with full background, specific examples, and detailed outcomes
- **Medium Context**: Good detail but may be missing some background or follow-up context
- **Low Context**: Brief responses with limited detail or incomplete scenarios
- **Skip**: Acknowledgments, thank yous, or responses with insufficient context

EXTRACTION DECISION FRAMEWORK:
1. **Start with Q&A Pairs**: Identify complete question-answer exchanges
2. **Evaluate Context**: Assess the completeness and richness of each response
3. **Group Related Content**: Combine related Q&A pairs that form complete thoughts
4. **Prioritize Substance**: Focus on responses with specific examples, metrics, and detailed explanations
5. **Maintain Flow**: Preserve conversation context and related follow-up questions
6. **Quality Check**: Ensure each extracted response provides meaningful, actionable insights

Analyze the provided interview chunk and extract COMPLETE, CONTEXT-RICH Q&A pairs. Return ONLY a JSON array containing the most valuable responses (quantity varies by content quality):

[
  {{
    "response_id": "{response_id}_1",
    "verbatim_response": "complete_verbatim_response_with_full_context_and_conversation_flow",
    "subject": "brief_subject_description_1",
    "question": "what_question_this_answers_1",
    "deal_status": "{deal_status}",
    "company": "{company}",
    "interviewee_name": "{interviewee_name}",
    "date_of_interview": "{date_of_interview}"
  }},
  {{
    "response_id": "{response_id}_2",
    "verbatim_response": "complete_verbatim_response_with_full_context_and_conversation_flow",
    "subject": "brief_subject_description_2",
    "question": "what_question_this_answers_2",
    "deal_status": "{deal_status}",
    "company": "{company}",
    "interviewee_name": "{interviewee_name}",
    "date_of_interview": "{date_of_interview}"
  }}
]

Guidelines:
- **Let Content Guide Quantity**: Extract 1-8 responses based on the richness of the content
- **Focus on Complete Context**: Prioritize responses that provide full background and reasoning
- **Preserve Conversation Flow**: Include related follow-up questions and clarifications
- **Subject Categories**: Product Features, Process, Pricing, Support, Integration, Decision Making, Workflow Optimization
- **Quality Threshold**: Only extract responses with substantial, actionable content
- **Context Preservation**: Ensure each response captures the complete thought process
- **Natural Grouping**: Group related Q&A pairs that form complete scenarios
- **Skip Low-Quality**: Skip chunks with only acknowledgments, thank yous, or insufficient context
- **Variable Output**: Some chunks may produce 2 responses, others 8 - this is expected and correct

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