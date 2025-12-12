from dataclasses import dataclass


###################################[ start Recipe ]###################################
@dataclass
class Recipe:
    """
    Represents a recipe with various attributes including ID, name, description, category, image, and author.

    Attributes:
        recipe_id (str): The unique identifier for the recipe.
        recipe_name (str): The name of the recipe.
        recipe_description (str): A detailed description of the recipe.
        recipe_category_id (str): The unique identifier for the category to which the recipe belongs.
        recipe_image_id (str): The unique identifier for the image associated with the recipe.
        recipe_author_id (str): The unique identifier for the author of the recipe.
    """

    recipe_id: str
    recipe_name: str
    recipe_description: str
    recipe_category_id: str
    recipe_image_id: str
    recipe_author_id: str


###################################[ end Recipe ]###################################
