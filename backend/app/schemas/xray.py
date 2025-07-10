from pydantic import BaseModel
from typing import Optional, Dict, Any

class XrayUserCreate(BaseModel):
    email: str
    full_name: Optional[str] = None
    protocol: str = "vless"

class XrayConfigCreate(BaseModel):
    name: str
    config: Dict[str, Any]
    description: Optional[str] = None

class XrayConfigUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None