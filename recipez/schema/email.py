from typing import List, Dict, Optional
from pydantic import BaseModel, EmailStr, HttpUrl, constr


###################################[ start EmailCodeSchema ]###################################
class EmailCodeSchema(BaseModel):
    """
    Schema for validating email-based login initiation.

    Attributes:
        email (EmailStr): A valid email address for the user.
        code (str): The verification code in the format XXX-XXX (alphanumeric).
    """

    email: EmailStr
    code: constr(pattern=r"^[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}$")


###################################[ end EmailCodeSchemaa ]#####################################


###################################[ start EmailInviteSchema ]###################################
class EmailInviteSchema(BaseModel):
    """Schema for validating recipe invitation emails."""

    email: EmailStr
    invite_link: HttpUrl
    sender_name: constr(min_length=2, max_length=50)


###################################[ end EmailInviteSchema ]#####################################


###################################[ start EmailRecipeShareSchema ]###################################
class EmailRecipeShareSchema(BaseModel):
    """Schema for validating recipe sharing emails."""

    email: EmailStr
    recipe_name: constr(min_length=2, max_length=100)
    recipe_link: HttpUrl
    sender_name: constr(min_length=2, max_length=50)


###################################[ end EmailRecipeShareSchema ]###################################


###################################[ start EmailRecipeShareFullSchema ]###################################
class EmailRecipeShareFullSchema(BaseModel):
    """
    Schema for validating full recipe sharing emails with complete recipe content.

    Attributes:
        email (EmailStr): A valid email address for the recipient.
        recipe_name (str): Name of the recipe being shared.
        recipe_description (str): Optional description of the recipe.
        recipe_ingredients (List[Dict[str, str]]): List of ingredients with quantity, measurement, name.
        recipe_steps (List[str]): List of recipe steps.
        sender_name (str): Name of the person sharing the recipe.
    """

    email: EmailStr
    recipe_name: constr(min_length=2, max_length=100)
    recipe_description: Optional[constr(max_length=500)] = None
    recipe_ingredients: List[Dict[str, str]]
    recipe_steps: List[str]
    sender_name: constr(min_length=2, max_length=50)


###################################[ end EmailRecipeShareFullSchema ]###################################
