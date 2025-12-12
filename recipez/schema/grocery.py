"""
Grocery list request and response schemas.

Provides Pydantic validation for grocery list API endpoints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List
from uuid import UUID


class GroceryListRequestSchema(BaseModel):
    """Schema for grocery list API request."""

    recipe_ids: List[UUID] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of recipe UUIDs to include in grocery list",
    )

    @field_validator("recipe_ids")
    @classmethod
    def validate_recipe_ids(cls, v: List[UUID]) -> List[UUID]:
        """Validate recipe IDs list."""
        if not v:
            raise ValueError("At least one recipe must be selected")
        if len(v) > 50:
            raise ValueError("Maximum 50 recipes allowed per grocery list")
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for rid in v:
            if rid not in seen:
                seen.add(rid)
                unique.append(rid)
        return unique
