from typing import Dict, List, Optional
from uuid import UUID
from flask import Blueprint, jsonify, request, g

from recipez.utils import (
    RecipezAuthNUtils,
    RecipezAuthZUtils,
    RecipezErrorUtils,
    is_valid_uuid,
)
from recipez.repository import (
    RecipeRepository,
    CategoryRepository,
    ImageRepository,
    IngredientRepository,
    StepRepository,
    UserRepository,
)
from recipez.schema import (
    CreateRecipeSchema,
    ReadRecipeSchema,
    UpdateRecipeSchema,
    DeleteRecipeSchema,
)
from recipez.dataclass import Recipe
from recipez.extensions import csrf

bp = Blueprint("api/recipe", __name__, url_prefix="/api/recipe")


#########################[ start create_recipe_api ]############################
@bp.route("/create", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.recipe_create_required
def create_recipe_api() -> Dict:
    """Create a new recipe."""
    name = f"recipe.{create_recipe_api.__name__}"
    response_msg = "Failed to create recipe"

    try:
        data = CreateRecipeSchema(**request.json)
    except Exception as e:
        return RecipezErrorUtils.handle_validation_error(
            name, request, e, "Invalid recipe data. Please check all required fields."
        )
    try:
        # Always use authenticated user's ID (never accept client-provided author_id)
        author_id = str(g.user.user_id)
        recipe = RecipeRepository.create_recipe(
            data.recipe_name,
            data.recipe_description,
            str(data.recipe_category_id),
            str(data.recipe_image_id),
            author_id,
        )
    except ValueError as e:
        if "already exists" in str(e).lower():
            return RecipezErrorUtils.handle_conflict_error(
                name, request, e, "A recipe with this name already exists"
            )
        return RecipezErrorUtils.handle_validation_error(
            name, request, e, "Invalid recipe data"
        )
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    return jsonify({"response": {"recipe": recipe.as_dict()}})


#########################[ end create_recipe_api ]##############################


#########################[ start read_recipes_api ]#############################
@bp.route("/all", methods=["GET"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.recipe_read_required
def read_recipes_api() -> Dict:
    """Return all recipes."""
    name = "recipe.read_recipes_api"
    response_msg = "Failed to fetch recipes"
    try:
        recipes = RecipeRepository.read_all_recipes()
        all_recipes = [r.as_dict() for r in recipes]
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    # Optimize: Fetch all authors in a single query to eliminate N+1 problem
    author_lookup = {}
    try:
        # Collect all unique valid author IDs
        author_ids = set()
        for recipe in all_recipes:
            author_id = recipe.get("recipe_author_id", "")
            if author_id:
                try:
                    # Validate UUID format
                    UUID(str(author_id))
                    author_ids.add(str(author_id))
                except ValueError:
                    # Skip invalid UUIDs
                    pass

        # Fetch all authors in one query if we have valid IDs
        if author_ids:
            authors = UserRepository.get_users_by_ids(list(author_ids))
            author_lookup = {str(author.user_id): author.as_dict() for author in authors}
    except Exception as e:
        # Log error but continue processing recipes without author data
        pass

    for recipe in all_recipes:
        # Lookup category with UUID validation
        category_id = recipe.get("recipe_category_id")
        if category_id and is_valid_uuid(category_id):
            try:
                category = CategoryRepository.read_category_by_id(str(category_id))
                if category:
                    recipe["recipe_category"] = category.as_dict()
            except Exception as e:
                return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

        # Lookup image with UUID validation
        image_id = recipe.get("recipe_image_id")
        if image_id and is_valid_uuid(image_id):
            try:
                image = ImageRepository.read_image_by_id(str(image_id))
                if image:
                    recipe["recipe_image"] = image.as_dict()
            except Exception as e:
                return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

        # Use pre-fetched author data from lookup
        author_id = recipe.get("recipe_author_id", "")
        if author_id and str(author_id) in author_lookup:
            recipe["author"] = author_lookup[str(author_id)]

        recipe_id = recipe.get("recipe_id", "")
        try:
            ingredients = IngredientRepository.read_ingredients_by_recipe_id(
                str(recipe_id)
            )
            all_ingredients = [ingredient.as_dict() for ingredient in ingredients]
        except Exception as e:
            return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

        if all_ingredients:
            recipe["recipe_ingredients"] = all_ingredients

        try:
            steps = StepRepository.read_steps_by_recipe_id(str(recipe_id))
            all_steps = [step.as_dict() for step in steps]
        except Exception as e:
            return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

        if all_steps:
            recipe["recipe_steps"] = all_steps

    return jsonify({"response": all_recipes})


#########################[ end read_recipes_api ]###############################


#########################[ start read_recipe_api ]##############################
@bp.route("/<pk>", methods=["GET"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.recipe_read_required
def read_recipe_api(pk: str) -> Dict:
    """Return a single recipe by id."""
    name = "recipe.read_recipe_api"
    response_msg = "Unable to retrieve recipe"
    try:
        data = ReadRecipeSchema(recipe_id=pk)
    except Exception as e:
        return RecipezErrorUtils.handle_validation_error(
            name, request, e, "Invalid recipe ID format"
        )
    try:
        recipe = RecipeRepository.get_recipe_by_id(str(data.recipe_id))
        if not recipe:
            return RecipezErrorUtils.handle_not_found_error(
                name, request, "Recipe not found"
            )
        recipe = recipe.as_dict()
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(
            name, request, e, "Unable to retrieve recipe"
        )

    # Lookup category with UUID validation
    category_id = recipe.get("recipe_category_id")
    if category_id and is_valid_uuid(category_id):
        try:
            category = CategoryRepository.read_category_by_id(str(category_id))
            if category:
                recipe["recipe_category"] = category.as_dict()
        except Exception as e:
            return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    # Lookup image with UUID validation
    image_id = recipe.get("recipe_image_id")
    if image_id and is_valid_uuid(image_id):
        try:
            image = ImageRepository.read_image_by_id(str(image_id))
            if image:
                recipe["recipe_image"] = image.as_dict()
        except Exception as e:
            return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    # Lookup author with UUID validation
    author_id = recipe.get("recipe_author_id")
    if author_id and is_valid_uuid(author_id):
        try:
            author = UserRepository.get_user_by_id(str(author_id))
            if author:
                recipe["recipe_author"] = author.as_dict()
        except Exception as e:
            return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    recipe_id = recipe.get("recipe_id", "")
    try:
        ingredients = IngredientRepository.read_ingredients_by_recipe_id(str(recipe_id))
        all_ingredients = [ingredient.as_dict() for ingredient in ingredients]
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    if all_ingredients:
        recipe["recipe_ingredients"] = all_ingredients

    try:
        steps = StepRepository.read_steps_by_recipe_id(str(recipe_id))
        all_steps = [step.as_dict() for step in steps]
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    if all_steps:
        recipe["recipe_steps"] = all_steps

    return jsonify({"response": recipe})


#########################[ end read_recipe_api ]###############################


#########################[ start update_recipe_api ]############################
@bp.route("/update/<pk>", methods=["PUT"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.recipe_update_required
def update_recipe_api(pk: str) -> Dict:
    """Update an existing recipe."""
    name = "recipe.update_recipe_api"
    response_msg = "Failed to update recipe"
    json_data = request.json or {}
    json_data["recipe_id"] = pk
    try:
        data = UpdateRecipeSchema(**json_data)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    try:
        existing_model = RecipeRepository.get_recipe_by_id(str(data.recipe_id))
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    if not existing_model:
        return jsonify({"response": {"error": response_msg}})

    existing_recipe = Recipe(
        recipe_id=str(existing_model.recipe_id),
        recipe_name=existing_model.recipe_name,
        recipe_description=existing_model.recipe_description,
        recipe_category_id=str(existing_model.recipe_category_id),
        recipe_image_id=str(existing_model.recipe_image_id)
        if existing_model.recipe_image_id
        else "",
        recipe_author_id=str(existing_model.recipe_author_id),
    )

    if existing_recipe.recipe_author_id != str(getattr(g.user, "user_id", "")):
        return RecipezErrorUtils.handle_api_error(
            name,
            request,
            "User is not recipe author",
            "You do not have permission to update this recipe",
        )

    try:
        updated = RecipeRepository.update_recipe(
            str(data.recipe_id),
            data.recipe_name,
            data.recipe_description,
            str(data.recipe_category_id) if data.recipe_category_id else None,
            str(data.recipe_image_id) if data.recipe_image_id else None,
        )
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)
    if not updated:
        return jsonify({"response": {"error": response_msg}})
    return jsonify({"response": {"success": True}})


#########################[ end update_recipe_api ]##############################


#########################[ start delete_recipe_api ]############################
@bp.route("/delete/<pk>", methods=["DELETE"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.recipe_delete_required
def delete_recipe_api(pk: str) -> Dict:
    """Delete a recipe."""
    name = "recipe.delete_recipe_api"
    response_msg = "Failed to delete recipe"

    try:
        data = DeleteRecipeSchema(recipe_id=UUID(pk))
    except Exception as e:
        recipe_error = "Invalid recipe id."
        return RecipezErrorUtils.handle_api_error(
            name, request, e, recipe_error
        )

    try:
        existing_model = RecipeRepository.get_recipe_by_id(str(data.recipe_id))
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    if not existing_model:
        return jsonify({"response": {"error": response_msg}})

    existing_recipe = Recipe(
        recipe_id=str(existing_model.recipe_id),
        recipe_name=existing_model.recipe_name,
        recipe_description=existing_model.recipe_description,
        recipe_category_id=str(existing_model.recipe_category_id),
        recipe_image_id=str(existing_model.recipe_image_id)
        if existing_model.recipe_image_id
        else "",
        recipe_author_id=str(existing_model.recipe_author_id),
    )

    if existing_recipe.recipe_author_id != str(getattr(g.user, "user_id", "")):
        return RecipezErrorUtils.handle_api_error(
            name,
            request,
            "User is not recipe author",
            "You do not have permission to delete this recipe",
        )

    # Clean up associated image before deleting recipe
    # ImageRepository.delete_image() already protects default images
    if existing_recipe.recipe_image_id:
        try:
            ImageRepository.delete_image(existing_recipe.recipe_image_id)
        except Exception as e:
            # Log but don't fail - recipe deletion is primary operation
            import logging
            logging.warning(f"Failed to delete recipe image: {e}")

    try:
        deleted_recipe = RecipeRepository.delete_recipe(str(data.recipe_id))
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    if not deleted_recipe:
        return jsonify({"response": {"error": response_msg}})
    return jsonify({"response": {"success": True}})


#########################[ end delete_recipe_api ]##############################


#########################[ start batch_update_category_api ]########################
@bp.route("/batch-update-category", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.recipe_update_required
def batch_update_category_api() -> Dict:
    """
    Batch update categories for multiple recipes.

    Expects JSON body with:
    {
        "updates": [
            {"recipe_id": "uuid", "category_id": "uuid"},
            ...
        ]
    }

    Only updates recipes owned by the current user.
    """
    name = "recipe.batch_update_category_api"
    response_msg = "Failed to batch update recipe categories"

    try:
        data = request.json or {}
        updates = data.get("updates", [])

        if not updates:
            return jsonify({"response": {"error": "No updates provided"}}), 400

        user_id = str(getattr(g.user, "user_id", ""))
        results = {
            "updated": [],
            "failed": [],
        }

        for update in updates:
            recipe_id = update.get("recipe_id")
            category_id = update.get("category_id")

            if not recipe_id or not category_id:
                results["failed"].append({
                    "recipe_id": recipe_id,
                    "reason": "Missing recipe_id or category_id"
                })
                continue

            try:
                # Get the existing recipe
                existing_model = RecipeRepository.get_recipe_by_id(str(recipe_id))

                if not existing_model:
                    results["failed"].append({
                        "recipe_id": recipe_id,
                        "reason": "Recipe not found"
                    })
                    continue

                # Verify ownership
                if str(existing_model.recipe_author_id) != user_id:
                    results["failed"].append({
                        "recipe_id": recipe_id,
                        "reason": "You do not have permission to update this recipe"
                    })
                    continue

                # Verify category exists
                category = CategoryRepository.read_category_by_id(str(category_id))
                if not category:
                    results["failed"].append({
                        "recipe_id": recipe_id,
                        "reason": "Category not found"
                    })
                    continue

                # Update the recipe's category
                updated = RecipeRepository.update_recipe(
                    recipe_id=str(recipe_id),
                    category_id=str(category_id),
                )

                if updated:
                    results["updated"].append({
                        "recipe_id": recipe_id,
                        "recipe_name": existing_model.recipe_name,
                        "new_category_id": category_id,
                        "new_category_name": category.category_name,
                    })
                else:
                    results["failed"].append({
                        "recipe_id": recipe_id,
                        "reason": "Update failed"
                    })

            except Exception as e:
                results["failed"].append({
                    "recipe_id": recipe_id,
                    "reason": str(e)
                })

        return jsonify({
            "response": {
                "success": len(results["updated"]) > 0,
                "updated_count": len(results["updated"]),
                "failed_count": len(results["failed"]),
                "updated": results["updated"],
                "failed": results["failed"],
            }
        })

    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)


#########################[ end batch_update_category_api ]##########################
