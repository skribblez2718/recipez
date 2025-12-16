from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    request,
    session,
    url_for,
)
from uuid import UUID
from pathlib import Path

from recipez.utils import (
    RecipezAuthNUtils,
    RecipezAuthZUtils,
    RecipezCategoryUtils,
    RecipezImageUtils,
    RecipezRecipeUtils,
    RecipezIngredientUtils,
    RecipezStepUtils,
    RecipezResponseUtils,
    RecipezErrorUtils,
)
from recipez.form import (
    CreateRecipeForm,
    UpdateRecipeForm,
    CreateCategoryForm,
    DeleteRecipeForm,
    IngredientForm,
    StepForm,
)
from recipez.form.ai import AICreateRecipeForm, AIModifyRecipeForm

bp = Blueprint("recipe", __name__, url_prefix="/recipe")


#########################[ start create_recipe_view ]##################################
@bp.route("/create", methods=["GET", "POST"])
@RecipezAuthNUtils.login_required
@RecipezAuthZUtils.category_read_required
@RecipezAuthZUtils.image_create_required
@RecipezAuthZUtils.ingredient_create_required
@RecipezAuthZUtils.step_create_required
@RecipezAuthZUtils.recipe_create_required
def create_recipe_view():
    """
    Renders the recipe creation page for creating recipes

    Returns:
        str: The rendered HTML response.
    """

    name = f"recipe.{create_recipe_view.__name__}"
    recipe_error = "{method} returned an invalid response: {error_msg}"
    response_msg = ""
    script_nonce, link_nonce = RecipezResponseUtils.generate_nonces()
    template_params = {
        "template": "recipe/create_recipe.html",
        "script_nonce": script_nonce,
        "link_nonce": link_nonce,
        "js_modules": {"recipe": True},
        "recipe_form": CreateRecipeForm(),
        "category_form": CreateCategoryForm(),
        "ai_create_form": AICreateRecipeForm(),
        "ai_modify_form": AIModifyRecipeForm(),
        "recipes": [],  # For AI dropdown modify workflow
        "categories": [],  # For AI dropdown form generation (already fetched below)
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

    try:
        response = RecipezCategoryUtils.read_all_categories(
            session["user_jwt"], request
        )
    except Exception as e:
        response = RecipezErrorUtils.handle_api_error(name, request, e, recipe_error)

    if response is None or (isinstance(response, dict) and "error" in response):
        response_msg = "An error occurred while loading the categories"
        error_msg = response.get("error", response_msg)
        error = recipe_error.format(
            method="RecipezCategoryUtils.read_all_categories", error_msg=error_msg
        )
        return RecipezErrorUtils.handle_view_error(
            name, error, request, response_msg, **template_params
        )

    category_choices = [
        (category["category_id"], category["category_name"]) for category in response
    ]
    template_params["recipe_form"].category_selector.choices = category_choices
    template_params["categories"] = response  # For AI dropdown form generation
    category_id_to_name = {
        category_id: category_name for category_id, category_name in category_choices
    }

    if request.method == "POST":
        response_msg = "An error occured creating the recipe"
        create_category_form = template_params["category_form"]
        recipe_form = template_params["recipe_form"]

        # Attach category form to recipe form for validation (either/or logic)
        recipe_form.create_category_form = create_category_form

        # Handle new category creation: if user provided a new category name,
        # add a placeholder to choices so SelectField validation passes
        new_category_name = (
            create_category_form.name.data.strip()
            if create_category_form.name.data
            else ""
        )
        if new_category_name:
            # User is creating a new category - add placeholder choice and set it
            placeholder_id = "new-category-placeholder"
            recipe_form.category_selector.choices.append((placeholder_id, new_category_name))
            recipe_form.category_selector.data = placeholder_id
        elif (
            recipe_form.category_selector.data is None
            and category_id_to_name
        ):
            # No new category and no selection - default to first existing category
            recipe_form.category_selector.data = next(iter(category_id_to_name.keys()))

        authorization = session.get("user_jwt", "")
        created_recipe = {}

        if recipe_form.validate_on_submit():
            # Step 1: Create or get the recipe category
            response = RecipezRecipeUtils.create_recipe_category(
                authorization=authorization,
                request=request,
                category_name=(
                    create_category_form.name.data.strip()
                    if create_category_form.name.data
                    and create_category_form.name.data.strip()
                    else ""
                ),
                create_category_form=(
                    create_category_form
                    if create_category_form.name.data
                    and create_category_form.name.data.strip()
                    else recipe_form
                ),
            )

            if response is None or (isinstance(response, dict) and "error" in response):
                error_msg = response.get("error", "An internal error occurred")
                if "already exists" in error_msg.lower():
                    response_msg = error_msg
                error = recipe_error.format(
                    method="RecipezRecipeUtils.create_recipe_category",
                    error_msg=error_msg,
                )
                return RecipezErrorUtils.handle_view_error(
                    name, request, error, response_msg, **template_params
                )

            new_category_created = response.get("new_category_created", False)
            recipe_category = response.get("category", {})
            recipe_category_id = recipe_category.get("category_id", "")
            created_recipe["recipe_category"] = recipe_category

            if new_category_created:
                recipe_category_name = recipe_category.get("category_name", "")
                flash(
                    f"Category '{recipe_category_name}' created successfully", "success"
                )

            # Step 2: Create the recipe image
            response = RecipezRecipeUtils.create_recipe_image(
                authorization=authorization,
                request=request,
                image_data=recipe_form.image.data if recipe_form.image.data else None,
            )

            if "error" in response:
                RecipezRecipeUtils.cleanup_recipe_category(
                    new_category_created, authorization, recipe_category_id, request
                )
                error = recipe_error.format(
                    method="RecipezRecipeUtils.create_recipe_image",
                    error_msg=response["error"],
                )
                return RecipezErrorUtils.handle_view_error(
                    name, request, error, response_msg, **template_params
                )

            new_image_created = response.get("new_image_created", False)
            recipe_image = response.get("image", {})
            recipe_image_id = recipe_image.get("image_id") or None
            created_recipe["recipe_image"] = recipe_image

            # Step 3: Create the recipe
            response = RecipezRecipeUtils.create_recipe_recipe(
                authorization=authorization,
                request=request,
                recipe_name=recipe_form.name.data.strip(),
                recipe_description=recipe_form.description.data.strip(),
                recipe_category_id=recipe_category_id,
                recipe_image_id=recipe_image_id,
            )

            if response is None or (isinstance(response, dict) and "error" in response):
                RecipezRecipeUtils.cleanup_recipe_category(
                    new_category_created, authorization, recipe_category_id, request
                )
                RecipezRecipeUtils.cleanup_recipe_image(
                    new_image_created, authorization, recipe_image_id, request
                )
                error_msg = response.get("error", response_msg)
                if "already exists" in error_msg.lower():
                    response_msg = error_msg
                error = recipe_error.format(
                    method="RecipezRecipeUtils.create_recipe_recipe",
                    error_msg=error_msg,
                )
                return RecipezErrorUtils.handle_view_error(
                    name, request, error, response_msg, **template_params
                )

            new_recipe_created = response.get("new_recipe_created", False)
            recipe = response.get("recipe", {})
            recipe_id = recipe.get("recipe_id", "")
            created_recipe = response.get("recipe", {})

            # Step 4: Create recipe ingredients
            response = RecipezRecipeUtils.create_recipe_ingredients(
                authorization=authorization,
                request=request,
                recipe_id=recipe_id,
                ingredient_forms=recipe_form.ingredients.entries,
            )

            if response is None or (isinstance(response, dict) and "error" in response):
                RecipezRecipeUtils.cleanup_recipe_category(
                    new_category_created, authorization, recipe_category_id, request
                )
                RecipezRecipeUtils.cleanup_recipe_image(
                    new_image_created, authorization, recipe_image_id, request
                )
                RecipezRecipeUtils.cleanup_recipe(
                    new_recipe_created, authorization, recipe_id, request
                )
                error = recipe_error.format(
                    method="RecipezRecipeUtils.create_recipe_ingredients",
                    error_msg=response.get("error", "An internal error occurred"),
                )
                return RecipezErrorUtils.handle_view_error(
                    name, request, error, response_msg, **template_params
                )

            new_ingredients_created = response.get("new_ingredients_created", False)
            recipe_ingredients = response.get("ingredients", {})
            created_recipe["recipe_ingredients"] = recipe_ingredients

            # Step 5: Create recipe steps
            response = RecipezRecipeUtils.create_recipe_steps(
                authorization=authorization,
                request=request,
                recipe_id=recipe_id,
                step_forms=recipe_form.steps.entries,
            )

            if response is None or (isinstance(response, dict) and "error" in response):
                RecipezRecipeUtils.cleanup_recipe_category(
                    new_category_created, authorization, recipe_category_id, request
                )
                RecipezRecipeUtils.cleanup_recipe_image(
                    new_image_created, authorization, recipe_image_id, request
                )
                RecipezRecipeUtils.cleanup_recipe(
                    new_recipe_created, authorization, recipe_id, request
                )
                RecipezRecipeUtils.cleanup_recipe_ingredients(
                    new_ingredients_created, authorization, recipe_ingredients, request
                )
                error = recipe_error.format(
                    method="RecipezRecipeUtils.create_recipe_steps",
                    error_msg=response.get("error", "An internal error occurred"),
                )
                return RecipezErrorUtils.handle_view_error(
                    name, request, error, response_msg, **template_params
                )

            flash(f"Recipe '{created_recipe.get('recipe_name', '')}' created successfully!", "success")
            return redirect(url_for("index.index"))
        else:
            template_params["form"] = recipe_form
            return RecipezErrorUtils.handle_view_error(
                name, request, "Recipe form failed validation", recipe_form.errors, **template_params
            )

    return RecipezResponseUtils.process_response(
        request,
        **template_params,
    )


#########################[ end create_recipe_view ]##################################


#########################[ start read_recipe_view ]##################################
@bp.route("/<pk>")
@RecipezAuthNUtils.login_required
@RecipezAuthZUtils.recipe_read_required
def read_recipe_view(pk: UUID):
    """
    Renders the recipe page by fetching the recipe asynchronously,
    processing it, and returning a response with appropriate headers.

    Args:
        pk (str): The primary key of the recipe.

    Returns:
        str: The rendered HTML response.
    """
    name = f"recipe.{read_recipe_view.__name__}"
    recipe_error = "{method} returned an invalid response: {error_msg}"
    response_message = "An error occurred while loading the recipe"
    script_nonce, link_nonce = RecipezResponseUtils.generate_nonces()
    delete_form = DeleteRecipeForm()
    template_params = {
        "template": "recipe/view_recipe.html",
        "script_nonce": script_nonce,
        "link_nonce": link_nonce,
        "js_modules": {"recipe": True, "share": True},
        "recipe": {},
        "delete_form": delete_form,
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

    try:
        response = RecipezRecipeUtils.read_recipe(session["user_jwt"], pk, request)
    except Exception as e:
        # Ensure minimal recipe data for template rendering on exception
        template_params["recipe"] = {"recipe_id": pk, "recipe_author_id": None}
        response = RecipezErrorUtils.handle_api_error(
            name, request, e, response_message
        )

    if response is None or (isinstance(response, dict) and "error" in response):
        error_msg = response.get("error", response_message)
        error = recipe_error.format(
            method="RecipezRecipeUtils.get_recipe", error_msg=error_msg
        )
        # Ensure recipe has minimal data for template rendering
        template_params["recipe"] = {"recipe_id": pk, "recipe_author_id": None}
        return RecipezErrorUtils.handle_view_error(
            name, error, request, **template_params
        )

    template_params["recipe"] = response

    return RecipezResponseUtils.process_response(
        request,
        **template_params,
    )


#########################[ end read_recipe_view ]##################################


#########################[ start update_recipe_view ]##################################
@bp.route("/update/<pk>", methods=["GET", "POST"])
@RecipezAuthNUtils.login_required
@RecipezAuthZUtils.category_read_required
@RecipezAuthZUtils.image_update_required
@RecipezAuthZUtils.ingredient_create_required
@RecipezAuthZUtils.ingredient_delete_required
@RecipezAuthZUtils.step_create_required
@RecipezAuthZUtils.step_delete_required
@RecipezAuthZUtils.recipe_update_required
def update_recipe_view(pk):
    """
    Update an existing recipe.

    Handles both GET and POST requests. For GET requests, this function populates
    the update form with the current recipe data. For POST requests, it validates
    and saves changes (including an optional updated image).
    """
    name = f"recipe.{update_recipe_view.__name__}"
    recipe_error = "{method} returned an invalid response: {error_msg}"
    response_msg = ""
    script_nonce, link_nonce = RecipezResponseUtils.generate_nonces()
    template_params = {
        "template": "recipe/update_recipe.html",
        "script_nonce": script_nonce,
        "link_nonce": link_nonce,
        "recipe_form": UpdateRecipeForm(),
        "category_form": CreateCategoryForm(),
        "js_modules": {"recipe": True},
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

    # Get the recipe to update
    try:
        response = RecipezRecipeUtils.read_recipe(session["user_jwt"], pk, request)
    except Exception as e:
        response = RecipezErrorUtils.handle_api_error(name, request, e, recipe_error)

    if response is None or (isinstance(response, dict) and "error" in response):
        response_msg = "An error occurred while loading the recipe"
        error_msg = response.get("error", response_msg)
        error = recipe_error.format(
            method="RecipezRecipeUtils.read_recipe", error_msg=error_msg
        )
        return RecipezErrorUtils.handle_view_error(
            name, request, error, response_msg, **template_params
        )

    # Check if the user is the recipe author
    existing_recipe = response
    # Add existing recipe to template params for error handling
    template_params["existing_recipe"] = existing_recipe

    if existing_recipe.get("recipe_author_id") != session.get("user_id"):
        flash("You can only edit your own recipes", "danger")
        return redirect(url_for("index.index"))
    
    # Get all categories for the dropdown
    try:
        response = RecipezCategoryUtils.read_all_categories(
            session["user_jwt"], request
        )
    except Exception as e:
        response = RecipezErrorUtils.handle_api_error(name, request, e, recipe_error)

    if response is None or (isinstance(response, dict) and "error" in response):
        response_msg = "An error occurred while loading the categories"
        error_msg = response.get("error", response_msg)
        error = recipe_error.format(
            method="RecipezCategoryUtils.read_all_categories", error_msg=error_msg
        )
        return RecipezErrorUtils.handle_view_error(
            name, request, error, response_msg, **template_params
        )

    category_choices = [
        (category["category_id"], category["category_name"]) for category in response
    ]
    template_params["recipe_form"].category_selector.choices = category_choices
    template_params["categories"] = response  # For AI dropdown form generation
    category_id_to_name = {
        category_id: category_name for category_id, category_name in category_choices
    }

    # Extract ingredients and steps from the existing_recipe data
    # The API already includes ingredients and steps in the recipe response
    ingredients_data = existing_recipe.get("recipe_ingredients", [])
    steps_data = existing_recipe.get("recipe_steps", [])
    
    
    
    
    if request.method == "POST":
        response_msg = "An error occurred updating the recipe"
        create_category_form = template_params["category_form"]
        recipe_form = template_params["recipe_form"]

        # Attach category form to recipe form for validation (either/or logic)
        recipe_form.create_category_form = create_category_form

        # Handle new category creation: if user provided a new category name,
        # add a placeholder to choices so SelectField validation passes
        new_category_name = (
            create_category_form.name.data.strip()
            if create_category_form.name.data
            else ""
        )
        if new_category_name:
            # User is creating a new category - add placeholder choice and set it
            placeholder_id = "new-category-placeholder"
            recipe_form.category_selector.choices.append((placeholder_id, new_category_name))
            recipe_form.category_selector.data = placeholder_id
        elif (
            recipe_form.category_selector.data is None
            and category_id_to_name
        ):
            # No new category and no selection - default to existing category
            recipe_form.category_selector.data = existing_recipe.get("recipe_category_id")

        authorization = session.get("user_jwt", "")

        if recipe_form.validate_on_submit():
            # Step 1: Update the recipe category
            response = RecipezRecipeUtils.update_recipe_category(
                authorization=authorization,
                request=request,
                recipe_id=pk,
                current_category_id=existing_recipe.get("recipe_category_id", ""),
                category_name=(
                    create_category_form.name.data.strip()
                    if create_category_form.name.data
                    and create_category_form.name.data.strip()
                    else ""
                ),
                create_category_form=(
                    create_category_form
                    if create_category_form.name.data
                    and create_category_form.name.data.strip()
                    else recipe_form
                ),
            )

            if response is None or (isinstance(response, dict) and "error" in response):
                error_msg = response.get("error", "An internal error occurred")
                if "already exists" in error_msg.lower():
                    response_msg = error_msg
                error = recipe_error.format(
                    method="RecipezRecipeUtils.update_recipe_category",
                    error_msg=error_msg,
                )
                return RecipezErrorUtils.handle_view_error(
                    name, request, error, response_msg, **template_params
                )

            new_category_created = response.get("new_category_created", False)
            recipe_category = response.get("category", {})

            if new_category_created:
                recipe_category_name = recipe_category.get("category_name", "")
                flash(
                    f"Category '{recipe_category_name}' created successfully", "success"
                )

            # Step 2: Update the recipe image
            response = RecipezRecipeUtils.update_recipe_image(
                authorization=authorization,
                request=request,
                recipe_id=pk,
                current_image_id=existing_recipe.get("recipe_image_id", ""),
                image_data=recipe_form.image.data if recipe_form.image.data else None,
            )

            if "error" in response:
                # Rollback category changes if a new category was created
                RecipezRecipeUtils.cleanup_recipe_category(
                    new_category_created, authorization, recipe_category.get("category_id", ""), request
                )
                error = recipe_error.format(
                    method="RecipezRecipeUtils.update_recipe_image",
                    error_msg=response["error"],
                )
                return RecipezErrorUtils.handle_view_error(
                    name, request, error, response_msg, **template_params
                )

            # Get the updated image info for the recipe update
            recipe_image = response.get("image", {})
            updated_image_id = recipe_image.get("image_id")

            # Ensure we always have a valid image ID (recipe_image_id is NOT NULL)
            final_image_id = updated_image_id if updated_image_id else existing_recipe.get("recipe_image_id")

            # If we still don't have an image ID, this is a data integrity issue
            if not final_image_id:
                error = "Recipe must have an associated image. Data integrity error."
                return RecipezErrorUtils.handle_view_error(
                    name, request, error, "Recipe update failed due to missing image", **template_params
                )

            # Step 3: Update the recipe details
            recipe_updates = {
                "recipe_name": recipe_form.name.data.strip(),
                "recipe_description": recipe_form.description.data.strip(),
            }

            # Include category_id update - use the category from step 1 or the selected category
            final_category_id = recipe_category.get("category_id")
            if not final_category_id:
                # If no new category was created, use the selected category from the form
                final_category_id = recipe_form.category_selector.data

            if final_category_id:
                recipe_updates["recipe_category_id"] = final_category_id

            # Include image_id update (always include to maintain NOT NULL constraint)
            recipe_updates["recipe_image_id"] = final_image_id
            
            response = RecipezRecipeUtils.update_recipe(
                authorization=authorization,
                request=request,
                recipe_id=pk,
                updates=recipe_updates
            )

            if response is None or (isinstance(response, dict) and "error" in response):
                # Rollback category changes if a new category was created
                RecipezRecipeUtils.cleanup_recipe_category(
                    new_category_created, authorization, recipe_category.get("category_id", ""), request
                )
                error_msg = response.get("error", response_msg)
                if "already exists" in error_msg.lower():
                    response_msg = error_msg
                error = recipe_error.format(
                    method="RecipezRecipeUtils.update_recipe",
                    error_msg=error_msg,
                )
                return RecipezErrorUtils.handle_view_error(
                    name, request, error, response_msg, **template_params
                )

            # Ensure clean database session state before proceeding to ingredients
            try:
                from recipez.extensions import sqla_db
                sqla_db.session.commit()
            except Exception:
                sqla_db.session.rollback()

            # Step 4: Update recipe ingredients
            response = RecipezRecipeUtils.update_recipe_ingredients(
                authorization=authorization,
                request=request,
                recipe_id=pk,
                current_ingredients=ingredients_data,
                ingredient_forms=recipe_form.ingredients.entries,
            )

            if response is None or (isinstance(response, dict) and "error" in response):
                # Rollback category changes if a new category was created
                RecipezRecipeUtils.cleanup_recipe_category(
                    new_category_created, authorization, recipe_category.get("category_id", ""), request
                )
                error = recipe_error.format(
                    method="RecipezRecipeUtils.update_recipe_ingredients",
                    error_msg=response.get("error", "An internal error occurred") if response else "An internal error occurred",
                )
                return RecipezErrorUtils.handle_view_error(
                    name, request, error, response_msg, **template_params
                )

            # Ensure clean database session state before proceeding to steps
            try:
                from recipez.extensions import sqla_db
                sqla_db.session.commit()
            except Exception:
                sqla_db.session.rollback()

            # Step 5: Update recipe steps
            response = RecipezRecipeUtils.update_recipe_steps(
                authorization=authorization,
                request=request,
                recipe_id=pk,
                current_steps=steps_data,
                step_forms=recipe_form.steps.entries,
            )

            if response is None or (isinstance(response, dict) and "error" in response):
                # Rollback category changes if a new category was created
                RecipezRecipeUtils.cleanup_recipe_category(
                    new_category_created, authorization, recipe_category.get("category_id", ""), request
                )
                error = recipe_error.format(
                    method="RecipezRecipeUtils.update_recipe_steps",
                    error_msg=response.get("error", "An internal error occurred") if response else "An internal error occurred",
                )
                return RecipezErrorUtils.handle_view_error(
                    name, request, error, response_msg, **template_params
                )

            flash(f"Recipe '{recipe_form.name.data.strip()}' updated successfully!", "success")
            return redirect(url_for("index.index"))
        else:
            template_params["recipe_form"] = recipe_form
            return RecipezErrorUtils.handle_view_error(
                name, request, "Recipe form failed validation", recipe_form.errors, **template_params
            )
    
    # For GET requests, prepopulate the form with existing recipe data
    recipe_form = template_params["recipe_form"]
    
    # Prepopulate ingredients using form data assignment after form creation
    if ingredients_data and len(ingredients_data) > 0:
        # Ensure we have the right number of ingredient forms
        while len(recipe_form.ingredients) < len(ingredients_data):
            recipe_form.ingredients.append_entry()
        while len(recipe_form.ingredients) > len(ingredients_data):
            recipe_form.ingredients.pop_entry()
            
        # Set data for each ingredient form
        for i, ingredient in enumerate(ingredients_data):
            if i < len(recipe_form.ingredients):
                recipe_form.ingredients[i].quantity.data = ingredient.get("ingredient_quantity", "")
                recipe_form.ingredients[i].measurement.data = ingredient.get("ingredient_measurement", "")
                recipe_form.ingredients[i].ingredient_name.data = ingredient.get("ingredient_name", "")
    else:
        # Ensure at least one empty ingredient form if no ingredients exist
        if len(recipe_form.ingredients) == 0:
            recipe_form.ingredients.append_entry()
    
    # Prepopulate steps using form data assignment after form creation
    if steps_data and len(steps_data) > 0:
        # Ensure we have the right number of step forms
        while len(recipe_form.steps) < len(steps_data):
            recipe_form.steps.append_entry()
        while len(recipe_form.steps) > len(steps_data):
            recipe_form.steps.pop_entry()
            
        # Set data for each step form
        for i, step in enumerate(steps_data):
            if i < len(recipe_form.steps):
                recipe_form.steps[i].step.data = step.get("step_text", "")
    else:
        # Ensure at least one empty step form if no steps exist
        if len(recipe_form.steps) == 0:
            recipe_form.steps.append_entry()
    
    # Set basic recipe data after populating sub-forms
    recipe_form.name.data = existing_recipe.get("recipe_name", "")
    recipe_form.description.data = existing_recipe.get("recipe_description", "")
    recipe_form.category_selector.data = existing_recipe.get("recipe_category_id", "")
    
    # Return the rendered template
    return RecipezResponseUtils.process_response(
        request,
        **template_params,
    )


#########################[ end update_recipe_view ]##################################


#########################[ start delete_recipe_view ]##################################
@bp.route("/delete/<pk>", methods=["POST"])
@RecipezAuthNUtils.login_required
def delete_recipe_view(pk):
    """
    Delete a recipe along with all its ingredients, steps, and associated image.
    Only the user who created the recipe can delete it.

    Uses Flask-WTF form validation for CSRF protection.

    :param pk: The primary key (ID) of the recipe to delete.
    :return: A redirect to the index page on success or error.
    """
    name = f"recipe.{delete_recipe_view.__name__}"

    # Instantiate delete form for CSRF validation
    delete_form = DeleteRecipeForm()

    # Validate CSRF token
    if not delete_form.validate_on_submit():
        flash("Failed to delete recipe: Invalid security token", "danger")
        return redirect(url_for("index.index"))

    try:
        response = RecipezRecipeUtils.delete_recipe(session["user_jwt"], request, pk)
    except Exception as e:
        response = RecipezErrorUtils.handle_api_error(
            name, request, e, "Failed to delete recipe"
        )

    if response is None or (isinstance(response, dict) and "error" in response):
        flash("Failed to delete recipe", "danger")
    else:
        flash("Recipe deleted", "success")
    return redirect(url_for("index.index"))


#########################[ end delete_recipe_view ]##################################
