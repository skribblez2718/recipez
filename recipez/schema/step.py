from pydantic import BaseModel, constr
from typing import List, Optional
from uuid import UUID


###################################[ start BaseStepSchema ]###################################
class BaseStepSchema(BaseModel):
    """
    Schema for validating step fields.

    Attributes:
        step_description (str): The step description.
    """

    step_description: constr(
        min_length=2,
        max_length=2000,
    )


###################################[ end BaseStepSchema ]#####################################


###################################[ start BaseStepsSchema ]###################################
class BaseStepsSchema(BaseModel):
    """
    Schema for validating step name.

    Attributes:
        steps (List[BaseStepSchema]): List of steps.
    """

    steps: List[BaseStepSchema]


###################################[ end BaseStepsSchema ]#####################################


###################################[ start CreateStepsSchema ]###################################
class CreateStepsSchema(BaseStepsSchema):
    """
    Schema for validating step creation.

    Attributes:
        author_id (UUID, optional): The ID of the author.
            If omitted, uses the authenticated user's ID.
        recipe_id (UUID): The ID of the recipe.
    """

    author_id: Optional[UUID] = None
    recipe_id: UUID


###################################[ end CreateStepsSchema ]#####################################


###################################[ start ReadStepsSchema ]#####################################
class ReadStepsSchema(BaseStepsSchema):
    """
    Schema for validating step read.

    Attributes:
        recipe_id (UUID): The ID of the recipe.
    """

    recipe_id: UUID


###################################[ end ReadStepsSchema ]#######################################


###################################[ start UpdateStepsSchema ]#####################################
class UpdateStepsSchema(BaseStepsSchema):
    """
    Schema for validating step update.

    Attributes:
        recipe_id (UUID): The ID of the recipe.
    """

    recipe_id: UUID


###################################[ end UpdateStepsSchema ]#######################################


###################################[ start DeleteStepSchema ]#####################################
class DeleteStepSchema(BaseModel):
    """
    Schema for validating step delete.

    Attributes:
        step_id (UUID): The ID of the step.
    """

    step_id: UUID


###################################[ end DeleteStepSchema ]#######################################


###################################[ start DeleteStepsSchema ]#####################################
class DeleteStepsSchema(BaseStepsSchema):
    """
    Schema for validating step delete.

    Attributes:
        recipe_id (UUID): The ID of the recipe.
    """

    recipe_id: UUID


###################################[ end DeleteStepsSchema ]#######################################
