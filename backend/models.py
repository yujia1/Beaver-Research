from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, server_default="user", nullable=False)  # admin, creator, contributor, user
    is_active = Column(Boolean, default=True)
    has_paid = Column(Boolean, default=False, nullable=False)  # Payment status for Research access
    payment_transaction_id = Column(String, nullable=True)  # PayPal transaction ID
    payment_date = Column(DateTime(timezone=True), nullable=True)  # Payment date
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ticker = Column(String, nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    type = Column(String, nullable=False)  # positive, negative, neutral
    category = Column(String, nullable=False)  # macro, micro, market, industry, product
    is_forecast = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    user = relationship("User", backref="events")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    report_type = Column(String) # e.g., 'company_overview', 'operating_drivers'
    ticker = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Filing13F(Base):
    """Track processed 13F filings per CIK"""
    __tablename__ = "filing_13f"

    id = Column(Integer, primary_key=True, index=True)
    cik = Column(String, nullable=False, index=True)
    accession_number = Column(String, nullable=False, unique=True, index=True)
    form_type = Column(String, nullable=False)  # 13F-HR, 13F-HR/A, 13F-NT
    filing_date = Column(DateTime(timezone=True), nullable=False)
    period_end_date = Column(DateTime(timezone=True), nullable=False)
    quarter = Column(String, nullable=False, index=True)  # YYYY-Q1, YYYY-Q2, etc.
    is_amended = Column(Boolean, default=False, nullable=False)
    minio_path = Column(String, nullable=True)  # Path to CSV in MinIO
    holdings_count = Column(Integer, nullable=True)
    total_value = Column(Integer, nullable=True)  # Total value in USD (cents)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
