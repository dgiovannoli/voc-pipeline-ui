from pydantic import BaseModel, validator
from coders.schemas import CRITERIA_LIST, SWOT_LIST, PHASE_LIST

class QuoteTag(BaseModel):
    quote_id: str
    criteria: str
    swot_theme: str
    journey_phase: str
    text: str
    response_id: str
    verbatim_response: str
    subject: str
    question: str
    deal_status: str
    company: str
    interviewee_name: str
    date_of_interview: str

    class Config:
        extra = "allow"  # Allow extra fields

    @validator('criteria')
    def validate_criteria(cls, v):
        if v not in CRITERIA_LIST:
            raise ValueError(f"Unknown criteria: {v}")
        return v

    @validator('swot_theme')
    def validate_swot(cls, v):
        if v not in SWOT_LIST:
            raise ValueError(f"Unknown swot_theme: {v}")
        return v

    @validator('journey_phase')
    def validate_phase(cls, v):
        if v not in PHASE_LIST:
            raise ValueError(f"Unknown journey_phase: {v}")
        return v
