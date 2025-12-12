from dataclasses import dataclass


###################################[ start Ingredient ]###################################
@dataclass
class Ingredient:
    """
    Represents an ingredient with various attributes including ID, name, quantity, measurement, author, and associated recipe.

    Attributes:
        ingredient_id (str): The unique identifier for the ingredient.
        ingredient_name (str): The name of the ingredient.
        ingredient_quantity (str): The quantity of the ingredient required.
        ingredient_measurement (str): The unit of measurement for the ingredient.
        ingredient_author_id (str): The unique identifier for the author of the ingredient.
        ingredient_recipe_id (str): The unique identifier for the recipe to which the ingredient belongs.
    """

    ingredient_id: str
    ingredient_name: str
    ingredient_quantity: str
    ingredient_measurement: str
    ingredient_author_id: str
    ingredient_recipe_id: str


###################################[ end Ingredient ]###################################
