"""
SQLAlchemy database models for PriceChekRider.
Defines User, Order, and Product tables.
"""
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """User model to store customer phone numbers and session data."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    current_session_data = Column(Text, nullable=True)  # Store SMS/USSD state (e.g. sms_step:location_set)
    city_code = Column(String(10), nullable=True)  # e.g. NAI for Nairobi (spec)
    location = Column(String(100), nullable=True)   # Full location e.g. NAI-Kileleshwa or Westlands
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to orders
    orders = relationship("Order", back_populates="user")


class Order(Base):
    """Order model to store customer orders."""
    
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    items = Column(Text, nullable=False)  # JSON string of items
    total_price = Column(Float, nullable=False)
    status = Column(String(20), default="PENDING", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to user
    user = relationship("User", back_populates="orders")
