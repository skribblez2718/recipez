from dataclasses import dataclass


###################################[ start Step ]###################################
@dataclass
class Step:
    """
    Represents a step in a recipe with various attributes including ID, text, author, and associated recipe.

    Attributes:
        step_id (str): The unique identifier for the step.
        step_text (str): The description of the step.
        step_author_id (str): The unique identifier for the author of the step.
        step_recipe_id (str): The unique identifier for the recipe to which the step belongs.
    """

    step_id: str
    step_text: str
    step_author_id: str
    step_recipe_id: str


###################################[ end Step ]###################################
