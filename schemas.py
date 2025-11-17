"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name.
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class Appuser(BaseModel):
    """
    Users collection schema
    Collection name: "appuser"
    """
    email: str = Field(..., description="Email address")
    name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")

class Request(BaseModel):
    """
    Requests collection schema
    Collection name: "request"
    """
    email: str = Field(..., description="Owner email")
    text: Optional[str] = Field(None, description="Text message content")
    photo_url: Optional[str] = Field(None, description="Uploaded photo URL")
    audio_url: Optional[str] = Field(None, description="Uploaded audio URL")
    contact_name: Optional[str] = Field(None, description="Contact name shared")
    contact_phone: Optional[str] = Field(None, description="Contact phone shared")
    lat: Optional[float] = Field(None, description="Latitude")
    lng: Optional[float] = Field(None, description="Longitude")
    status: str = Field("sent", description="Request status")
    
# The Flames database viewer reads these schemas from GET /schema endpoint if implemented.
