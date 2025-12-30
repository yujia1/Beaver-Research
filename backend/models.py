from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Float, Text, Enum, JSON, BigInteger, UniqueConstraint
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
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Payment / Stripe fields
    has_paid = Column(Boolean, default=False, nullable=False)
    payment_transaction_id = Column(String, nullable=True)
    payment_date = Column(DateTime(timezone=True), nullable=True)
    
    stripe_customer_id = Column(String, nullable=True, index=True)
    stripe_subscription_id = Column(String, nullable=True)
    stripe_current_period_end = Column(DateTime(timezone=True), nullable=True)
    
    # User Preferences & Metadata
    settings = Column(JSON, default={}, nullable=True)  # Theme, notifications, etc.
    last_login = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    portfolio_positions = relationship("PortfolioPosition", back_populates="user", cascade="all, delete-orphan")


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
    __tablename__ = "portfolio_positions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ticker = Column(String, index=True, nullable=False)
    sector = Column(String, nullable=True)
    
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="portfolio_positions")
    lots = relationship("PortfolioLot", back_populates="position", cascade="all, delete-orphan")
    analysis = relationship("PositionAnalysis", back_populates="position", cascade="all, delete-orphan")

    # Unique constraint: one position per ticker per user
    __table_args__ = (
        UniqueConstraint('user_id', 'ticker', name='uix_user_ticker_portfolio'),
    )


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
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    position = relationship("PortfolioPosition", back_populates="lots")


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


class SystemConfig(Base):
    __tablename__ = "system_config"

    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
