from flask import Blueprint, request, session, redirect, url_for, flash
from recipez.utils import (
    RecipezAuthNUtils,
    RecipezCategoryUtils,
    RecipezErrorUtils,
    RecipezProfileUtils,
    RecipezRecipeUtils,
    RecipezResponseUtils,
)
from recipez.form import AICreateRecipeForm, AIModifyRecipeForm
from recipez.repository import ApiKeyRepository

bp = Blueprint("profile", __name__, url_prefix="/profile")


#########################[ start profile ]#########################
@bp.route("/", methods=["GET", "POST"])
@RecipezAuthNUtils.login_required
def profile() -> str:
    """Display and update user profile."""
    name = "profile.profile"
    response_msg = "An error occurred while loading the profile"
    script_nonce, link_nonce = RecipezResponseUtils.generate_nonces()
    ai_create_form = AICreateRecipeForm()
    ai_modify_form = AIModifyRecipeForm()
    template_params = {
        "template": "profile.html",
        "script_nonce": script_nonce,
        "link_nonce": link_nonce,
        "js_modules": {"profile": True},
        "profile": {},
        "ai_create_form": ai_create_form,
        "ai_modify_form": ai_modify_form,
        "jwt_token": session["user_jwt"],
    }
    if request.method == "POST":
        image_file = request.files.get("image")
        if image_file and image_file.filename:
            response = RecipezProfileUtils.update_profile_image(
                session["user_jwt"], request, session["user_id"], image_file
            )
            if not response or "error" in response:
                error_msg = response.get("error", response_msg)
                return RecipezErrorUtils.handle_view_error(
                    name, request, error_msg, response_msg, **template_params
                )
            flash("Profile image updated", "success")
            return redirect(url_for("profile.profile"))
    # GET
    response = RecipezProfileUtils.read_profile(session["user_jwt"], request)
    if not response or "error" in response:
        error_msg = response.get("error", response_msg)
        return RecipezErrorUtils.handle_view_error(
            name, request, error_msg, response_msg, **template_params
        )
    template_params["profile"] = response

    # Fetch recipes for AI dropdown
    try:
        recipes_response = RecipezRecipeUtils.read_all_recipes(session["user_jwt"], request)
        # make_request already extracts "response" key, so recipes_response is a list
        if recipes_response and not isinstance(recipes_response, dict):
            template_params["recipes"] = recipes_response
        elif isinstance(recipes_response, dict) and "error" not in recipes_response:
            template_params["recipes"] = recipes_response.get("response", [])
    except Exception:
        template_params["recipes"] = []

    # Fetch categories for AI dropdown
    try:
        categories_response = RecipezCategoryUtils.read_all_categories(session["user_jwt"], request)
        # make_request already extracts "response" key, so categories_response is a list
        if categories_response and not isinstance(categories_response, dict):
            template_params["categories"] = categories_response
        elif isinstance(categories_response, dict) and "error" not in categories_response:
            template_params["categories"] = categories_response.get("response", [])
    except Exception:
        template_params["categories"] = []

    # Fetch user's API keys
    try:
        api_keys = ApiKeyRepository.get_api_keys_by_user_id(session["user_id"])
        template_params["api_keys"] = [k.as_dict() for k in api_keys]
    except Exception:
        template_params["api_keys"] = []

    # Available scopes for API key creation form
    template_params["available_scopes"] = {
        "resources": {
            "Recipe": ["recipe:create", "recipe:read", "recipe:update", "recipe:delete"],
            "Category": ["category:create", "category:read", "category:update", "category:delete"],
            "Image": ["image:create", "image:read", "image:update", "image:delete"],
            "Ingredient": ["ingredient:create", "ingredient:read", "ingredient:update", "ingredient:delete"],
            "Step": ["step:create", "step:read", "step:update", "step:delete"],
        },
        "ai": {
            "AI Features": ["ai:create-recipe", "ai:modify-recipe", "ai:speech-to-text", "ai:grocery-list"],
        },
        "email": {
            "Email": ["email:recipe:share"],
        },
    }

    # Add api_key JS module
    template_params["js_modules"]["api_key"] = True

    return RecipezResponseUtils.process_response(request, **template_params)


#########################[ end profile ]###########################
