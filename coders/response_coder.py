import os, json
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from coders.models import QuoteTag
from coders.schemas import CRITERIA_LIST, SWOT_LIST, PHASE_LIST

class ResponseCoder:
    def __init__(self):
        self.llm = OpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"))
        # Updated prompt template with JSON schema and metadata usage
        self.prompt = PromptTemplate(
            input_variables=[
                "chunk_text",
                "response_id", 
                "deal_status",
                "company",
                "interviewee_name",
                "date_of_interview"
            ],
            template=f"""Analyze this interview chunk and extract insights using the Buried Wins framework.

Interview Text: {{chunk_text}}

Available Categories:
- Criteria: {CRITERIA_LIST}
- SWOT Themes: {SWOT_LIST}
- Journey Phases: {PHASE_LIST}

Instructions:
1. Analyze the text for customer insights, pain points, or positive feedback
2. Categorize using the available options above
3. Extract the most relevant quote
4. Return a JSON object with the following structure

Return ONLY this JSON format:
{{{{
  "quote_id": "unique_identifier",
  "criteria": "one_of_the_criteria_options",
  "swot_theme": "one_of_the_swot_options", 
  "journey_phase": "one_of_the_phase_options",
  "text": "exact_quote_from_text",
  "response_id": "{{response_id}}",
  "verbatim_response": "{{chunk_text}}",
  "subject": "brief_subject_description",
  "question": "what_question_this_answers",
  "deal_status": "{{deal_status}}",
  "company": "{{company}}",
  "interviewee_name": "{{interviewee_name}}",
  "date_of_interview": "{{date_of_interview}}"
}}}}""",
        )
        # Use modern RunnableSequence syntax instead of deprecated LLMChain
        self.chain = self.prompt | self.llm

    def code(self, chunk_text, metadata):
        # Generate quote_id and response_id from metadata if available
        quote_id = f"{metadata.get('interview_id', 'unknown')}_{metadata.get('chunk_index', 0)}"
        response_id = f"resp_{metadata.get('interview_id', 'unknown')}_{metadata.get('chunk_index', 0)}"
        
        # Extract required metadata fields
        deal_status = metadata.get('deal_status', 'unknown')
        company = metadata.get('company', 'unknown')
        interviewee_name = metadata.get('interviewee_name', 'unknown')
        date_of_interview = metadata.get('date_of_interview', '2024-01-01')
        
        # Invoke the chain with proper input including all six required fields
        raw = self.chain.invoke({
            "chunk_text": chunk_text,
            "response_id": response_id,
            "deal_status": deal_status,
            "company": company,
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
        
        # Attempt JSON parse + schema validation (up to 3 retries)
        for attempt in range(3):
            try:
                # Clean the response text
                cleaned_text = raw_text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                obj = json.loads(cleaned_text)
                # Ensure quote_id is set
                if 'quote_id' not in obj or not obj['quote_id']:
                    obj['quote_id'] = quote_id
                tag = QuoteTag(**obj)
                return tag.dict()
            except json.JSONDecodeError as e:
                if attempt < 2:  # Retry up to 2 more times
                    print(f"JSON decode error on attempt {attempt + 1}: {e}")
                    print(f"Raw response: {raw_text}")
                    raw = self.chain.invoke({
                        "chunk_text": chunk_text,
                        "response_id": response_id,
                        "deal_status": deal_status,
                        "company": company,
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
                        "company": company,
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
