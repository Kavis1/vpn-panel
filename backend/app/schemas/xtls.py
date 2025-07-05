""
XTLS Schemas

This module contains Pydantic models for XTLS-related data validation and serialization.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl

class XTLSCertificate(BaseModel):
    """Schema for XTLS certificate information."""
    key_path: str = Field(..., description="Path to the private key file")
    cert_path: str = Field(..., description="Path to the certificate file")
    expires_at: datetime = Field(..., description="Certificate expiration date and time")

class XTLSUserBase(BaseModel):
    """Base schema for XTLS user information."""
    user_id: int = Field(..., description="User ID")
    email: str = Field(..., description="User's email address")
    vless_id: str = Field(..., description="VLESS user ID")
    connection_string: str = Field(..., description="VLESS connection string")

class XTLSUserCreate(XTLSUserBase):
    """Schema for creating a new XTLS user."""
    certificate: XTLSCertificate = Field(..., description="Certificate information")

class XTLSUser(XTLSUserBase):
    """Schema for XTLS user information."""
    certificate: XTLSCertificate = Field(..., description="Certificate information")
    
    class Config:
        orm_mode = True

class XTLSConfig(BaseModel):
    """Schema for XTLS configuration."""
    config: Dict[str, Any] = Field(..., description="Xray configuration")
    certificates_dir: str = Field(..., description="Directory containing XTLS certificates")

class XTLSStats(BaseModel):
    """Schema for XTLS statistics."""
    total_users: int = Field(..., description="Total number of XTLS users")
    active_users: int = Field(..., description="Number of active XTLS users")
    certificate_expirations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of upcoming certificate expirations"
    )

class XTLSReload(BaseModel):
    """Schema for XTLS reload response."""
    success: bool = Field(..., description="Whether the reload was successful")
    message: str = Field(..., description="Status message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the reload")

class XTLSConnectionInfo(BaseModel):
    """Schema for XTLS connection information."""
    protocol: str = Field(..., description="Connection protocol (e.g., 'vless')")
    address: str = Field(..., description="Server address")
    port: int = Field(..., description="Server port")
    security: str = Field(..., description="Security type (e.g., 'xtls')")
    flow: str = Field(..., description="XTLS flow type")
    sni: Optional[str] = Field(None, description="Server Name Indication")
    alpn: Optional[List[str]] = Field(None, description="Application-Layer Protocol Negotiation")
    fingerprint: Optional[str] = Field(None, description="TLS fingerprint")
    public_key: Optional[str] = Field(None, description="Public key for XTLS")
    short_id: Optional[str] = Field(None, description="Short ID for XTLS")
    spider_x: Optional[str] = Field(None, description="SpiderX header for XTLS")
