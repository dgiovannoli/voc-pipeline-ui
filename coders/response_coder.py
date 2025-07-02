import os, json, time
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from coders.models import ResponseRow
from coders.schemas import CRITERIA_LIST, SWOT_LIST, PHASE_LIST

class ResponseCoder:
    def __init__(self):
        self.llm = OpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=1000,  # Limit response length to prevent truncation
            temperature=0.1   # Lower temperature for more consistent responses
        )
        # ——— Response Data Table Prompt ———
        self.prompt = PromptTemplate(
            input_variables=[
                "chunk_text",
                "deal_status",
                "company_name",
                "interviewee_name",
                "date_of_interview",
                "response_id"
            ],
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
    "company": "{company_name}",
    "interviewee_name": "{interviewee_name}",
    "date_of_interview": "{date_of_interview}"
  }}
</execution_instructions>
""".strip()
        )
        # Use modern RunnableSequence syntax instead of deprecated LLMChain
        self.chain = self.prompt | self.llm

    def code(self, chunk_text, metadata):
        # Generate quote_id and response_id from metadata if available
        quote_id = f"{metadata.get('interview_id', 'unknown')}_{metadata.get('chunk_index', 0)}"
        response_id = f"resp_{metadata.get('interview_id', 'unknown')}_{metadata.get('chunk_index', 0)}"
        
        # Extract required metadata fields
        deal_status = metadata.get('deal_status', 'unknown')
        company_name = metadata.get('company', 'unknown')
        interviewee_name = metadata.get('interviewee_name', 'unknown')
        date_of_interview = metadata.get('date_of_interview', '2024-01-01')
        
        # Invoke the chain with proper input including all six required fields
        raw = self.chain.invoke({
            "chunk_text": chunk_text,
            "response_id": response_id,
            "deal_status": deal_status,
            "company_name": company_name,
            "interviewee_name": interviewee_name,
            "date_of_interview": date_of_interview
        })
        
        # Extract the content from the response
        if hasattr(raw, 'content'):
            raw_text = raw.content
        else:
            raw_text = str(raw)
        
        # Check for empty response
        if not raw_text or raw_text.strip() == "":
            raise RuntimeError(f"Empty response from LLM for chunk: {chunk_text[:100]}...")
        
        # Attempt JSON parse + schema validation with exponential backoff
        for attempt in range(3):
            if attempt > 0:
                # Exponential backoff: wait 1s, 2s, 4s
                time.sleep(2 ** (attempt - 1))
            try:
                # Clean the response text
                cleaned_text = raw_text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                # Handle truncated JSON responses
                if cleaned_text.count('{') > cleaned_text.count('}'):
                    # JSON is incomplete, try to complete it
                    missing_braces = cleaned_text.count('{') - cleaned_text.count('}')
                    cleaned_text += '}' * missing_braces
                    
                # Handle incomplete string values
                if cleaned_text.count('"') % 2 != 0:
                    # Odd number of quotes, likely incomplete string
                    last_quote_pos = cleaned_text.rfind('"')
                    if last_quote_pos != -1:
                        # Find the start of the incomplete string
                        start_pos = cleaned_text.rfind('"', 0, last_quote_pos)
                        if start_pos != -1:
                            # Complete the string and add missing fields
                            incomplete_field = cleaned_text[start_pos+1:last_quote_pos+1]
                            cleaned_text = cleaned_text[:start_pos+1] + incomplete_field + '", "deal_status": "' + deal_status + '", "company": "' + company_name + '", "interviewee_name": "' + interviewee_name + '", "date_of_interview": "' + date_of_interview + '"}'
                
                obj = json.loads(cleaned_text)
                # Create ResponseRow with the required fields
                response_row = ResponseRow(**obj)
                return response_row.dict()
            except json.JSONDecodeError as e:
                if attempt < 2:  # Retry up to 2 more times
                    print(f"JSON decode error on attempt {attempt + 1}: {e}")
                    print(f"Raw response: {raw_text}")
                    raw = self.chain.invoke({
                        "chunk_text": chunk_text,
                        "response_id": response_id,
                        "deal_status": deal_status,
                        "company_name": company_name,
                        "interviewee_name": interviewee_name,
                        "date_of_interview": date_of_interview
                    })
                    if hasattr(raw, 'content'):
                        raw_text = raw.content
                    else:
                        raw_text = str(raw)
                else:
                    raise RuntimeError(f"Failed to parse JSON after 3 attempts. Raw response: {raw_text}")
            except Exception as e:
                if attempt < 2:
                    print(f"Other error on attempt {attempt + 1}: {e}")
                    raw = self.chain.invoke({
                        "chunk_text": chunk_text,
                        "response_id": response_id,
                        "deal_status": deal_status,
                        "company_name": company_name,
                        "interviewee_name": interviewee_name,
                        "date_of_interview": date_of_interview
                    })
                    if hasattr(raw, 'content'):
                        raw_text = raw.content
                    else:
                        raw_text = str(raw)
                else:
                    raise RuntimeError(f"Failed to process after 3 attempts: {raw_text}. Error: {e}")
        
        raise RuntimeError(f"Failed to parse tags: {raw_text}")
