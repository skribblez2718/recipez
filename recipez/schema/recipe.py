from pydantic import BaseModel, constr
from typing import Optional
from uuid import UUID


###################################[ start CreateRecipeSchema ]#####################################
class CreateRecipeSchema(BaseModel):
    """
    Schema for validating email-based login initiation.

    Attributes:
        recipe_id (UUID): A valid recipe_id
    """

    recipe_name: constr(min_length=2, max_length=100)
    recipe_description: constr(
        min_length=2,
        max_length=2000,
    )
    recipe_category_id: UUID
    recipe_image_id: UUID
    recipe_author_id: Optional[UUID] = None


###################################[ end ReadRecipeSchema ]#######################################


###################################[ start ReadRecipeSchema ]#####################################
class ReadRecipeSchema(BaseModel):
    """
    Schema for validating email-based login initiation.

    Attributes:
        recipe_id (UUID): A valid recipe_id
    """

    recipe_id: UUID


###################################[ end ReadRecipeSchema ]#######################################


###################################[ start UpdateRecipeSchema ]#####################################
class UpdateRecipeSchema(BaseModel):
    """Schema for validating recipe updates."""

    recipe_id: UUID
    recipe_name: constr(min_length=2, max_length=100) | None = None
    recipe_description: constr(min_length=2, max_length=2000) | None = None
    recipe_category_id: UUID | None = None
    recipe_image_id: UUID | None = None


###################################[ end UpdateRecipeSchema ]#####################################


###################################[ start DeleteRecipeSchema ]#####################################
class DeleteRecipeSchema(BaseModel):
    """
    Schema for validating email-based login initiation.

    Attributes:
        recipe_id (UUID): A valid recipe_id
    """

    recipe_id: UUID


###################################[ end DeleteRecipeSchema ]#####################################
