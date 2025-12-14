from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import InputRequired, Length, Regexp


###################################[ start BaseCategoryForm ]###################################
class BaseCategoryForm(FlaskForm):
    """
    Base form for creating or updating a category with fields for the category name.

    Attributes:
        csrf_token (StringField): CSRF token field.
        name (StringField): Category name field with validation constraints.
        submit (SubmitField): Submit button for form submission.
    """

    csrf_token = StringField(None, validators=[InputRequired()])
    name = StringField(
        "Category Name",
        name="category-name",
        validators=[
            InputRequired(),
            Length(min=2, max=50),
            Regexp(
                regex=r"^[a-zA-Z0-9-_' éèêëàâäùûüôöîïçñáíóúÉÈÊËÀÂÄÙÛÜÔÖÎÏÇÑÁÍÓÚ]+$",
                message="Category name can only contain letters (including accented), numbers, underscores, hyphens, and spaces",
            ),
        ],
    )


###################################[ end BaseCategoryForm ]###################################


###################################[ start CreateCategoryForm ]###################################
class CreateCategoryForm(BaseCategoryForm):
    submit = SubmitField("Create", name="create_category")


###################################[ end CreateCategoryForm ]###################################


###################################[ start UpdateCategoryForm ]###################################
class UpdateCategoryForm(BaseCategoryForm):
    submit = SubmitField("Update", name="update_category")


###################################[ end UpdateCategoryForm ]###################################


###################################[ start DeleteCategoryForm ]###################################
class DeleteCategoryForm(FlaskForm):
    csrf_token = StringField(None, validators=[InputRequired()])
    submit = SubmitField("Yes! Delete this Category", name="delete_category")


###################################[ end DeleteCategoryForm ]###################################
