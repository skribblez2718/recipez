from flask import (
    Blueprint,
    request,
    session,
)

from recipez.form.ai import AICreateRecipeForm, AIModifyRecipeForm
from recipez.utils import (
    RecipezAuthNUtils,
    RecipezAuthZUtils,
    RecipezErrorUtils,
    RecipezCategoryUtils,
    RecipezRecipeUtils,
    RecipezResponseUtils,
)

bp = Blueprint("index", __name__, url_prefix="/")


#########################[ start index ]###################################
@bp.route("/")
@RecipezAuthNUtils.login_required
@RecipezAuthZUtils.recipe_read_required
@RecipezAuthZUtils.category_read_required
def index() -> str:
    """
    Renders the index page by fetching categories and recipes asynchronously,
    processing them, and returning a response with appropriate headers.

    Returns:
        str: The rendered HTML response.
    """
    name = "index.index"
    index_error = "{method} returned an invalid response: {error_msg}"
    response_msg = "An error occurred while loading {objs}"
    script_nonce, link_nonce = RecipezResponseUtils.generate_nonces()
    template_params = {
        "template": "index.html",
        "script_nonce": script_nonce,
        "link_nonce": link_nonce,
        "js_modules": {"search": True, "grocery": True},
        "categories": [],
        "recipes": [],
        "ai_create_form": AICreateRecipeForm(),
        "ai_modify_form": AIModifyRecipeForm(),
    }

    category_response_msg = response_msg.format(objs="categories")
    try:
        response = RecipezCategoryUtils.read_all_categories(
            session["user_jwt"], request
        )
    except Exception as e:
        response = RecipezErrorUtils.handle_api_error(
            name, request, e, category_response_msg
        )

    if not response or "error" in response:
        error_msg = response.get("error", category_response_msg)
        error = index_error.format(
            method="RecipezCategoryUtils.read_all_categories", error_msg=error_msg
        )
        return RecipezErrorUtils.handle_view_error(
            name, request, error, category_response_msg, **template_params
        )

    template_params["categories"] = response.get("response", []) if isinstance(response, dict) else response

    recipe_response_msg = response_msg.format(objs="recipes")
    try:
        response = RecipezRecipeUtils.read_all_recipes(session["user_jwt"], request)
    except Exception as e:
        response = RecipezErrorUtils.handle_api_error(
            name, request, e, recipe_response_msg
        )

    if not response or "error" in response:
        error_msg = response.get("error", recipe_response_msg)
        error = index_error.format(
            method="RecipezRecipeUtils.read_all_recipes", error_msg=error_msg
        )
        return RecipezErrorUtils.handle_view_error(
            name, request, error, recipe_response_msg, **template_params
        )

    template_params["recipes"] = response.get("response", []) if isinstance(response, dict) else response
    template_params["user_jwt"] = session.get("user_jwt", "")

    return RecipezResponseUtils.process_response(
        request,
        **template_params,
    )


#########################[ end index ]#####################################
