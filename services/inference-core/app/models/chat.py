from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID

class ChatMessageRequest(BaseModel):
    query_text: str = Field(..., description="The user's question or message")
    client_id: str = Field(..., description="The tenant/client identifier")
    conversation_id: Optional[UUID] = Field(None, description="Existing conversation ID if applicable")
    user_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context about the user")

class SourceDocument(BaseModel):
    content_id: str
    title: Optional[str] = None
    body_content: str
    score: float
    metadata: Dict[str, Any]

class ChatMessageResponse(BaseModel):
    answer: str = Field(..., description="The AI generated response")
    sources: List[SourceDocument] = Field(default_factory=list, description="The sources used to generate the answer")
    conversation_id: UUID = Field(..., description="The conversation ID for this session")

class LeadScoringResult(BaseModel):
    score_engagement: int = Field(0, ge=-20, le=30)
    score_finance: int = Field(0, ge=-10, le=30)
    score_timeline: int = Field(0, ge=0, le=20)
    score_match: int = Field(0, ge=0, le=15)
    score_info: int = Field(0, ge=-3, le=5)
    reasoning: str = Field(..., description="Breve explicación del porqué de estos puntajes")
