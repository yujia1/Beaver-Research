from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Float, Text, Enum, JSON, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, server_default="user", nullable=False)  # admin, creator, contributor, user
    is_active = Column(Boolean, default=False)  # requires admin activation before login is allowed

    # User Preferences & Metadata
    settings = Column(JSON, default={}, nullable=True)  # Theme, notifications, etc.
    last_login = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True) # Text content or Markdown
    file_path = Column(String, nullable=True) # S3/MinIO key for PDF/File assets
    report_type = Column(String, index=True, nullable=False)  # daily, logic, short, market
    ticker = Column(String, index=True, nullable=True)
    is_uploaded = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="reports")


class PortfolioPosition(Base):
    """
    Single shared portfolio: one row per ticker, not per user. All admin/creator/
    contributor/user roles view the same data; only admin/creator can write to it.
    """
    __tablename__ = "portfolio_positions"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True, nullable=False)
    sector = Column(String, nullable=True)

    updated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    updated_by = relationship("User", foreign_keys=[updated_by_user_id])
    lots = relationship("PortfolioLot", back_populates="position", cascade="all, delete-orphan")
    analysis = relationship("PositionAnalysis", back_populates="position", cascade="all, delete-orphan")


class PortfolioLot(Base):
    __tablename__ = "portfolio_lots"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("portfolio_positions.id"), nullable=False, index=True)

    purchase_date = Column(String, nullable=False)  # ISO Date String YYYY-MM-DD
    quantity = Column(Integer, nullable=False)
    cost_per_share = Column(Float, nullable=False)
    side = Column(String, default="LONG")  # LONG or SHORT
    link = Column(String, nullable=True)
    note = Column(Text, nullable=True)

    updated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    position = relationship("PortfolioPosition", back_populates="lots")
    updated_by = relationship("User", foreign_keys=[updated_by_user_id])


class PositionAnalysis(Base):
    __tablename__ = "position_analysis"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("portfolio_positions.id"), nullable=False, index=True)
    
    question_id = Column(Integer, nullable=False)
    answer = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    position = relationship("PortfolioPosition", back_populates="analysis")
    
    __table_args__ = (
        UniqueConstraint('position_id', 'question_id', name='uix_position_question'),
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String, index=True, nullable=False)
    resource = Column(String, index=True, nullable=False)
    can_access = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('role', 'resource', name='uix_role_resource'),
    )


class FinancialStatementCache(Base):
    """Optional: Permanent storage for financial statements beyond Redis TTL"""
    __tablename__ = "financial_statement_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    statement_type = Column(String, nullable=False)  # income, cashflow, balance
    fiscal_year = Column(Integer, nullable=False)
    period = Column(String, default="annual", nullable=False)  # annual or quarter
    
    # Full statement data as JSON
    data = Column(JSON, nullable=False)
    
    # Metadata
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(String, default="fmp", nullable=False)  # fmp, manual, etc.
    
    # Indexes for fast lookup
    __table_args__ = (
        UniqueConstraint('ticker', 'statement_type', 'fiscal_year', 'period', name='uix_ticker_statement_year'),
    )
