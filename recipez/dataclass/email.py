from dataclasses import dataclass
from typing import List, Dict


###################################[ start EmailInvite ]###################################
@dataclass
class EmailInvite:
    """Data class representing an invitation email payload."""

    email: str
    invite_link: str
    sender_name: str


###################################[ end EmailInvite ]###################################


###################################[ start EmailRecipeShare ]###################################
@dataclass
class EmailRecipeShare:
    """Data class representing a recipe sharing email payload."""

    email: str
    recipe_name: str
    recipe_link: str
    sender_name: str


###################################[ end EmailRecipeShare ]###################################


###################################[ start EmailRecipeShareFull ]###################################
@dataclass
class EmailRecipeShareFull:
    """Data class representing a full recipe sharing email payload with complete recipe content."""

    email: str
    recipe_name: str
    recipe_description: str
    recipe_ingredients: List[Dict[str, str]]
    recipe_steps: List[str]
    sender_name: str


###################################[ end EmailRecipeShareFull ]###################################
