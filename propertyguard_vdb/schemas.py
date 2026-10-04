from typing import List, Optional, Literal
from pydantic import BaseModel, Field

ToneType = Literal["good", "warn", "bad"]
SeverityType = Literal["High", "Medium", "Low"]

class IssueItem(BaseModel):
    severity: SeverityType
    title: str
    detail: str

class VerificationResponse(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    document_status: str
    document_tone: ToneType
    document_note: str
    area_status: str
    area_tone: ToneType
    area_note: str
    document_area: Optional[float] = None
    area_unit: str
    duplicate_status: str
    duplicate_tone: ToneType
    duplicate_note: str
    issues: List[IssueItem] = []
    report_id: Optional[str] = None
    generated_at: Optional[str] = None
    is_dummy: bool = False