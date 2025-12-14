from pydantic import BaseModel, constr, validator
from uuid import UUID
import re


class BaseAISchema(BaseModel):
    message: constr(min_length=2, max_length=1000)

    @validator("message")
    def clean_message(cls, v: str) -> str:
        # Allow Unicode but clean dangerous characters for AI processing
        # Remove control characters but keep printable Unicode
        cleaned = re.sub(r"[\x00-\x1f\x7f]", " ", v)
        return cleaned.strip()


class AICreateRecipeSchema(BaseAISchema):
    pass


class AIModifyRecipeSchema(BaseAISchema):
    recipe_id: UUID
