"""
Grocery list API blueprint.

Provides endpoint for generating AI-organized grocery lists from selected recipes
and sending them to the user's email.
"""

from flask import Blueprint, jsonify, request, current_app, g
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from typing import Dict, List, Tuple
import re

from recipez.utils import RecipezAuthNUtils, RecipezAuthZUtils, RecipezErrorUtils, RecipezEmailUtils, RecipezSecretsUtils
from recipez.repository import IngredientRepository
from recipez.schema.grocery import GroceryListRequestSchema
from recipez.extensions import csrf

bp = Blueprint("api/grocery", __name__, url_prefix="/api/grocery")

# Model ID validation pattern
MODEL_ID_PATTERN = re.compile(r"^[a-zA-Z0-9._:-]{1,100}$")


def _get_model():
    """
    Get OpenAI chat model instance for grocery list AI operations.

    Uses the grocery-specific model configuration (RECIPEZ_OPENAI_GROCERY_MODEL_ID)
    which may be a different model/assistant than the recipe creation model.

    Returns:
        ChatOpenAI: Configured OpenAI chat model instance
    """
    model_id = current_app.config.get("RECIPEZ_OPENAI_GROCERY_MODEL_ID", "gpt-3.5-turbo")

    # Additional runtime validation of model ID
    if model_id and not MODEL_ID_PATTERN.match(model_id):
        current_app.logger.error(f"Invalid model ID format at runtime: {model_id}")
        model_id = "gpt-3.5-turbo"  # Fallback to safe default

    return ChatOpenAI(
        api_key=current_app.config.get("RECIPEZ_OPENAI_API_KEY"),
        base_url=current_app.config.get("RECIPEZ_OPENAI_API_BASE") or None,
        model=model_id,
        request_timeout=180.0,  # 3 minutes to handle model loading
    )


def _parse_quantity(qty_str: str) -> float:
    """
    Parse quantity string to float, handling fractions and ranges.

    Args:
        qty_str: Quantity string (e.g., "1.5", "1/2", "1 1/2", "1-2")

    Returns:
        float: Parsed quantity, defaults to 1.0 if parsing fails
    """
    try:
        qty_str = qty_str.strip()

        # Handle ranges like "1-2" - take the average
        if "-" in qty_str and "/" not in qty_str:
            parts = qty_str.split("-")
            if len(parts) == 2:
                low = _parse_quantity(parts[0])
                high = _parse_quantity(parts[1])
                return (low + high) / 2

        # Handle mixed numbers like "1 1/2"
        if " " in qty_str and "/" in qty_str:
            parts = qty_str.split(" ", 1)
            whole = float(parts[0])
            frac_parts = parts[1].split("/")
            if len(frac_parts) == 2:
                return whole + float(frac_parts[0]) / float(frac_parts[1])

        # Handle simple fractions like "1/2", "3/4"
        if "/" in qty_str:
            parts = qty_str.split("/")
            if len(parts) == 2:
                return float(parts[0]) / float(parts[1])

        # Handle decimals and integers
        return float(qty_str)

    except (ValueError, ZeroDivisionError):
        return 1.0  # Default to 1 if parsing fails


def _consolidate_ingredients(recipe_ids: List[str]) -> Dict[Tuple[str, str], float]:
    """
    Fetch and consolidate ingredients from multiple recipes.

    Groups ingredients by (normalized_name, measurement) and sums quantities.

    Args:
        recipe_ids: List of recipe UUID strings

    Returns:
        Dict mapping (name, measurement) tuples to total quantities
    """
    consolidated: Dict[Tuple[str, str], float] = {}

    for recipe_id in recipe_ids:
        ingredients = IngredientRepository.read_ingredients_by_recipe_id(str(recipe_id))

        for ing in ingredients:
            # Normalize ingredient name (lowercase, strip whitespace)
            name = ing.ingredient_name.strip().lower()
            measurement = (
                ing.ingredient_measurement.strip().lower()
                if ing.ingredient_measurement
                else ""
            )

            # Parse quantity
            quantity = _parse_quantity(ing.ingredient_quantity)

            key = (name, measurement)
            consolidated[key] = consolidated.get(key, 0.0) + quantity

    return consolidated


def _format_consolidated_list(consolidated: Dict[Tuple[str, str], float]) -> str:
    """
    Format consolidated ingredients as a simple list for AI processing.

    Args:
        consolidated: Dict mapping (name, measurement) to quantities

    Returns:
        Formatted string with one ingredient per line
    """
    lines = []
    for (name, measurement), quantity in sorted(consolidated.items()):
        # Format quantity nicely (remove trailing zeros)
        qty_str = f"{quantity:g}"
        if measurement:
            lines.append(f"- {qty_str} {measurement} {name}")
        else:
            lines.append(f"- {qty_str} {name}")
    return "\n".join(lines)


def _build_email_html(organized_content: str) -> str:
    """
    Build clean HTML email from AI-organized content.

    Args:
        organized_content: HTML content with department sections from AI

    Returns:
        Complete HTML email document
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Grocery List</title>
    <style>
        body {{
            font-family: Arial, Helvetica, sans-serif;
            background-color: #0f172a;
            margin: 0;
            padding: 0;
            line-height: 1.6;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            padding: 0;
            background-color: #1e293b;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            text-align: center;
            background-color: #0f172a;
            color: white;
            padding: 20px 15px;
            border-bottom: 3px solid #ff6b6b;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .content {{
            padding: 24px;
            color: #e2e8f0;
        }}
        h2 {{
            color: #ff6b6b;
            border-bottom: 2px solid #334155;
            padding-bottom: 8px;
            margin-top: 24px;
            margin-bottom: 12px;
            font-size: 18px;
        }}
        h2:first-child {{
            margin-top: 0;
        }}
        ul {{
            margin: 12px 0;
            padding-left: 24px;
        }}
        li {{
            margin: 8px 0;
            color: #e2e8f0;
            font-size: 15px;
        }}
        .footer {{
            text-align: center;
            padding: 16px;
            color: #94a3b8;
            font-size: 12px;
            background-color: #0f172a;
            border-top: 1px solid #334155;
        }}
        .footer a {{
            color: #ff6b6b;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Your Grocery List</h1>
        </div>
        <div class="content">
            {organized_content}
        </div>
        <div class="footer">
            <p>Generated by <a href="#">Recipez</a></p>
        </div>
    </div>
</body>
</html>"""


#########################[ start send_grocery_list_api ]#########################
@bp.route("/send", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.ai_grocery_list_required
def send_grocery_list_api():
    """
    Generate AI-organized grocery list and send via email.

    Consolidates ingredients from selected recipes, sends to AI for
    department organization, and emails the result to the user.

    Request Body:
        recipe_ids: List of recipe UUID strings

    Returns:
        JSON response with success message or error
    """
    name = "grocery.send_grocery_list_api"
    response_msg = "Failed to generate grocery list"

    # Parse and validate request
    try:
        if not request.is_json or not request.json:
            return jsonify({"error": "JSON request body required"}), 400
        data = GroceryListRequestSchema(**request.json)
    except Exception as e:
        current_app.logger.error(f"Request parsing failed: {type(e).__name__}: {str(e)}")
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    try:
        # Step 1: Consolidate ingredients from all selected recipes
        consolidated = _consolidate_ingredients([str(rid) for rid in data.recipe_ids])

        if not consolidated:
            return jsonify({"error": "Selected recipes have no ingredients"}), 400

        # Step 2: Format ingredients list for AI
        ingredient_list = _format_consolidated_list(consolidated)

        current_app.logger.info(
            f"Grocery list: Processing {len(consolidated)} consolidated ingredients "
            f"from {len(data.recipe_ids)} recipes"
        )

        # Step 3: Send to AI for department organization
        model = _get_model()

        prompt = f"""Organize the following grocery list by store department.
Use these departments: Produce, Dairy, Meat & Seafood, Bakery, Frozen, Pantry, Beverages, Snacks, Condiments & Sauces, Other.

Format your response as HTML with:
- <h2> tags for department names
- <ul> and <li> tags for items within each department
- Only include departments that have items
- Keep the quantities and measurements exactly as provided
- Capitalize ingredient names properly

Grocery list to organize:
{ingredient_list}

Return ONLY the HTML content for the departments and items, no additional text or explanation."""

        resp = model.invoke([HumanMessage(content=prompt)])
        content = getattr(resp, "content", "")

        if not content or len(content.strip()) == 0:
            current_app.logger.error("AI returned empty content for grocery list")
            return jsonify({"error": "AI service returned empty response"}), 500

        # Step 4: Build complete email HTML
        email_html = _build_email_html(content.strip())

        # Step 5: Send email to user (decrypt the encrypted email address)
        user_email = RecipezSecretsUtils.decrypt(g.user.user_email)
        email_result = RecipezEmailUtils.send_email(
            user_email,
            "Your Grocery List from Recipez",
            email_html,
            request,
        )

        if "error" in email_result:
            current_app.logger.error(f"Email send failed: {email_result}")
            return jsonify({"error": f"Failed to send email: {email_result.get('error', 'Unknown')}"}), 500

        current_app.logger.info(f"Grocery list sent to {user_email}")
        return jsonify({"response": {"message": "Grocery list sent to your email"}})

    except Exception as e:
        current_app.logger.error(
            f"Grocery list generation failed: {type(e).__name__}: {str(e)}"
        )
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)


#########################[ end send_grocery_list_api ]#########################
