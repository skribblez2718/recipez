from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, HiddenField, SubmitField
from wtforms.validators import InputRequired, Length, UUID as UUIDValidator


###################################[ start AICreateRecipeForm ]###################################
class AICreateRecipeForm(FlaskForm):
    """
    Flask-WTF form for AI recipe creation with CSRF protection.

    This form validates user input for AI-powered recipe generation, ensuring
    proper CSRF token validation and message length constraints.

    Attributes:
        csrf_token (StringField): CSRF token field for security validation.
        message (TextAreaField): Recipe description/request from user (2-500 chars).
        submit (SubmitField): Submit button for form submission.
    """

    csrf_token = StringField(None, validators=[InputRequired()])
    message = TextAreaField(
        "Recipe Description",
        validators=[
            InputRequired(message="Please describe the recipe you want to create"),
            Length(
                min=2,
                max=500,
                message="Recipe description must be between 2 and 500 characters"
            ),
        ],
    )
    submit = SubmitField("Generate Recipe")


###################################[ end AICreateRecipeForm ]###################################


###################################[ start AIModifyRecipeForm ]###################################
class AIModifyRecipeForm(FlaskForm):
    """
    Flask-WTF form for AI recipe modification with CSRF protection.

    This form validates user input for AI-powered recipe modifications, ensuring
    proper CSRF token validation, UUID format validation for recipe selection,
    and message length constraints.

    Attributes:
        csrf_token (StringField): CSRF token field for security validation.
        recipe_id (HiddenField): UUID of the recipe to modify.
        message (TextAreaField): Modification instructions from user (2-500 chars).
        submit (SubmitField): Submit button for form submission.
    """

    csrf_token = StringField(None, validators=[InputRequired()])
    recipe_id = HiddenField(
        "Recipe ID",
        validators=[
            InputRequired(message="Please select a recipe to modify"),
            UUIDValidator(message="Invalid recipe ID format"),
        ],
    )
    message = TextAreaField(
        "Modification Request",
        validators=[
            InputRequired(message="Please describe your modifications"),
            Length(
                min=2,
                max=500,
                message="Modification description must be between 2 and 500 characters"
            ),
        ],
    )
    submit = SubmitField("Modify Recipe")


###################################[ end AIModifyRecipeForm ]###################################
