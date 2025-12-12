from pydantic import BaseModel, constr, validator, Field, field_validator
from uuid import UUID
from typing import Any, Optional
import re

ALLOWED_ASCII = r"^[\x00-\x7F]+$"


class BaseAISchema(BaseModel):
    message: constr(min_length=2, max_length=500)

    @validator("message")
    def english_only(cls, v: str) -> str:
        if not re.match(ALLOWED_ASCII, v):
            raise ValueError("non-english characters detected")
        cleaned = re.sub(r"[^A-Za-z0-9 ]+", " ", v)
        return cleaned.lower().strip()


class AICreateRecipeSchema(BaseAISchema):
    pass


class AIModifyRecipeSchema(BaseAISchema):
    recipe_id: UUID


class AISTTSchema(BaseModel):
    """Schema for Speech-to-Text API requests with relaxed validation for transcriptions."""

    class Config:
        # Allow audio file upload
        arbitrary_types_allowed = True

    # Audio file validation - using Pydantic v2 field validators
    audio_file: Optional[Any] = Field(None, description="Audio file for transcription")

    @field_validator('audio_file')
    @classmethod
    def validate_audio_file(cls, v):
        """Validate audio file type and size."""
        if v is None:
            raise ValueError("Audio file is required")

        # Add file size validation (e.g., max 25MB for OpenAI STT)
        max_size = 25 * 1024 * 1024  # 25MB
        if hasattr(v, 'content_length') and v.content_length > max_size:
            raise ValueError(f"Audio file too large. Maximum size: {max_size} bytes")

        # Validate MIME type
        allowed_types = [
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav',
            'audio/mp4', 'audio/x-m4a', 'audio/webm', 'audio/flac'
        ]
        if hasattr(v, 'content_type') and v.content_type not in allowed_types:
            raise ValueError(f"Unsupported audio format. Allowed: {', '.join(allowed_types)}")

        return v
