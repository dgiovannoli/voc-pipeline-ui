import os, json, time, logging
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from coders.models import ResponseRow
from coders.schemas import CRITERIA_LIST, SWOT_LIST, PHASE_LIST

class ResponseCoder:
    def __init__(self):
        self.llm = OpenAI(
            model_name="gpt-3.5-turbo-16k",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=16000,
            temperature=0.1
        )
        # ——— Response Data Table Prompt ———
        self.prompt = PromptTemplate(
            input_variables=["response_id","chunk_text","company","company_name","interviewee_name","deal_status","date_of_interview"],
            template="""
<role>
  <identity>Expert business analyst specializing in extracting actionable insights from customer interviews</identity>
  <objective>Transform interview transcripts into structured, business-relevant insights for strategic analysis</objective>
</role>

<input_specification>
  <source>Interview transcript chunk containing customer feedback</source>
  <content_type>Verbatim response from customer interview</content_type>
  <context>Win-loss analysis for product/service evaluation and strategic insights</context>
</input_specification>

<critical_requirements>
  <requirement>Extract SPECIFIC, ACTIONABLE insights that can inform business decisions</requirement>
  <requirement>Identify concrete examples, metrics, and specific use cases</requirement>
  <requirement>Focus on business impact, competitive factors, and implementation details</requirement>
  <requirement>Capture specific feature requests, pain points, and success stories</requirement>
</critical_requirements>

<segmentation_principles>
  <principle>Each response should represent a complete business insight or actionable feedback</principle>
  <principle>Subject should capture the specific business area or feature being discussed</principle>
  <principle>Question should reflect the strategic business question this addresses</principle>
  <principle>Prioritize quotes with specific examples, numbers, or concrete details</principle>
</segmentation_principles>

<processing_steps>
  <step>1. Read and understand the interview chunk for business relevance</step>
  <step>2. Identify the specific business topic, feature, or process being discussed</step>
  <step>3. Determine what strategic business question this response addresses</step>
  <step>4. Extract the verbatim response text with full context</step>
  <step>5. Ensure the insight is specific and actionable, not generic</step>
</processing_steps>

<output_format>
  <columns>
    <column name="Response ID" type="string" description="Unique identifier for this response"/>
    <column name="Verbatim Response" type="string" description="Exact text from the interview"/>
    <column name="Subject" type="string" description="Specific business topic, feature, or process"/>
    <column name="Question" type="string" description="Strategic business question this addresses"/>
    <column name="Deal Status" type="string" description="Status of the deal (won/lost/etc)"/>
    <column name="Company Name" type="string" description="Name of the customer company"/>
    <column name="Interviewee Name" type="string" description="Name of the person interviewed"/>
    <column name="Date of Interview" type="string" description="Date when interview was conducted"/>
  </columns>
  <header_row>Response ID, Verbatim Response, Subject, Question, Deal Status, Company Name, Interviewee Name, Date of Interview</header_row>
  <formatting_requirements>
    <requirement>All text fields should be properly escaped</requirement>
    <requirement>Dates should be in YYYY-MM-DD format</requirement>
    <requirement>No empty fields - use appropriate defaults if needed</requirement>
  </formatting_requirements>
</output_format>

<examples>
  <example>
    <input>Customer said: "The AI feature has been particularly beneficial for summarizing lengthy interviews. I can get a quick overview of key points in just a few minutes instead of spending hours reading through transcripts. I'd love to see it integrate legal terms like 'consent to search' for my DUI cases."</input>
    <output>
      Response ID: resp_001
      Verbatim Response: "The AI feature has been particularly beneficial for summarizing lengthy interviews. I can get a quick overview of key points in just a few minutes instead of spending hours reading through transcripts. I'd love to see it integrate legal terms like 'consent to search' for my DUI cases."
      Subject: AI Summarization Feature - Legal Integration
      Question: How can AI features be enhanced for specific industry use cases?
      Deal Status: {deal_status}
      Company Name: {company_name}
      Interviewee Name: {interviewee_name}
      Date of Interview: {date_of_interview}
    </output>
  </example>
  
  <example>
    <input>Customer said: "We switched from a human transcription service that took 3-4 days and cost $2.50 per minute to Rev which gives us results in 2 hours at $1.25 per minute. The time savings alone have been game-changing for our legal practice."</input>
    <output>
      Response ID: resp_002
      Verbatim Response: "We switched from a human transcription service that took 3-4 days and cost $2.50 per minute to Rev which gives us results in 2 hours at $1.25 per minute. The time savings alone have been game-changing for our legal practice."
      Subject: Cost and Speed Comparison - Competitive Advantage
      Question: What specific metrics demonstrate our competitive advantages?
      Deal Status: {deal_status}
      Company Name: {company_name}
      Interviewee Name: {interviewee_name}
      Date of Interview: {date_of_interview}
    </output>
  </example>
</examples>

<subject_identification_guide>
  <category>Product Features: Specific capabilities, performance metrics, feature requests</category>
  <category>Implementation: Setup time, complexity, integration requirements</category>
  <category>Pricing: Cost comparisons, ROI metrics, budget impact</category>
  <category>Support: Response times, expertise, specific support needs</category>
  <category>Competitive: Direct comparisons, switching factors, market positioning</category>
  <category>Business Impact: Revenue impact, efficiency gains, strategic value</category>
  <category>Use Cases: Specific applications, industry requirements, workflow integration</category>
</subject_identification_guide>

<quality_assurance>
  <check>Ensure subject captures specific business area or feature</check>
  <check>Verify question addresses strategic business concern</check>
  <check>Confirm response contains concrete details or examples</check>
  <check>Validate insight is actionable and business-relevant</check>
  <check>Prioritize quotes with specific metrics, numbers, or use cases</check>
</quality_assurance>

<execution_instructions>
  Analyze the provided interview chunk and return a JSON object with the following structure:
  {{
    "response_id": "{response_id}",
    "verbatim_response": "{chunk_text}",
    "subject": "specific_business_topic_or_feature",
    "question": "strategic_business_question_this_addresses",
    "deal_status": "{deal_status}",
    "company": "{company}",
    "interviewee_name": "{interviewee_name}",
    "date_of_interview": "{date_of_interview}"
  }}
  
  **Focus on extracting specific, actionable business insights. Avoid generic statements. Prioritize quotes with concrete examples, metrics, or specific use cases.**
  
  **Output must be strictly valid JSON matching the ResponseRow schema. Return only the raw JSON object—no markdown, no extra commentary or tables.**
</execution_instructions>

Output (JSON only):
{{
  "response_id": "{response_id}",
  "verbatim_response": "{chunk_text}",
  "subject": "specific_business_topic_or_feature",
  "question": "strategic_business_question_this_addresses",
  "deal_status": "{deal_status}",
  "company": "{company}",
  "interviewee_name": "{interviewee_name}",
  "date_of_interview": "{date_of_interview}"
}}
""".strip()
        )
        # Use modern RunnableSequence syntax instead of deprecated LLMChain
        self.chain = self.prompt | self.llm

    def code(self,
             chunk_text: str,
             response_id: str,
             company: str,
             company_name: str,
             interviewee_name: str,
             deal_status: str,
             date_of_interview: str
    ) -> dict:
        # Prepare the input with all required variables
        chain_input = {
            "chunk_text": chunk_text,
            "response_id": response_id,
            "company": company,
            "company_name": company_name,
            "interviewee_name": interviewee_name,
            "deal_status": deal_status,
            "date_of_interview": date_of_interview
        }
        
        raw = ""
        # up to 3 attempts to get valid JSON
        for _ in range(3):
            raw = self.chain.invoke(chain_input).strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
                tag = ResponseRow(**obj)
                return tag.dict()
            except Exception:
                # malformed JSON, retry
                continue
        # if we reach here, skip this chunk
        logging.warning("Skipping chunk (no valid LLM output): %s", chunk_text[:60].replace("\n"," "))
        return None
