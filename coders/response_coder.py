import os, json
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from coders.models import QuoteTag
from coders.schemas import CRITERIA_LIST, SWOT_LIST, PHASE_LIST

class ResponseCoder:
    def __init__(self):
        self.llm = OpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"))
        # Simplified prompt template with escaped curly braces in JSON example
        self.prompt = PromptTemplate(
            input_variables=["chunk_text", "metadata"],
            template=f"""
Tag this interview chunk using the Buried Wins framework.

Text: {{chunk_text}}

Available options:
- Criteria: {CRITERIA_LIST}
- SWOT: {SWOT_LIST}  
- Phases: {PHASE_LIST}

Return ONLY a JSON object with these exact keys:
- quote_id (string)
- criteria (one of the criteria above)
- swot_theme (one of the SWOT themes above)
- journey_phase (one of the phases above)
- text (the exact quote text)

Example: {{{{"quote_id":"chunk_1","criteria":"product_capability","swot_theme":"strength","journey_phase":"awareness","text":"The product works great"}}}}
""",
        )
        # Use modern RunnableSequence syntax instead of deprecated LLMChain
        self.chain = self.prompt | self.llm

    def code(self, chunk_text, metadata):
        # Generate quote_id from metadata if available
        quote_id = f"{metadata.get('interview_id', 'unknown')}_{metadata.get('chunk_index', 0)}"
        
        # Invoke the chain with proper input
        raw = self.chain.invoke({
            "chunk_text": chunk_text, 
            "metadata": metadata
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
                        "metadata": metadata
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
                        "metadata": metadata
                    })
                    if hasattr(raw, 'content'):
                        raw_text = raw.content
                    else:
                        raw_text = str(raw)
                else:
                    raise RuntimeError(f"Failed to process after 3 attempts: {raw_text}. Error: {e}")
        
        raise RuntimeError(f"Failed to parse tags: {raw_text}")
