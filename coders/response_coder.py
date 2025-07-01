import os, json
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
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
{{"quote_id":"intvw1_0","criteria":"product_capability","swot_theme":"strength","journey_phase":"awareness","text":"…"}}
""",
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def code(self, chunk_text, metadata):
        raw = self.chain.invoke({"chunk_text": chunk_text, "metadata": metadata})
        # Attempt JSON parse + schema validation (up to 2 retries)
        for attempt in range(2):
            try:
                obj = json.loads(raw.strip())
                tag = QuoteTag(**obj)
                return tag.dict()
            except Exception:
                raw = self.chain.invoke({"chunk_text": chunk_text, "metadata": metadata})
        raise RuntimeError(f"Failed to parse tags: {raw}")
