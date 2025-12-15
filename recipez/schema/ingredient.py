from pydantic import BaseModel, constr
from typing import List, Optional
from uuid import UUID
from enum import Enum


###################################[ start MeasurementEnum ]###################################
class MeasurementEnum(str, Enum):
    # Weight measurements
    gram = "gram"
    ounce = "ounce"
    pound = "pound"
    kilogram = "kilogram"
    # Volume measurements
    teaspoon = "teaspoon"
    tablespoon = "tablespoon"
    fluid_ounce = "fluid ounce"
    cup = "cup"
    pint = "pint"
    quart = "quart"
    gallon = "gallon"
    milliliter = "milliliter"
    liter = "liter"
    # Abbreviations (kept for compatibility)
    tsp = "tsp"
    Tbsp = "Tbsp"
    # Approximate/colloquial measurements
    pinch = "pinch"
    dash = "dash"
    dollop = "dollop"
    handful = "handful"
    # Item-based measurements
    clove = "clove"
    sprig = "sprig"
    piece = "piece"
    slice = "slice"
    whole = "whole"


###################################[ end MeasurementEnum ]#####################################


###################################[ start BaseIngredientSchema ]###################################
class BaseIngredientSchema(BaseModel):
    """
    Schema for validating ingredient fields.

    Attributes:
        ingredient_quantity (str): Quantity of the ingredient.
        ingredient_measurement (str): Measurement unit (must be one of the allowed values).
        ingredient_name (str): Name of the ingredient.
    """

    ingredient_quantity: constr(
        pattern=r"^(\d+(\.\d+)?|\d+/\d+)(\s*-\s*(\d+(\.\d+)?|\d+/\d+))?$",
        strip_whitespace=True,
    )
    ingredient_measurement: MeasurementEnum
    ingredient_name: constr(
        min_length=2, max_length=100, pattern=r"^[a-zA-Z0-9\s()\-°,'/%.&:\u2010-\u2015\u2212\u2018\u2019\u00BC-\u00BE\u2153\u2154éèêëàâäùûüôöîïçñáíóúÉÈÊËÀÂÄÙÛÜÔÖÎÏÇÑÁÍÓÚ]+$", strip_whitespace=True
    )


###################################[ end BaseIngredientSchema ]#####################################


###################################[ start BaseIngredientsSchema ]###################################
class BaseIngredientsSchema(BaseModel):
    """
    Schema for validating ingredient name.

    Attributes:
        ingredients (List[BaseIngredientSchema]): List of ingredients.
    """

    ingredients: List[BaseIngredientSchema]


###################################[ end BaseIngredientsSchema ]#####################################


###################################[ start CreateIngredientSchema ]###################################
class CreateIngredientSchema(BaseIngredientsSchema):
    """
    Schema for validating ingredient creation.

    Attributes:
        author_id (UUID, optional): The ID of the author.
            If omitted, uses the authenticated user's ID.
        recipe_id (UUID): The ID of the recipe.
    """

    author_id: Optional[UUID] = None
    recipe_id: UUID


###################################[ end CreateIngredientSchema ]#####################################


###################################[ start ReadIngredientSchema ]#####################################
class ReadIngredientSchema(BaseModel):
    """
    Schema for validating ingredient read.

    Attributes:
        ingredient_id (UUID): The ID of the ingredient.
    """

    ingredient_id: UUID


###################################[ end ReadIngredientSchema ]#######################################


###################################[ start UpdateIngredientSchema ]#####################################
class UpdateIngredientSchema(BaseIngredientSchema):
    """
    Schema for validating ingredient update.

    Attributes:
        ingredient_id (UUID): The ID of the ingredient.
    """

    ingredient_id: UUID


###################################[ end UpdateIngredientSchema ]#######################################


###################################[ start DeleteIngredientSchema ]#####################################
class DeleteIngredientSchema(BaseModel):
    """
    Schema for validating ingredient update.

    Attributes:
        ingredient_id (UUID): The ID of the ingredient.
    """

    ingredient_id: UUID


###################################[ end DeleteIngredientSchema ]#######################################
