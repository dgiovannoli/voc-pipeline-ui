from pydantic import BaseModel, validator
from coders.schemas import CRITERIA_LIST, SWOT_LIST, PHASE_LIST

class ResponseRow(BaseModel):
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
