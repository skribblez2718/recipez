from flask import (
    Blueprint,
    flash,
    redirect,
    request,
    session,
    url_for,
)
from typing import Union, Any

from recipez.utils import (
    RecipezAuthNUtils,
    RecipezAuthZUtils,
    RecipezCategoryUtils,
    RecipezRecipeUtils,
    RecipezResponseUtils,
    RecipezErrorUtils,
)
from recipez.form import (
    CreateCategoryForm,
    UpdateCategoryForm,
    DeleteCategoryForm,
)
from recipez.form.ai import AICreateRecipeForm, AIModifyRecipeForm

bp = Blueprint("category", __name__, url_prefix="/category")


#########################[ start create_category ]#########################
@bp.route("/create", methods=["GET", "POST"])
@RecipezAuthNUtils.login_required
@RecipezAuthZUtils.category_create_required
def create_category() -> Union[str, Any]:
    """
    Creates a new category.

    Returns:
        A string or a response object containing the template and script nonce.
    """
    name = f"category.{create_category.__name__}"
    category_error = (
        "RecipezCategoryUtils.create_category returned an invalid response: {error_msg}"
    )
    response_msg = "An error occurred while creating the category"
    script_nonce, link_nonce = RecipezResponseUtils.generate_nonces()
    template_params = {
        "template": "category/create_category.html",
        "script_nonce": script_nonce,
        "link_nonce": link_nonce,
        "js_modules": {"recipe": True},
        "form": CreateCategoryForm(),
        "ai_create_form": AICreateRecipeForm(),
        "ai_modify_form": AIModifyRecipeForm(),
        "recipes": [],  # For AI dropdown modify workflow
        "categories": [],  # For AI dropdown form generation
    }

    # Fetch all recipes for AI dropdown (modify workflow)
    try:
        recipes_response = RecipezRecipeUtils.read_all_recipes(session["user_jwt"], request)
        # make_request already extracts "response" key, so recipes_response is a list
        if recipes_response and not isinstance(recipes_response, dict):
            template_params["recipes"] = recipes_response
        elif isinstance(recipes_response, dict) and "error" not in recipes_response:
            template_params["recipes"] = recipes_response.get("response", [])
    except Exception:
        pass  # Silently fail - AI dropdown will just have empty recipes

    # Fetch all categories for AI dropdown (form generation)
    try:
        categories_response = RecipezCategoryUtils.read_all_categories(session["user_jwt"], request)
        # make_request already extracts "response" key, so categories_response is a list
        if categories_response and not isinstance(categories_response, dict):
            template_params["categories"] = categories_response
        elif isinstance(categories_response, dict) and "error" not in categories_response:
            template_params["categories"] = categories_response.get("response", [])
    except Exception:
        pass  # Silently fail - AI dropdown will just have empty categories

    create_category_form = template_params["form"]
    if request.method == "POST":
        if not create_category_form.validate_on_submit():
            return RecipezErrorUtils.handle_view_error(
                name, request, None, None, **template_params
            )

        author_id = session.get("user_id", "")
        category_name = create_category_form.data["name"]
        try:
            response = RecipezCategoryUtils.create_category(
                authorization=session.get("user_jwt", ""),
                request=request,
                author_id=author_id,
                category_name=category_name,
            )
        except Exception as e:
            response = RecipezErrorUtils.handle_api_error(
                name, request, e, category_error
            )

        if not response or "error" in response:
            error_msg = response.get("error", category_error)
            error = category_error.format(error_msg=error_msg)
            if "already exists" in error_msg.lower():
                response_msg = error_msg
            return RecipezErrorUtils.handle_view_error(
                name, request, error, response_msg, **template_params
            )

        category_name = response.get("category", {}).get("category_name", "")
        flash(f"Category '{category_name}' created successfully", "success")
        return redirect(url_for("index.index"))

    return RecipezResponseUtils.process_response(
        request,
        **template_params,
    )


#########################[ end create_category ]###########################


#########################[ start update_category ]#########################
@bp.route("/update/<pk>", methods=["GET", "POST"])
@RecipezAuthNUtils.login_required
@RecipezAuthZUtils.category_update_required
def update_category(pk: str) -> Union[str, Any]:
    """
    Updates an existing category.

    Returns:
        A string or a response object containing the template and script nonce.
    """
    name = f"category.{update_category.__name__}"
    category_error = "{method} returned an invalid response: {error_msg}"
    response_msg = ""
    script_nonce, link_nonce = RecipezResponseUtils.generate_nonces()
    template_params = {
        "template": "category/update_category.html",
        "script_nonce": script_nonce,
        "link_nonce": link_nonce,
        "js_modules": {
            "recipe": True,
            "modal": True,
        },
        "update_form": UpdateCategoryForm(),
        "delete_form": DeleteCategoryForm(),
        "ai_create_form": AICreateRecipeForm(),
        "ai_modify_form": AIModifyRecipeForm(),
        "recipes": [],  # For AI dropdown modify workflow
        "categories": [],  # For AI dropdown form generation
    }

    # Fetch all recipes for AI dropdown (modify workflow)
    try:
        recipes_response = RecipezRecipeUtils.read_all_recipes(session["user_jwt"], request)
        # make_request already extracts "response" key, so recipes_response is a list
        if recipes_response and not isinstance(recipes_response, dict):
            template_params["recipes"] = recipes_response
        elif isinstance(recipes_response, dict) and "error" not in recipes_response:
            template_params["recipes"] = recipes_response.get("response", [])
    except Exception:
        pass  # Silently fail - AI dropdown will just have empty recipes

    # Fetch all categories for AI dropdown (form generation)
    try:
        categories_response = RecipezCategoryUtils.read_all_categories(session["user_jwt"], request)
        # make_request already extracts "response" key, so categories_response is a list
        if categories_response and not isinstance(categories_response, dict):
            template_params["categories"] = categories_response
        elif isinstance(categories_response, dict) and "error" not in categories_response:
            template_params["categories"] = categories_response.get("response", [])
    except Exception:
        pass  # Silently fail - AI dropdown will just have empty categories

    category_id = pk
    template_params["category_id"] = category_id
    update_category_form = template_params["update_form"]
    delete_category_form = template_params["delete_form"]

    try:
        response = RecipezCategoryUtils.read_category_by_id(
            session["user_jwt"], request, category_id
        )
    except Exception as e:
        response = RecipezErrorUtils.handle_api_error(name, request, e, category_error)

    if not response or "error" in response:
        error_msg = response.get("error", category_error)
        error = category_error.format(
            method="RecipezCategoryUtils.read_category_by_id", error_msg=error_msg
        )
        response_msg = "An error occurred while fetching the category"
        return RecipezErrorUtils.handle_view_error(
            name, request, error, response_msg, **template_params
        )

    category = response.get("category")
    category_name = category.get("category_name", "")
    if request.method == "POST":
        if (
            "update_category" in request.form
            and not update_category_form.validate_on_submit()
        ):
            template_params["form"] = update_category_form
            return RecipezErrorUtils.handle_view_error(
                name, request, None, None, **template_params
            )

        if (
            "delete_category" in request.form
            and not delete_category_form.validate_on_submit()
        ):
            template_params["form"] = delete_category_form
            return RecipezErrorUtils.handle_view_error(
                name, request, None, None, **template_params
            )

        if "update_category" in request.form:
            update_category_name = update_category_form.name.data.strip()
            try:
                response = RecipezCategoryUtils.update_category(
                    authorization=session.get("user_jwt", ""),
                    request=request,
                    category_id=category_id,
                    category_name=update_category_name,
                )
            except Exception as e:
                response = RecipezErrorUtils.handle_api_error(
                    name, request, e, category_error
                )

            if not response or "error" in response:
                error_msg = response.get("error", category_error)
                error = category_error.format(
                    method="RecipezCategoryUtils.update_category", error_msg=error_msg
                )
                response_msg = "An error occurred while updating the category"
                return RecipezErrorUtils.handle_view_error(
                    name, request, error, response_msg, **template_params
                )

            updated_category_name = response.get("category", {}).get("category_name", "")
            flash(f"Category '{updated_category_name}' updated successfully", "success")
        elif "delete_category" in request.form:
            try:
                response = RecipezCategoryUtils.delete_category(
                    authorization=session.get("user_jwt", ""),
                    request=request,
                    category_id=category_id,
                )
            except Exception as e:
                response = RecipezErrorUtils.handle_api_error(
                    name, request, e, category_error
                )

            if not response or "error" in response:
                error_msg = response.get("error", category_error)
                error = category_error.format(
                    method="RecipezCategoryUtils.delete_category", error_msg=error_msg
                )
                response_msg = "An error occurred while deleting the category"
                return RecipezErrorUtils.handle_view_error(
                    name, request, error, response_msg, **template_params
                )

            flash(f"Category '{category_name}' deleted successfully", "success")

        return redirect(url_for("index.index"))
    else:
        template_params["update_form"].name.data = category_name

    return RecipezResponseUtils.process_response(
        request,
        **template_params,
    )


#########################[ end update_category ]###########################
