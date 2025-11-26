from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    report_type = Column(String) # e.g., 'company_overview', 'operating_drivers'
    ticker = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
