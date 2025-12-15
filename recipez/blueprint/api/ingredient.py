from typing import Dict, List
from uuid import UUID
from flask import Blueprint, g, jsonify, request

from recipez.utils import RecipezAuthNUtils, RecipezAuthZUtils, RecipezErrorUtils
from recipez.repository import IngredientRepository
from recipez.schema import (
    CreateIngredientSchema,
    ReadIngredientSchema,
    UpdateIngredientSchema,
    DeleteIngredientSchema,
)
from recipez.extensions import csrf

bp = Blueprint("api/ingredient", __name__, url_prefix="/api/ingredient")


#########################[ start create_ingredients_api ]#########################
@bp.route("/create", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.ingredient_create_required
def create_ingredients_api() -> Dict:
    """Create ingredients for a recipe."""
    name = f"ingredient.{create_ingredients_api.__name__}"
    response_msg = "Failed to create ingredient"

    try:
        data = CreateIngredientSchema(**request.json)
    except Exception as e:
        return RecipezErrorUtils.handle_validation_error(
            name, request, e, "Invalid ingredient data. Please check all required fields."
        )

    created_ingredients: List[Dict] = []
    # Use provided author_id or fall back to authenticated user's ID
    author_id = str(data.author_id) if data.author_id else str(g.user.user_id)
    try:
        for ingredient in data.ingredients:
            created_ingredient = IngredientRepository.create_ingredient(
                ingredient.ingredient_name,
                ingredient.ingredient_quantity,
                ingredient.ingredient_measurement,
                str(data.recipe_id),
                author_id,
            )
            created_ingredients.append(created_ingredient.as_dict())
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    return jsonify({"response": {"ingredients": created_ingredients}})


#########################[ end create_ingredients_api ]###########################


#########################[ start read_ingredients_api ]###########################
@bp.route("/<pk>", methods=["GET"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.ingredient_read_required
def read_ingredients_api(pk: str) -> Dict:
    """Read a single ingredient."""
    name = "ingredient.read_ingredients_api"
    try:
        data = ReadIngredientSchema(ingredient_id=pk)
    except Exception as e:
        return RecipezErrorUtils.handle_validation_error(
            name, request, e, "Invalid ingredient ID format"
        )

    try:
        ingredient = IngredientRepository.read_ingredient_by_id(str(data.ingredient_id))
        if not ingredient:
            return RecipezErrorUtils.handle_not_found_error(
                name, request, "Ingredient not found"
            )
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(
            name, request, e, "Unable to retrieve ingredient"
        )

    return jsonify({"response": {"ingredient": ingredient.as_dict()}})


#########################[ end read_ingredients_api ]#############################


#########################[ start update_ingredient_api ]#########################
@bp.route("/update/<pk>", methods=["PUT"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.ingedient_update_required
def update_ingredient_api(pk: str) -> Dict:
    """Update an ingredient."""
    name = "ingredient.update_ingredient_api"
    response_msg = "Failed to update ingredient"
    json_data = request.json or {}
    json_data["ingredient_id"] = pk
    try:
        data = UpdateIngredientSchema(**json_data)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)
    try:
        updated = IngredientRepository.update_ingredient(
            str(data.ingredient_id),
            data.ingredient_name,
            data.ingredient_quantity,
            data.ingredient_measurement,
        )
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)
    if not updated:
        return jsonify({"response": {"error": response_msg}})

    return jsonify({"response": {"success": True}})


#########################[ end update_ingredient_api ]###########################


#########################[ start delete_ingredient_api ]#########################
@bp.route("/delete/<pk>", methods=["DELETE"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.ingredient_delete_required
def delete_ingredient_api(pk: str) -> Dict:
    """Delete an ingredient."""
    name = "ingredient.delete_ingredient_api"
    response_msg = "Failed to delete ingredient"
    try:
        data = DeleteIngredientSchema(ingredient_id=pk)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)
    try:
        deleted = IngredientRepository.delete_ingredient(str(data.ingredient_id))
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)
    if not deleted:
        return jsonify({"response": {"error": response_msg}})

    return jsonify({"response": {"success": True}})


#########################[ end delete_ingredient_api ]###########################
