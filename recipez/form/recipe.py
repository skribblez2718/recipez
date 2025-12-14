from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    FieldList,
    FormField,
    SelectField,
    FileField,
    TextAreaField,
    SubmitField,
)
from wtforms.validators import InputRequired, Length, Regexp

from recipez.form.ingredient import IngredientForm
from recipez.form.step import StepForm


###################################[ start BaseRecipeForm ]###############################
class BaseRecipeForm(FlaskForm):
    """
    Base form for creating and updating a recipe with fields for image, category, name, description, ingredients, and steps.

    Attributes:
        csrf_token (StringField): CSRF token field.
        image (FileField): Image file field.
        category_selector (SelectField): Category selector field with validation constraints.
        name (StringField): Name of the recipe with validation constraints.
        description (TextAreaField): Description of the recipe with validation constraints.
        ingredient (FieldList): List of ingredients using IngredientForm.
        step (FieldList): List of steps using StepForm.
    """

    def validate(self, *args, **kwargs) -> bool:
        rv = super().validate(*args, **kwargs)
        if not rv:
            return False

        category_selected = bool(
            self.category_selector.data and str(self.category_selector.data).strip()
        )
        create_category_name = getattr(
            getattr(self, "create_category_form", None), "name", None
        )
        new_category_filled = bool(
            create_category_name
            and create_category_name.data
            and create_category_name.data.strip()
        )
        if not (category_selected or new_category_filled):
            error_msg = "Category is required"
            self.category_selector.errors.append(error_msg)
            if create_category_name:
                create_category_name.errors.append(error_msg)
            return False
        return True

    csrf_token = StringField(None, validators=[InputRequired()])
    image = FileField("Image")
    category_selector = SelectField(
        "Category",
        name="category-selector",
        coerce=str,
        validators=[
            # InputRequired removed - validation handled conditionally in view
            # If creating new category, this field can be empty or use placeholder
            Regexp(
                regex=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$|^$|^new-category-placeholder$",
                message="Category selector must be a valid UUID",
            ),
        ],
    )
    name = StringField(
        "Name",
        name="recipe-name",
        validators=[
            InputRequired(
                message="Recipe name is required",
            ),
            Length(
                min=2,
                max=100,
                message="Recipe names must be between 2 and 100 characters long",
            ),
            Regexp(
                regex=r"^[0-9a-zA-Z\-_()., '&/\u2010-\u2015\u2212éèêëàâäùûüôöîïçñáíóúÉÈÊËÀÂÄÙÛÜÔÖÎÏÇÑÁÍÓÚ]+$",
                message="Recipe names can only contain letters (including accented), numbers, hyphens, underscores, parentheses, periods, commas, apostrophes, ampersands, slashes and spaces",
            ),
        ],
    )

    description = TextAreaField(
        "Description",
        validators=[
            InputRequired(
                message="Recipe description is required",
            ),
            Length(
                min=2,
                max=2000,
                message="Recipe description must be between 2 and 2000 characters long",
            ),
            Regexp(
                regex=r"^[0-9a-zA-Z\-_()., '&\n\r\t!?:;#@%\"*/+=°\u00A0\u00B7\u00BC-\u00BE\u2010-\u2015\u2018\u2019\u201C\u201D\u2022\u2026\u2153\u2154\u2212éèêëàâäùûüôöîïçñáíóúÉÈÊËÀÂÄÙÛÜÔÖÎÏÇÑÁÍÓÚ]+$",
                message="Recipe description contains invalid characters",
            ),
        ],
    )

    ingredients = FieldList(FormField(IngredientForm), min_entries=1)
    steps = FieldList(FormField(StepForm), min_entries=1)


###################################[ end BaseRecipeForm ]###############################


###################################[ start CreateRecipeForm ]###############################
class CreateRecipeForm(BaseRecipeForm):
    """
    Form for creating a new recipe with fields for image, category, name, description, ingredients, and steps.
    Inherits all fields from BaseRecipeForm and adds a submit button for creation.
    """

    submit = SubmitField("Create", name="submit-recipe")


###################################[ end CreateRecipeForm ]###############################


###################################[ start UpdateRecipeForm ]###############################
class UpdateRecipeForm(BaseRecipeForm):
    """
    Form for updating an existing recipe with fields for image, category, name, description, ingredients, and steps.
    Inherits all fields from BaseRecipeForm and adds a submit button for updating.
    """

    submit = SubmitField("Update", name="update-recipe")


###################################[ end UpdateRecipeForm ]###############################


###################################[ start DeleteRecipeForm ]###############################
class DeleteRecipeForm(FlaskForm):
    """
    Form for deleting a recipe. Contains only CSRF protection and a submit button.
    
    Attributes:
        csrf_token (StringField): CSRF token field for security.
        submit (SubmitField): Submit button for deleting the recipe.
    """
    
    csrf_token = StringField(None, validators=[InputRequired()])
    submit = SubmitField("Delete Recipe", name="delete-recipe")


###################################[ end DeleteRecipeForm ]###############################
