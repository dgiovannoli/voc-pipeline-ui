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
  <identity>Expert qualitative coding analyst specializing in win-loss interview data extraction</identity>
  <objective>Transform interview transcripts into structured data for analysis</objective>
</role>

<input_specification>
  <source>Interview transcript chunk containing customer feedback</source>
  <content_type>Verbatim response from customer interview</content_type>
  <context>Win-loss analysis for product/service evaluation</context>
</input_specification>

<critical_requirements>
  <requirement>Extract meaningful insights from customer feedback</requirement>
  <requirement>Identify specific subjects and questions addressed</requirement>
  <requirement>Maintain data integrity and consistency</requirement>
  <requirement>Ensure all fields are properly populated</requirement>
</critical_requirements>

<segmentation_principles>
  <principle>Each response should represent a complete thought or insight</principle>
  <principle>Subject should capture the main topic being discussed</principle>
  <principle>Question should reflect what the response is answering</principle>
</segmentation_principles>

<processing_steps>
  <step>1. Read and understand the interview chunk</step>
  <step>2. Identify the primary subject or topic</step>
  <step>3. Determine what question this response addresses</step>
  <step>4. Extract the verbatim response text</step>
  <step>5. Populate all required fields with appropriate data</step>
</processing_steps>

<output_format>
  <columns>
    <column name="Response ID" type="string" description="Unique identifier for this response"/>
    <column name="Verbatim Response" type="string" description="Exact text from the interview"/>
    <column name="Subject" type="string" description="Main topic or subject being discussed"/>
    <column name="Question" type="string" description="What question this response is answering"/>
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
    <input>Customer said: "The onboarding process was too complex and took too long. We needed something simpler."</input>
    <output>
      Response ID: resp_001
      Verbatim Response: "The onboarding process was too complex and took too long. We needed something simpler."
      Subject: Onboarding Process Complexity
      Question: What were the main issues with the onboarding process?
      Deal Status: {deal_status}
      Company Name: {company_name}
      Interviewee Name: {interviewee_name}
      Date of Interview: {date_of_interview}
    </output>
  </example>
</examples>

<subject_identification_guide>
  <category>Product Features: Technical capabilities, functionality, performance</category>
  <category>Process: Workflows, procedures, methodologies</category>
  <category>Pricing: Cost, value, ROI, budget considerations</category>
  <category>Support: Customer service, training, documentation</category>
  <category>Integration: Technical compatibility, implementation</category>
  <category>Decision Making: Factors influencing purchase decisions</category>
</subject_identification_guide>

<quality_assurance>
  <check>Ensure subject accurately reflects the main topic</check>
  <check>Verify question is relevant to the response content</check>
  <check>Confirm all metadata fields are populated</check>
  <check>Validate response text is complete and accurate</check>
</quality_assurance>

<execution_instructions>
  Analyze the provided interview chunk and return a JSON object with the following structure:
  {{
    "response_id": "{response_id}",
    "verbatim_response": "{chunk_text}",
    "subject": "brief_subject_description",
    "question": "what_question_this_answers",
    "deal_status": "{deal_status}",
    "company": "{company}",
    "interviewee_name": "{interviewee_name}",
    "date_of_interview": "{date_of_interview}"
  }}
  
  **Output must be strictly valid JSON matching the ResponseRow schema. Return only the raw JSON object—no markdown, no extra commentary or tables.**
</execution_instructions>

Output (JSON only):
{{
  "response_id": "{response_id}",
  "verbatim_response": "{chunk_text}",
  "subject": "brief_subject_description",
  "question": "what_question_this_answers",
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
