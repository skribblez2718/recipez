from pydantic import BaseModel, constr, validator
from uuid import UUID
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
