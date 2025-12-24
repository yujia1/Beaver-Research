from pydantic import BaseModel
from typing import Optional

class ReportRequest(BaseModel):
    data_context: str
    prompt_customization: Optional[str] = ""

class CompanyAnalysisRequest(BaseModel):
    ticker: str
    company_name: str
    sector: str
