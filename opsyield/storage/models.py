import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Integer, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    cloud_accounts = relationship("CloudAccount", back_populates="organization", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="viewer")
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="users")

class CloudAccount(Base):
    """Stores cloud provider credentials securely per organization."""
    __tablename__ = "cloud_accounts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # aws, gcp, azure
    account_id = Column(String(255), nullable=False) # e.g., AWS Account ID, GCP Project ID
    name = Column(String(255), nullable=True)
    credentials_json = Column(Text, nullable=False)  # Encrypted credentials JSON
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="cloud_accounts")
    cost_snapshots = relationship("CostSnapshot", back_populates="cloud_account", cascade="all, delete-orphan")

class CostSnapshot(Base):
    """Daily aggregated cost records per resource/service."""
    __tablename__ = "cost_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    cloud_account_id = Column(String(36), ForeignKey("cloud_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    provider = Column(String(50), nullable=False)
    service = Column(String(255), nullable=False, index=True)
    resource_id = Column(String(512), nullable=True, index=True)
    region = Column(String(100), nullable=True)
    
    cost = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    usage_quantity = Column(Float, nullable=True)
    usage_unit = Column(String(50), nullable=True)
    
    timestamp = Column(DateTime, nullable=False, index=True)
    tags = Column(JSON, nullable=True)

    cloud_account = relationship("CloudAccount", back_populates="cost_snapshots")

class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    provider = Column(String(50), nullable=False)
    service = Column(String(255), nullable=True)
    resource_id = Column(String(512), nullable=True)
    
    expected_cost = Column(Float, nullable=False)
    actual_cost = Column(Float, nullable=False)
    deviation_percent = Column(Float, nullable=False)
    severity = Column(String(50), nullable=False) # low, medium, high, critical
    
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved = Column(Boolean, default=False)
    description = Column(Text, nullable=True)

class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    provider = Column(String(50), nullable=True)
    service = Column(String(255), nullable=True)
    
    forecast_date = Column(DateTime, nullable=False, index=True)
    predicted_cost = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=True)
    upper_bound = Column(Float, nullable=True)
    
    generated_at = Column(DateTime, default=datetime.utcnow)

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    provider = Column(String(50), nullable=False)
    resource_id = Column(String(512), nullable=False, index=True)
    resource_type = Column(String(100), nullable=True)
    
    recommendation_type = Column(String(100), nullable=False) # e.g. idle_resource, rightsize, reserved_instance
    description = Column(Text, nullable=False)
    
    potential_savings = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    
    status = Column(String(50), default="open") # open, ignored, implemented
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
