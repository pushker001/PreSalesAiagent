from pydantic import BaseModel
from typing import Optional, Dict, Any

class OrganizationSettingsUpdate(BaseModel):
    brand_voice: Optional[str] = None
    sender_settings: Optional[Dict[str, Any]] = None
class OrganizationSettingsResponse(BaseModel):
    org_id: str
    brand_voice: Optional[str]
    sender_settings: Optional[Dict[str, Any]]