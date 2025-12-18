from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
)
from wtforms.validators import InputRequired, Length, Regexp, AnyOf


###################################[ start IngredientForm ]###################################
class IngredientForm(FlaskForm):
    """
    Form for adding an ingredient with fields for quantity, measurement, and name.

    Attributes:
        csrf_token (StringField): CSRF token field.
        quantity (StringField): Quantity of the ingredient with validation constraints.
        measurement (SelectField): Measurement unit of the ingredient with validation constraints.
        ingredient_name (StringField): Name of the ingredient with validation constraints.
    """

    valid_measurements = [
        # Weight measurements
        "gram",
        "ounce",
        "pound",
        "kilogram",
        # Volume measurements
        "teaspoon",
        "tablespoon",
        "fluid ounce",
        "cup",
        "pint",
        "quart",
        "gallon",
        "milliliter",
        "liter",
        # Abbreviations (kept for compatibility)
        "tsp",
        "Tbsp",
        # Approximate/colloquial measurements
        "pinch",
        "dash",
        "dollop",
        "handful",
        # Item-based measurements
        "clove",
        "sprig",
        "piece",
        "slice",
        "whole",
    ]

    csrf_token = StringField(None, validators=[InputRequired()])
    quantity = StringField(
        "Quantity",
        validators=[
            InputRequired(),
            Regexp(
                regex=r"^(\d*\.?\d+|\d+/\d+)(\s*-\s*(\d*\.?\d+|\d+/\d+))?$",
                message="Quantity must be an integer, decimal or fraction, or a range of integers, decimals or fractions",
            ),
        ],
    )
    # Initialize without choices; they will be set later.
    measurement = SelectField(
        "Measurement",
        validators=[
            InputRequired(),
            AnyOf(
                values=valid_measurements,
                message=f"Invalid measurement. Allowed measurements are: {', '.join(valid_measurements)}",
            ),
        ],
    )
    ingredient_name = StringField(
        "Name",
        validators=[
            InputRequired(),
            Length(
                min=2,
                max=100,
                message="Ingredient name must be between 2 and 100 characters long",
            ),
        ],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the choices here, when the application context is active.
        self.measurement.choices = self.valid_measurements


###################################[ end IngredientForm ]###################################
