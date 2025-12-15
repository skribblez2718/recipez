from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
)
from wtforms.validators import InputRequired, Length


###################################[ start StepForm ]#######################################
class StepForm(FlaskForm):
    """
    Form for adding a step with a text field.

    Attributes:
        csrf_token (StringField): CSRF token field.
        step (TextAreaField): Text of the step with validation constraints.
    """

    csrf_token = StringField(None, validators=[InputRequired()])
    step = TextAreaField(
        "",
        validators=[
            InputRequired(),
            Length(
                min=2,
                max=2000,
                message="Step description must be between 2 and 2000 characters long",
            ),
        ],
    )


###################################[ end StepForm ]#########################################
