from pydantic import BaseModel, ConfigDict, constr
from uuid import UUID


###################################[ start CreateRecipeSchema ]#####################################
class CreateRecipeSchema(BaseModel):
    """
    Schema for validating recipe creation.

    Attributes:
        recipe_name (str): Name of the recipe (2-100 characters)
        recipe_description (str): Description of the recipe (2-2000 characters)
        recipe_category_id (UUID): The category ID for the recipe
        recipe_image_id (UUID): The image ID for the recipe
    """

    model_config = ConfigDict(extra="forbid")

    recipe_name: constr(min_length=2, max_length=100)
    recipe_description: constr(
        min_length=2,
        max_length=2000,
    )
    recipe_category_id: UUID
    recipe_image_id: UUID


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
