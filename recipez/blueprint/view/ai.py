from flask import Blueprint, jsonify, request, session, redirect, url_for, flash, current_app
from datetime import datetime

from recipez.form import (
    AICreateRecipeForm,
    AIModifyRecipeForm,
)
from recipez.utils import (
    RecipezAuthNUtils,
    RecipezAuthZUtils,
    RecipezAIUtils,
    RecipezErrorUtils,
    RecipezRecipeUtils,
    RecipezResponseUtils,
)

bp = Blueprint("ai", __name__, url_prefix="/ai")

# Security constants for session storage limits
MAX_RESPONSE_SIZE = 50000  # 50KB max for raw response
MAX_INGREDIENTS = 50
MAX_STEPS = 30


def _set_ai_error_state(workflow: str) -> None:
    """
    Set AI error state in session for JavaScript detection.

    Args:
        workflow: The workflow type ('create' or 'modify')
    """
    session["ai_error_state"] = {
        "workflow": workflow,
        "timestamp": datetime.utcnow().isoformat()
    }


@bp.route("/create", methods=["POST"])
@RecipezAuthNUtils.login_required
@RecipezAuthZUtils.ai_create_recipe_required
def ai_create_recipe():
    """
    Create a recipe using AI assistance.

    This view handles form submission via standard POST request.
    On success, stores AI response in session and redirects to recipe creation page.
    On failure, flashes error message and re-renders current page.

    Returns:
        Response: Redirect to recipe creation page or re-rendered template with errors.
    """
    name = "ai_create_recipe"
    form = AICreateRecipeForm()

    # Get nonces for template rendering (needed for error re-render)
    script_nonce, link_nonce = RecipezResponseUtils.generate_nonces()

    # Prepare template params for potential error re-render
    template_params = {
        "template": "index.html",  # Default fallback
        "script_nonce": script_nonce,
        "link_nonce": link_nonce,
        "ai_create_form": form,  # Include form with errors
        "ai_modify_form": AIModifyRecipeForm(),  # Include empty modify form
    }

    # Validate form (includes CSRF check)
    if not form.validate_on_submit():
        # Form validation failed - flash error and re-render
        _set_ai_error_state("create")
        flash("Please provide a valid recipe description (2-500 characters) and try again.", "error")
        return RecipezErrorUtils.handle_view_error(
            name,
            request,
            "Form validation failed",
            None,
            **template_params
        )

    try:
        # Call AI utility to generate recipe
        response = RecipezAIUtils.create_recipe(
            session.get("user_jwt", ""),
            request,
            form.message.data
        )

        # Check if response contains error
        if "error" in response:
            _set_ai_error_state("create")
            # Log detailed error, show generic message to user
            current_app.logger.error(f"AI request failed: {response['error']}, user: {session.get('user_id')}")
            flash("Unable to generate recipe. Please try again or contact support if the issue persists.", "error")
            return RecipezErrorUtils.handle_view_error(
                name,
                request,
                "AI request failed",
                None,
                **template_params
            )

        # Success - parse AI response into structured data
        # Handle both wrapped and unwrapped response formats
        if "response" in response:
            raw_response = response["response"]
        else:
            # Response is already unwrapped (has 'recipe' directly)
            raw_response = response

        recipe_text = raw_response.get("recipe", "") if isinstance(raw_response, dict) else str(raw_response)

        # Validate recipe_text is not empty
        if not recipe_text or len(recipe_text.strip()) == 0:
            current_app.logger.error("Empty recipe_text received from API")
            _set_ai_error_state("create")
            flash("AI service returned empty response. Please try again.", "error")
            return RecipezErrorUtils.handle_view_error(
                name,
                request,
                "Empty API response",
                None,
                **template_params
            )

        # Parse the recipe response to extract structured data
        parsed_recipe = RecipezAIUtils.parse_recipe_response(recipe_text)

        # Validate and limit parsed data to prevent session storage exhaustion
        if len(parsed_recipe.get("ingredients", [])) > MAX_INGREDIENTS:
            current_app.logger.warning(
                f"Truncating ingredients from {len(parsed_recipe['ingredients'])} to {MAX_INGREDIENTS}"
            )
            parsed_recipe["ingredients"] = parsed_recipe["ingredients"][:MAX_INGREDIENTS]

        if len(parsed_recipe.get("steps", [])) > MAX_STEPS:
            current_app.logger.warning(
                f"Truncating steps from {len(parsed_recipe['steps'])} to {MAX_STEPS}"
            )
            parsed_recipe["steps"] = parsed_recipe["steps"][:MAX_STEPS]

        # Return JSON response for AJAX handling
        return jsonify({
            "success": True,
            "recipe": parsed_recipe
        })

    except Exception as e:
        # Unexpected error - log detailed error, show generic message to user
        _set_ai_error_state("create")
        current_app.logger.error(f"AI recipe creation failed: {str(e)}, user: {session.get('user_id')}")
        flash("Unable to generate recipe. Please try again later.", "error")
        return RecipezErrorUtils.handle_view_error(
            name,
            request,
            "AI recipe creation failed",
            e,
            **template_params
        )


@bp.route("/modify", methods=["POST"])
@RecipezAuthNUtils.login_required
@RecipezAuthZUtils.ai_modify_recipe_required
def ai_modify_recipe():
    """
    Modify an existing recipe using AI assistance.

    This view handles form submission via standard POST request.
    On success, stores AI response in session and redirects to recipe edit page.
    On failure, flashes error message and re-renders current page.

    Returns:
        Response: Redirect to recipe edit page or re-rendered template with errors.
    """
    name = "ai_modify_recipe"
    form = AIModifyRecipeForm()

    # Get nonces for template rendering
    script_nonce, link_nonce = RecipezResponseUtils.generate_nonces()

    # Prepare template params for error re-render
    template_params = {
        "template": "index.html",  # Default fallback
        "script_nonce": script_nonce,
        "link_nonce": link_nonce,
        "ai_create_form": AICreateRecipeForm(),
        "ai_modify_form": form,  # Include form with errors
    }

    # Validate form (includes CSRF and UUID validation)
    if not form.validate_on_submit():
        _set_ai_error_state("modify")
        flash("Please select a recipe and provide a valid modification description (2-500 characters).", "error")
        return RecipezErrorUtils.handle_view_error(
            name,
            request,
            "Form validation failed",
            None,
            **template_params
        )

    try:
        # Verify recipe exists and user has access
        recipe_response = RecipezRecipeUtils.read_recipe(
            session.get("user_jwt", ""),
            form.recipe_id.data,
            request
        )

        if not recipe_response or "error" in recipe_response:
            _set_ai_error_state("modify")
            # Log detailed error with recipe ID, show generic message to user
            current_app.logger.warning(f"Recipe not found: {form.recipe_id.data}, user: {session.get('user_id')}")
            flash("Recipe not found. Please select a different recipe.", "error")
            return RecipezErrorUtils.handle_view_error(
                name,
                request,
                "Recipe not found",
                None,
                **template_params
            )

        # Check user has permission to modify this recipe
        if recipe_response.get("recipe_author_id") != session.get("user_id"):
            _set_ai_error_state("modify")
            # Log detailed error, show generic message to user
            current_app.logger.warning(f"Permission denied for recipe: {form.recipe_id.data}, user: {session.get('user_id')}")
            flash("You don't have permission to modify this recipe. Please select one of your own recipes.", "error")
            return RecipezErrorUtils.handle_view_error(
                name,
                request,
                "Permission denied",
                None,
                **template_params
            )

        # Call AI utility to modify recipe
        response = RecipezAIUtils.modify_recipe(
            session.get("user_jwt", ""),
            request,
            form.recipe_id.data,
            form.message.data
        )

        # Check if response contains error
        if "error" in response:
            _set_ai_error_state("modify")
            # Log detailed error, show generic message to user
            current_app.logger.error(f"AI modification failed: {response['error']}, user: {session.get('user_id')}")
            flash("Unable to modify recipe. Please try again later.", "error")
            return RecipezErrorUtils.handle_view_error(
                name,
                request,
                "AI modification failed",
                None,
                **template_params
            )

        # Success - parse AI response into structured data
        # Handle both wrapped and unwrapped response formats
        if "response" in response:
            raw_response = response["response"]
        else:
            # Response is already unwrapped (has 'recipe' directly)
            raw_response = response

        # For modify, we store the full response (API will parse later)
        recipe_content = raw_response.get("recipe", "") if isinstance(raw_response, dict) else str(raw_response)

        # Validate recipe content is not empty
        if not recipe_content or len(recipe_content.strip()) == 0:
            current_app.logger.error("Empty recipe content received from API")
            _set_ai_error_state("modify")
            flash("AI service returned empty response. Please try again.", "error")
            return RecipezErrorUtils.handle_view_error(
                name,
                request,
                "Empty API response",
                None,
                **template_params
            )

        # Parse the recipe content into structured data
        parsed_recipe = RecipezAIUtils.parse_recipe_response(recipe_content)

        # Return JSON response for AJAX handling
        return jsonify({
            "success": True,
            "recipe": parsed_recipe,
            "recipe_id": str(form.recipe_id.data)
        })

    except Exception as e:
        # Unexpected error - log detailed error, show generic message to user
        _set_ai_error_state("modify")
        current_app.logger.error(f"AI recipe modification failed: {str(e)}, user: {session.get('user_id')}")
        flash("Unable to modify recipe. Please try again later.", "error")
        return RecipezErrorUtils.handle_view_error(
            name,
            request,
            "AI recipe modification failed",
            e,
            **template_params
        )
