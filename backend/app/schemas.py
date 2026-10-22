from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class InteractionBase(BaseModel):
    hcp_id: int
    interaction_type: Optional[str] = None
    interaction_date: Optional[datetime] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    followup_actions: Optional[str] = None


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = None
    interaction_date: Optional[datetime] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    followup_actions: Optional[str] = None


class InteractionOut(InteractionBase):
    id: int
    created_via: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    hcp_id: Optional[int] = None
    current_interaction_id: Optional[int] = None
    current_form: Optional[dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    form_update: Optional[dict[str, Any]] = None

