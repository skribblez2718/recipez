from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, PasswordField, SubmitField
from wtforms.validators import Email, InputRequired, Length, EqualTo, Regexp


###################################[ start EmailForm ]###################################
class EmailForm(FlaskForm):
    """
    A Flask form for entering an email to receive a login code.

    Attributes:
        csrf_token (StringField): A CSRF token field that is required.
        email (StringField): An email field that is required and must be a valid email address.
        submit (SubmitField): A submit button labeled "Send Code".
    """

    csrf_token: StringField = StringField(None, validators=[InputRequired()])
    email: StringField = StringField(
        "Email",
        validators=[
            InputRequired(),
            Email(message="Invalid email."),
        ],
    )
    submit: SubmitField = SubmitField("Send Code")


###################################[ end EmailForm ]#####################################


###################################[ start CodeForm ]####################################
class CodeForm(FlaskForm):
    """
    A Flask form for verifying a login code using 8 individual character fields.

    Attributes:
        csrf_token (StringField): A CSRF token field that is required.
        email (HiddenField): A hidden field for the user's email.
        code1-code8 (StringField): Individual character fields for the verification code.
        code_hidden (HiddenField): A hidden field that stores the complete code.
        submit (SubmitField): A submit button labeled "Verify".
    """

    csrf_token: StringField = StringField(None, validators=[InputRequired()])
    email: HiddenField = HiddenField(
        None,
        validators=[
            InputRequired(),
            Email(message="Invalid email."),
        ],
    )
    # Individual character fields for the verification code
    code1: StringField = StringField(
        "1",
        validators=[InputRequired(), Regexp(r"^[a-zA-Z0-9]$"), Length(min=1, max=1)],
    )
    code2: StringField = StringField(
        "2",
        validators=[InputRequired(), Regexp(r"^[a-zA-Z0-9]$"), Length(min=1, max=1)],
    )
    code3: StringField = StringField(
        "3",
        validators=[InputRequired(), Regexp(r"^[a-zA-Z0-9]$"), Length(min=1, max=1)],
    )
    code4: StringField = StringField(
        "4",
        validators=[InputRequired(), Regexp(r"^[a-zA-Z0-9]$"), Length(min=1, max=1)],
    )
    code5: StringField = StringField(
        "5",
        validators=[InputRequired(), Regexp(r"^[a-zA-Z0-9]$"), Length(min=1, max=1)],
    )
    code6: StringField = StringField(
        "6",
        validators=[InputRequired(), Regexp(r"^[a-zA-Z0-9]$"), Length(min=1, max=1)],
    )
    code7: StringField = StringField(
        "7",
        validators=[InputRequired(), Regexp(r"^[a-zA-Z0-9]$"), Length(min=1, max=1)],
    )
    code8: StringField = StringField(
        "8",
        validators=[InputRequired(), Regexp(r"^[a-zA-Z0-9]$"), Length(min=1, max=1)],
    )
    # Hidden field to store the complete code
    code_hidden: HiddenField = HiddenField("Complete Code")
    submit: SubmitField = SubmitField("Verify")


###################################[ end CodeForm ]####################################
