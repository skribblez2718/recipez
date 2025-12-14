from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
)
from wtforms.validators import InputRequired, Length, Regexp


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
            Regexp(
                regex=r"^[0-9a-zA-Z\-_()., '&\n\r\t!?:;#@%\"*/+=°\u00A0\u00BC-\u00BE\u2010-\u2015\u2018\u2019\u201C\u201D\u2022\u2026\u2153\u2154\u2212éèêëàâäùûüôöîïçñáíóúÉÈÊËÀÂÄÙÛÜÔÖÎÏÇÑÁÍÓÚ]+$",
                message="Step description contains invalid characters",
            ),
        ],
    )


###################################[ end StepForm ]#########################################
