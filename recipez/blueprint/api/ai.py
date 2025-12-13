from flask import Blueprint, jsonify, request, current_app, g
from langchain_core.messages import HumanMessage, SystemMessage
import re

from langchain_openai import ChatOpenAI

from recipez.utils import RecipezAuthNUtils, RecipezAuthZUtils, RecipezErrorUtils
from recipez.repository import RecipeRepository
from recipez.schema import AICreateRecipeSchema, AIModifyRecipeSchema
from recipez.extensions import csrf

bp = Blueprint("api/ai", __name__, url_prefix="/api/ai")

# Model ID validation pattern
MODEL_ID_PATTERN = re.compile(r'^[a-zA-Z0-9._:-]{1,100}$')


def _get_model():
    """
    Get OpenAI chat model instance for recipe AI operations.

    Uses the recipe-specific model configuration (RECIPEZ_OPENAI_RECIPE_MODEL_ID)
    for recipe creation and modification operations.

    Returns:
        ChatOpenAI: Configured OpenAI chat model instance
    """
    model_id = current_app.config.get("RECIPEZ_OPENAI_RECIPE_MODEL_ID", "gpt-3.5-turbo")

    # Additional runtime validation of model ID
    if model_id and not MODEL_ID_PATTERN.match(model_id):
        current_app.logger.error(f"Invalid model ID format at runtime: {model_id}")
        model_id = "gpt-3.5-turbo"  # Fallback to safe default

    return ChatOpenAI(
        api_key=current_app.config.get("RECIPEZ_OPENAI_API_KEY"),
        base_url=current_app.config.get("RECIPEZ_OPENAI_API_BASE") or None,
        model=model_id,
        request_timeout=180.0,  # 3 minutes to handle model loading on first request
    )


def _parse_request_data(request, schema_class):
    """
    Parse and validate request data from JSON body.

    Args:
        request: Flask request object
        schema_class: Pydantic schema class for validation

    Returns:
        Validated schema instance

    Raises:
        ValueError: If request is not JSON or validation fails.

    Example:
        # Correct usage (JavaScript):
        fetch('/api/ai/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: "Create a pasta recipe" })
        });
    """
    if request.is_json and request.json:
        try:
            return schema_class(**request.json)
        except Exception as e:
            raise ValueError(f"Invalid request data format: {str(e)}")
    else:
        raise ValueError(
            "JSON request body required. "
            "Form data is not supported. "
            "Please use Content-Type: application/json with JSON body."
        )


@bp.route("/create", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.ai_create_recipe_required
def ai_create_recipe_api():
    name = "ai.ai_create_recipe_api"
    response_msg = "Failed to generate recipe"

    try:
        data = _parse_request_data(request, AICreateRecipeSchema)
    except Exception as e:
        current_app.logger.error(f"Request parsing failed: {type(e).__name__}: {str(e)}")
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    try:
        model = _get_model()

        # Prepend user message with prompt prefix
        formatted_message = f"Create me a recipe based on the following requirements:\n{data.message}"

        resp = model.invoke([HumanMessage(content=formatted_message)])
        content = getattr(resp, "content", "")

        # Validate content is not empty
        if not content or len(content.strip()) == 0:
            current_app.logger.error("LLM returned empty content!")
            return RecipezErrorUtils.handle_api_error(
                name, request,
                "Empty LLM response",
                "AI service returned empty response"
            )

        # Validate content looks like JSON or markdown
        content_stripped = content.strip()
        if not (content_stripped.startswith('{') or content_stripped.startswith('#')):
            current_app.logger.warning(
                f"LLM response doesn't look like JSON or markdown. First 100 chars: {content_stripped[:100]}"
            )

    except Exception as e:
        current_app.logger.error(f"AI create recipe failed: {type(e).__name__}: {str(e)}")
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    return jsonify({"response": {"recipe": content}})


@bp.route("/modify", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.ai_modify_recipe_required
def ai_modify_recipe_api():
    name = "ai.ai_modify_recipe_api"
    response_msg = "Failed to modify recipe"

    try:
        data = _parse_request_data(request, AIModifyRecipeSchema)
    except Exception as e:
        current_app.logger.error(f"Request parsing failed: {type(e).__name__}: {str(e)}")
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    try:
        recipe = RecipeRepository.get_recipe_by_id(str(data.recipe_id))
        if not recipe:
            current_app.logger.warning(f"Recipe not found: {data.recipe_id}")
            return jsonify({"response": {"error": "Recipe not found"}})

        model = _get_model()

        # Format message with recipe context in user message instead of system message
        formatted_message = (
            f"Below is a recipe I would like to modify:\n"
            f"{recipe.as_dict()}\n"
            f"Modify the above recipe based on the following requirements:\n"
            f"{data.message}"
        )

        resp = model.invoke([HumanMessage(content=formatted_message)])
        content = getattr(resp, "content", "")

        # Validate content is not empty
        if not content or len(content.strip()) == 0:
            current_app.logger.error("LLM returned empty content!")
            return RecipezErrorUtils.handle_api_error(
                name, request,
                "Empty LLM response",
                "AI service returned empty response"
            )

        # Validate content looks like JSON or markdown
        content_stripped = content.strip()
        if not (content_stripped.startswith('{') or content_stripped.startswith('#')):
            current_app.logger.warning(
                f"LLM response doesn't look like JSON or markdown. First 100 chars: {content_stripped[:100]}"
            )

    except Exception as e:
        current_app.logger.error(f"AI modify recipe failed: {type(e).__name__}: {str(e)}")
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    return jsonify({"response": {"recipe": content}})