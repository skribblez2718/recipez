from typing import Dict, List
from uuid import UUID
from flask import (
    Blueprint,
    g,
    jsonify,
    request,
)
from recipez.utils import RecipezAuthNUtils, RecipezAuthZUtils, RecipezErrorUtils
from recipez.repository import CategoryRepository
from recipez.schema import (
    CreateCategorySchema,
    ReadCategorySchema,
    UpdateCategorySchema,
    DeleteCategorySchema,
)
from recipez.extensions import csrf

bp = Blueprint("api/category", __name__, url_prefix="/api/category")


#########################[ start create_category_api ]######################
@bp.route("/create", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.category_create_required
def create_category_api() -> Dict[str, List[Dict[str, int]]]:
    """
    Creates a new category.

    Returns:
        A dictionary containing a list of categories if successful.
        If an error occurs, the dictionary will contain an error message.
    """
    name = f"category.{create_category_api.__name__}"
    response_msg = "An error occurred while creating the category"

    try:
        data: CreateCategorySchema = CreateCategorySchema(**request.json)
    except Exception as e:
        response_msg = "Invalid category format"
        return RecipezErrorUtils.handle_validation_error(name, request, e, response_msg)

    # Always use authenticated user's ID (never accept client-provided author_id)
    author_id = str(g.user.user_id)
    try:
        category = CategoryRepository.create_category(
            data.category_name, author_id
        )
    except ValueError as e:
        if "already exists" in str(e).lower():
            response_msg = "A category with this name already exists"
            return RecipezErrorUtils.handle_conflict_error(name, request, e, response_msg)
        response_msg = "Invalid category data"
        return RecipezErrorUtils.handle_validation_error(name, request, e, response_msg)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    return jsonify(
        {
            "response": {
                "category": category.as_dict(),
            }
        }
    )


#########################[ end create_category_api ]########################


#########################[ start read_category_api ]######################
@bp.route("/<pk>", methods=["GET"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.category_read_required
def read_category_api(pk: str):
    name = f"category.{read_category_api.__name__}"

    try:
        data: ReadCategorySchema = ReadCategorySchema(**{"category_id": UUID(pk)})
    except Exception as e:
        return RecipezErrorUtils.handle_validation_error(
            name, request, e, "Invalid category ID format"
        )

    category_id = data.category_id
    try:
        category = CategoryRepository.read_category_by_id(category_id)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(
            name, request, e, "Unable to retrieve category"
        )

    if not category:
        return RecipezErrorUtils.handle_not_found_error(
            name, request, "Category not found"
        )

    return jsonify({"response": {"category": category.as_dict()}})


#########################[ end read_category_api ]########################


#########################[ start read_categories_api ]######################
@bp.route("/all", methods=["GET"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.category_read_required
def read_categories_api() -> Dict[str, List[Dict[str, int]]]:
    """
    Retrieves all categories from the database and returns them in JSON format.

    Returns:
        A dictionary containing a list of categories if successful.
        If an error occurs, the dictionary will contain an error message.
    """
    name = f"category.{read_categories_api.__name__}"
    response_msg = "An error occurred while fetching categories"

    all_categories = []
    try:
        categories = CategoryRepository.read_all_categories()
        for category in categories:
            if not category:
                all_categories.append(
                    {
                        "category_id": "",
                        "category_name": "",
                        "category_author_id": "",
                        "created_at": "",
                    }
                )
                continue
            all_categories.append(category.as_dict())
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    return jsonify({"response": all_categories})


#########################[ end read_categories_api ]########################


#########################[ start update_category_api ]######################
@bp.route("/update/<pk>", methods=["PUT"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.category_update_required
@RecipezAuthZUtils.owner_required
def update_category_api(pk: str) -> Dict[str, List[Dict[str, int]]]:
    """
    Updates an existing category.

    Returns:
        A dictionary containing a list of categories if successful.
        If an error occurs, the dictionary will contain an error message.
    """
    name = f"category.{update_category_api.__name__}"
    category_error = "An error occurred while updating the category"

    category_name = request.json.get("category_name")
    category_id = UUID(pk)
    try:
        data: UpdateCategorySchema = UpdateCategorySchema(
            **{"category_name": category_name, "category_id": category_id}
        )
    except Exception as e:
        category_error = "Invalid category name or id"
        return RecipezErrorUtils.handle_api_error(name, request, e, category_error)

    try:
        category_updated = CategoryRepository.update_category(
            data.category_id, data.category_name
        )
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, category_error)

    if not category_updated:
        return jsonify(
            {
                "response": {
                    "error": category_error,
                }
            }
        )

    return jsonify(
        {
            "response": {
                "category": category_updated.as_dict(),
                "success": "Category updated successfully",
            }
        }
    )


#########################[ end update_category_api ]########################


#########################[ start delete_category_preview_api ]######################
@bp.route("/delete/<pk>/preview", methods=["GET"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.scope_required("category:delete")
def delete_category_preview_api(pk: str) -> Dict[str, dict]:
    """
    Preview what would happen if a category is deleted.

    Returns information about whether the user can delete the category and
    lists their recipes that would need to be updated.

    Args:
        pk (str): The ID of the category to preview deletion for.

    Returns:
        Dict[str, dict]: A Flask JSON response with preview information.
    """
    name = f"category.delete_category_preview_api"

    try:
        data: DeleteCategorySchema = DeleteCategorySchema(**{"category_id": UUID(pk)})
    except Exception as e:
        category_error = "Invalid category id."
        return RecipezErrorUtils.handle_api_error(name, request, e, category_error)

    user_id = str(getattr(g.user, "user_id", ""))
    can_delete, reason = CategoryRepository.can_delete_category(str(data.category_id), user_id)

    # Get the user's recipes that use this category (so they can update them first)
    affected_recipes = CategoryRepository.get_user_recipes_by_category(str(data.category_id), user_id)

    return jsonify({
        "response": {
            "can_delete": can_delete,
            "reason": reason,
            "affected_recipes": affected_recipes,
            "affected_count": len(affected_recipes),
            "message": f"You have {len(affected_recipes)} recipe(s) using this category that will need to be updated" if affected_recipes else "No recipes of yours use this category"
        }
    })


#########################[ end delete_category_preview_api ]########################


#########################[ start delete_category_api ]######################
@bp.route("/delete/<pk>", methods=["DELETE"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.scope_required("category:delete")
def delete_category_api(pk: str) -> Dict[str, dict]:
    """
    Deletes a category by its ID.

    A category can only be deleted if:
    1. The user owns the category (is the author)
    2. No OTHER users' recipes are using this category

    Before deletion, the user's recipes using this category will be reassigned
    to the 'Uncategorized' category.

    Args:
        pk (str): The ID of the category to delete.

    Returns:
        Dict[str, dict]: A Flask JSON response with success or error message.
    """
    from recipez.repository import UserRepository
    from recipez.repository.recipe import RecipeRepository

    name = f"category.delete_category_api"
    response_msg = "Failed to delete category"

    try:
        data: DeleteCategorySchema = DeleteCategorySchema(**{"category_id": UUID(pk)})
    except Exception as e:
        category_error = "Invalid category id."
        return RecipezErrorUtils.handle_api_error(name, request, e, category_error)

    # Check if user can delete this category (owns it and no other users' recipes use it)
    user_id = str(getattr(g.user, "user_id", ""))
    can_delete, reason = CategoryRepository.can_delete_category(str(data.category_id), user_id)

    if not can_delete:
        return jsonify({"response": {"error": reason}}), 400

    # Get user's affected recipes before deletion
    affected_recipes = CategoryRepository.get_user_recipes_by_category(str(data.category_id), user_id)

    # Reassign user's recipes to 'Uncategorized' category before deletion
    if affected_recipes:
        system_user = UserRepository.get_system_user()
        uncategorized = CategoryRepository.get_or_create_uncategorized(str(system_user.user_id))

        for recipe_info in affected_recipes:
            RecipeRepository.update_recipe(
                recipe_id=recipe_info["recipe_id"],
                category_id=str(uncategorized.category_id),
            )

    try:
        deleted = CategoryRepository.delete_category(data.category_id)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    if not deleted:
        return jsonify(
            {
                "response": {
                    "error": response_msg,
                }
            }
        )

    return jsonify({
        "response": {
            "success": "Category deleted successfully",
            "recipes_reassigned": len(affected_recipes),
            "reassigned_to": "Uncategorized" if affected_recipes else None,
        }
    })


#########################[ end delete_category_api ]########################
