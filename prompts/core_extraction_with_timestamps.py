"""
Core Extraction Prompt - Stage 1 with Timestamp Support
Extracts essential verbatim responses, metadata, and timestamps from interview transcripts.
This is the source of truth and should focus on quality verbatim extraction with timing information.
"""

CORE_EXTRACTION_PROMPT_WITH_TIMESTAMPS = """
CRITICAL INSTRUCTIONS FOR CONTEXT-DRIVEN EXTRACTION WITH TIMESTAMPS:
- You have access to focused context windows (~7K tokens) containing Q&A exchanges.
- Focus on COMPLETE CONTEXT and MEANINGFUL Q&A PAIRS rather than arbitrary numbers.
- Extract responses that provide complete thought processes, reasoning, and business context.
- Some chunks may have 2 valuable Q&A pairs, others may have 8 - let the content guide you.
- **IMPORTANT**: Extract timestamps for each Q&A pair to enable video navigation.

ENHANCED QUESTION DETECTION STRATEGY:
Look for questions in these forms:
- **Direct questions**: "What is...?" "How do you...?" "Why did you...?"
- **Statement + Question**: "Speed and cost were priorities. Were there other criteria?"
- **Embedded questions**: "I'm curious about..." followed by a question
- **Clarifying questions**: "So you're saying..." followed by a question
- **Multi-part questions**: Questions with multiple clauses or follow-ups
- **Complex questions**: Questions embedded in longer explanations or statements
- **Follow-up questions**: Questions that reference previous context

EXAMPLES OF COMPLEX QUESTIONS TO CAPTURE:
- "Speed and cost were your top two priority. And you just mentioned layout as kind of a nice to have something that made you feel comfortable in it. Were there any other criteria that you evaluated when comparing Rev to other vendors?"
- "When it comes to the transcription work they had done, were there any needs or even criteria that were specific to legal?"
- "With accuracy rating so high. Are there any files where it would be worth it to upgrade to a human transcriptionist first for accuracy purposes?"
- "When you went to find a vendor, did you already know about Rev, or did you look at a few different vendors online through search?"

DO NOT skip questions just because they are complex or have multiple parts.

CONTEXT-DRIVEN EXTRACTION STRATEGY:
- **Evaluate the Context**: Look for complete Q&A exchanges that provide full context
- **Preserve Thought Processes**: Capture responses that show complete reasoning and decision-making
- **Maintain Conversation Flow**: Include related follow-up questions and clarifications
- **Focus on Substance**: Prioritize responses with specific examples, metrics, and detailed explanations
- **Natural Grouping**: Group related Q&A pairs that form a complete thought or scenario
- **Quality Over Quantity**: Better to extract 2 comprehensive responses than 5 fragmented ones
- **Capture All Valuable Content**: Don't skip responses just because they're brief or complex

EXTRACTION CRITERIA:
1. **Complete Context**: Responses that provide full background, reasoning, and implications
2. **Specific Examples**: Detailed scenarios, use cases, workflows, and quantitative details
3. **Business Impact**: ROI discussions, decision factors, risk assessments, and strategic perspectives
4. **Comparative Analysis**: Before/after comparisons, competitive evaluations, and performance metrics
5. **Integration Details**: Workflow requirements, technical specifications, and process changes
6. **Customer Experiences**: Complete scenarios with full context and specific outcomes
7. **Brief but Important**: Short responses that contain key insights or decisions
8. **Complex Discussions**: Multi-part exchanges that form complete thoughts

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
- Capture responses even if they are brief but contain important insights

TIMESTAMP EXTRACTION RULES:
- **Extract Start Timestamps**: Identify when each Q&A exchange begins
- **Extract End Timestamps**: Identify when each Q&A exchange ends
- **Use Available Timestamps**: Look for timestamps in the format [HH:MM:SS] or (MM:SS)
- **Normalize Format**: Convert all timestamps to HH:MM:SS format
- **Handle Missing Timestamps**: If no timestamps are available, set to null
- **Map to Q&A Pairs**: Associate timestamps with the specific question and response
- **Preserve Timing Context**: Maintain the chronological order of exchanges

CONTEXT EVALUATION:
- **High Context**: Complete scenarios with full background, specific examples, and detailed outcomes
- **Medium Context**: Good detail but may be missing some background or follow-up context
- **Low Context**: Brief responses with limited detail or incomplete scenarios
- **Skip**: Acknowledgments, thank yous, or responses with insufficient context
- **Include**: Brief responses that contain key decisions, preferences, or important insights

EXTRACTION DECISION FRAMEWORK:
1. **Start with Q&A Pairs**: Identify complete question-answer exchanges
2. **Evaluate Context**: Assess the completeness and richness of each response
3. **Group Related Content**: Combine related Q&A pairs that form complete thoughts
4. **Prioritize Substance**: Focus on responses with specific examples, metrics, and detailed explanations
5. **Maintain Flow**: Preserve conversation context and related follow-up questions
6. **Quality Check**: Ensure each extracted response provides meaningful, actionable insights
7. **Capture Edge Cases**: Include brief but important responses that contain key insights
8. **Extract Timestamps**: Identify and map timing information for each Q&A pair

CRITICAL FIELD DEFINITIONS:
- **SUBJECT**: The main topic or area being discussed (e.g., "Product Features", "Pricing", "Implementation")
- **QUESTION**: The actual question that was asked to elicit this response. This must be a real question from the transcript, in interrogative form (e.g., "How do you evaluate pricing?", "What challenges did you face during implementation?").
  - **Do NOT** use a subject description or summary as the question.
  - **If you cannot find the actual question, set the field to 'UNKNOWN' and log a warning.**
  - **Include complex questions with multiple clauses or embedded statements.**
- **START_TIMESTAMP**: When the question-answer exchange begins (format: HH:MM:SS)
- **END_TIMESTAMP**: When the question-answer exchange ends (format: HH:MM:SS)

FIELD EXAMPLES:
✅ CORRECT:
- Subject: "Product Features"
- Question: "How do you use Rev in your daily workflow?"
- Start Timestamp: "00:01:30"
- End Timestamp: "00:02:15"

❌ INCORRECT:
- Subject: "Product Features" 
- Question: "Feedback on product features and their importance" (This is a subject description, not a question)
- Subject: "Pricing and Cost"
- Question: "Consideration of pricing factors and cost evaluation" (This is a subject description, not a question)

✅ CORRECT:
- Subject: "Pricing and Cost"
- Question: "What factors do you consider when evaluating pricing?"
- Start Timestamp: "00:03:45"
- End Timestamp: "00:04:30"

VALIDATION RULES:
- The "question" field **must** be an actual question from the transcript, in interrogative form (usually ends with a question mark, or starts with 'what', 'how', 'why', 'when', 'who', 'where', 'which').
- If the question is missing or ambiguous, set the field to 'UNKNOWN'.
- Never use a subject description, summary, or feedback statement as the question.
- Log a warning if you cannot find a valid question.
- **Include complex questions with multiple clauses or embedded statements.**
- **Timestamps should be in HH:MM:SS format or null if not available.**

CRITICAL COVERAGE REQUIREMENT:
- **CHRONOLOGICAL PROCESSING**: Process Q&A pairs in order from beginning to end of chunk
- **COMPLETE COVERAGE**: Extract ALL question-response pairs, regardless of length or perceived quality
- **NO SKIPPING**: Do not skip Q&A pairs at the beginning, middle, or end of chunks
- **Include Short Responses**: Brief responses often contain crucial insights - do not filter them out
- **Header Tolerance**: Skip only document headers, titles, and metadata - not actual Q&A content
- **Timestamp Mapping**: Ensure each Q&A pair has associated timing information

IMPORTANT: Capture ALL question-response pairs, including:
- Questions with multiple clauses or statements
- Questions embedded in longer explanations
- Follow-up questions within the same exchange
- Questions that reference previous context
- Brief but important responses
- Short responses that might seem less "substantial" but contain key insights

Analyze the provided interview chunk and extract COMPLETE Q&A pairs in CHRONOLOGICAL ORDER with TIMESTAMPS. Return ONLY a JSON array containing ALL question-response pairs found in the chunk:

[
  {{
    "response_id": "{response_id}_1",
    "verbatim_response": "complete_verbatim_response_with_full_context_and_conversation_flow",
    "subject": "Product Features",
    "question": "How do you currently use the product?",
    "start_timestamp": "00:01:30",
    "end_timestamp": "00:02:15",
    "deal_status": "{deal_status}",
    "company": "{company}",
    "interviewee_name": "{interviewee_name}",
    "date_of_interview": "{date_of_interview}"
  }},
  {{
    "response_id": "{response_id}_2",
    "verbatim_response": "complete_verbatim_response_with_full_context_and_conversation_flow",
    "subject": "Implementation Process",
    "question": "What challenges did you face during setup?",
    "start_timestamp": "00:03:45",
    "end_timestamp": "00:04:30",
    "deal_status": "{deal_status}",
    "company": "{company}",
    "interviewee_name": "{interviewee_name}",
    "date_of_interview": "{date_of_interview}"
  }}
]

Guidelines:
- **Chronological Order**: Process Q&A pairs from beginning to end - maintain transcript sequence
- **Complete Coverage**: Extract ALL Q&A pairs found in the chunk, regardless of length
- **Preserve Conversation Flow**: Include related follow-up questions and clarifications
- **Subject Categories**: Product Features, Integration Challenges, Implementation Process, Adoption Challenges, Pricing and Cost, Competitive Analysis, Support and Service, Security and Compliance, Vendor Reliability, Sales Experience, Performance and Speed, Business Impact, Decision Making, Workflow Optimization, Future Considerations
- **Question Format**: Must be an actual question (interrogative format), not a description
- **Context Preservation**: Ensure each response captures the complete thought process
- **No Selective Filtering**: Do not skip responses based on perceived quality or length
- **Include All Types**: Extract both detailed responses AND brief but important responses
- **Variable Output**: Chunks may produce 2-15 responses depending on actual Q&A content - this is expected
- **Capture Complex Questions**: Include questions with multiple clauses, embedded statements, or complex structures
- **Equal Treatment**: Give equal consideration to all Q&A pairs regardless of response length
- **Timestamp Extraction**: Extract start and end timestamps for each Q&A pair when available
- **Timestamp Format**: Use HH:MM:SS format or null if timestamps are not available

Interview chunk to analyze:
{chunk_text}
"""

def get_core_extraction_prompt_with_timestamps(response_id: str, company: str, interviewee_name: str, 
                                              deal_status: str, date_of_interview: str, chunk_text: str) -> str:
    """Generate the core extraction prompt with timestamp support."""
    return CORE_EXTRACTION_PROMPT_WITH_TIMESTAMPS.format(
        response_id=response_id,
        company=company,
        interviewee_name=interviewee_name,
        deal_status=deal_status,
        date_of_interview=date_of_interview,
        chunk_text=chunk_text
    )
