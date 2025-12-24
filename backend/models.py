from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean, ForeignKey, Float, UniqueConstraint
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
    payment_date = Column(DateTime(timezone=True), nullable=True)  # Payment date
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    reports = relationship("Report", back_populates="user")

class RolePermission(Base):
    """Store permissions for each role accessing different resources"""
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String, nullable=False, index=True)  # admin, creator, contributor, user
    resource = Column(String, nullable=False)  # /research, /alphatrade, /report, /investment
    can_access = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Unique constraint to prevent duplicate rules
    __table_args__ = (
        UniqueConstraint('role', 'resource', name='uix_role_resource'),
    )



class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    report_type = Column(String) 
    ticker = Column(String, index=True)
    is_uploaded = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="reports")

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
    total_value = Column(BigInteger, nullable=True)  # Total value in USD
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SavedReport(Base):
    __tablename__ = "saved_reports"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    report_content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# AlphaTrade Models
class AlphaTradePosition(Base):
    __tablename__ = "alphatrade_positions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ticker = Column(String, index=True, nullable=False)
    sector = Column(String, nullable=True)
    current_price = Column(Float, nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="alphatrade_positions")
    lots = relationship("AlphaTradeLot", back_populates="position", cascade="all, delete-orphan")
    fundamental_analysis = relationship("AlphaTradeFundamentalAnalysis", back_populates="position", cascade="all, delete-orphan")

    # Unique constraint: one position per ticker per user
    __table_args__ = (
        UniqueConstraint('user_id', 'ticker', name='uix_user_ticker'),
    )


class AlphaTradeLot(Base):
    __tablename__ = "alphatrade_lots"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("alphatrade_positions.id"), nullable=False)
    purchase_date = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    cost_per_share = Column(Float, nullable=False)
    side = Column(String, nullable=False)  # 'LONG' or 'SHORT'
    link = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    position = relationship("AlphaTradePosition", back_populates="lots")


class AlphaTradeFundamentalAnalysis(Base):
    __tablename__ = "alphatrade_fundamental_analysis"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("alphatrade_positions.id"), nullable=False)
    question_id = Column(Integer, nullable=False)
    answer = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)  # 1-5
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    position = relationship("AlphaTradePosition", back_populates="fundamental_analysis")






class WhaleAlert(Base):
    __tablename__ = "whale_alerts"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    institution_name = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)  # WHALE_NEW, WHALE_EXIT, WHALE_INCREASE, WHALE_DECREASE
    severity = Column(String, nullable=False)  # HIGH, MEDIUM, LOW
    message = Column(Text, nullable=False)
    quarter = Column(String, nullable=False)
    percent_change = Column(Float, nullable=True)
    shares_change = Column(Float, nullable=True)
    value_change = Column(Float, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PositionChange(Base):
    __tablename__ = "position_changes"

    id = Column(Integer, primary_key=True, index=True)
    cik = Column(String, index=True, nullable=False)
    ticker = Column(String, index=True, nullable=False)
    institution_name = Column(String, nullable=False)
    change_type = Column(String, nullable=False)  # NEW, CLOSED, INCREASED, DECREASED
    current_quarter = Column(String, nullable=False)
    prior_quarter = Column(String, nullable=True)
    
    # Use BigInteger for share counts and values to prevent overflow
    current_shares = Column(BigInteger, nullable=False)
    prior_shares = Column(BigInteger, nullable=True)
    shares_change = Column(BigInteger, nullable=True)
    
    percent_change = Column(Float, nullable=True)
    
    current_value = Column(BigInteger, nullable=False)
    prior_value = Column(BigInteger, nullable=True)
    
    is_whale = Column(Boolean, default=False)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SystemConfig(Base):
    __tablename__ = "system_config"

    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False)
    description = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
