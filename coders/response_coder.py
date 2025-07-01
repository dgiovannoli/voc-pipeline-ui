import os, json
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from coders.models import QuoteTag
from coders.schemas import CRITERIA_LIST, SWOT_LIST, PHASE_LIST

class ResponseCoder:
    def __init__(self):
        self.llm = OpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"))
        # Inline the lists via an f-string so they aren't treated as variables
        self.prompt = PromptTemplate(
            input_variables=["chunk_text", "metadata"],
            template=f"""
You are tagging one interview chunk according to the Buried Wins framework.

Chunk:
\"\"\"
{{chunk_text}}
\"\"\"

Metadata:
{{metadata}}

Return ONLY a JSON object with exactly these keys:
- quote_id (string)
- criteria (one of {CRITERIA_LIST})
- swot_theme (one of {SWOT_LIST})
- journey_phase (one of {PHASE_LIST})
- text (the exact quote text)

Example output:
{{{{"quote_id":"intvw1_0","criteria":"product_capability","swot_theme":"strength","journey_phase":"awareness","text":"…"}}}}
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
        
        # Attempt JSON parse + schema validation (up to 2 retries)
        for attempt in range(2):
            try:
                obj = json.loads(raw_text.strip())
                # Ensure quote_id is set
                if 'quote_id' not in obj or not obj['quote_id']:
                    obj['quote_id'] = quote_id
                tag = QuoteTag(**obj)
                return tag.dict()
            except Exception as e:
                if attempt < 1:  # Only retry once
                    raw = self.chain.invoke({
                        "chunk_text": chunk_text, 
                        "metadata": metadata
                    })
                    if hasattr(raw, 'content'):
                        raw_text = raw.content
                    else:
                        raw_text = str(raw)
                else:
                    raise RuntimeError(f"Failed to parse tags after retries: {raw_text}. Error: {e}")
        
        raise RuntimeError(f"Failed to parse tags: {raw_text}")
