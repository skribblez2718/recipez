from flask import current_app
from typing import (
    List,
    Dict,
    Union,
)

from recipez.utils.api import RecipezAPIUtils
from recipez.utils.error import RecipezErrorUtils
from recipez.utils.category import RecipezCategoryUtils
from recipez.utils.image import RecipezImageUtils
from recipez.utils.ingredient import RecipezIngredientUtils
from recipez.utils.step import RecipezStepUtils
from recipez.schema import (
    UpdateRecipeSchema,
    DeleteRecipeSchema,
)


###################################[ start RecipezRecipeUtils ]###################################
class RecipezRecipeUtils:
    """
    A class to handle recipe operations for the Recipez application.
    """

    #########################[ start create_recipe ]#############################
    @staticmethod
    def create_recipe(
        authorization: str, request: "Request", recipe: Dict[str, str]
    ) -> List[Dict[str, str]]:
        """
        Creates a new recipe.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            recipe (Dict[str, str]): The recipe to create.

        Returns:
            List[Dict[str, str]]: A list of recipes.
        """
        name = f"recipe.create_recipe"
        response_msg = "An error occurred while creating the recipe"

        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/recipe/create",
                authorization=authorization,
                request=request,
                json=recipe,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if response is None or (isinstance(response, dict) and "error" in response):
            error_msg = response.get("error", response_msg)
            if "already exists" in error_msg.lower():
                response_msg = error_msg
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        return response

    #########################[ end create_recipe ]###############################

    #########################[ start read_all_recipes ]#############################
    @staticmethod
    def read_all_recipes(
        authorization: str, request: "Request"
    ) -> List[Dict[str, str]]:
        """
        Fetches all recipes from the API.

        Args:
            request (Request): The request object.

        Returns:
            List[Dict[str, str]]: A list of recipes.
        """
        name = f"recipe.read_all_recipes"
        response_msg = "An error occurred while fetching recipes"
        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").get,
                path="/api/recipe/all",
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if response is None or (isinstance(response, dict) and "error" in response):
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        return response

    #########################[ end read_all_recipes ]###############################

    #########################[ start read_recipe ]#############################
    @staticmethod
    def read_recipe(authorization: str, pk: str, request: "Request") -> Dict[str, str]:
        """
        Fetches a single recipe from the API.

        Args:
            request (Request): The request object.

        Returns:
            Dict[str, str]: A single recipe.
        """
        name = f"recipe.read_recipe"
        recipe_error = "An error occurred while fetching recipes"
        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").get,
                path=f"/api/recipe/{pk}",
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, recipe_error)

        if response is None or (isinstance(response, dict) and "error" in response):
            error_msg = response.get("error", recipe_error)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, recipe_error
            )

        return response

    #########################[ end read_recipe ]###############################

    #########################[ start update_recipe ]#############################
    @staticmethod
    def update_recipe(
        authorization: str,
        request: "Request",
        recipe_id: str,
        updates: Dict[str, str],
    ) -> List[Dict[str, str]]:
        """Update an existing recipe via the API."""
        name = "recipe.update_recipe"
        response_msg = "An error occurred while updating the recipe"

        update_payload = {"recipe_id": recipe_id}
        update_payload.update(updates)
        try:
            data = UpdateRecipeSchema(**update_payload)
        except Exception as e:
            recipe_error = "Invalid recipe update data."
            return RecipezErrorUtils.handle_util_error(
                name, request, e, recipe_error
            )

        try:
            response = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").put,
                path=f"/api/recipe/update/{data.recipe_id}",
                json=data.model_dump(mode="json"),
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if response is None or (isinstance(response, dict) and "error" in response):
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        return response

    #########################[ end update_recipe ]###############################

    #########################[ start delete_recipe ]#############################
    @staticmethod
    def delete_recipe(
        authorization: str, request: "Request", recipe_id: str
    ) -> List[Dict[str, str]]:
        """Delete a recipe via the API."""
        name = "recipe.delete_recipe"
        response_msg = "An error occurred while deleting the recipe"
        try:
            data = DeleteRecipeSchema(recipe_id=recipe_id)
        except Exception as e:
            recipe_error = "Invalid recipe id."
            return RecipezErrorUtils.handle_util_error(
                name, request, e, recipe_error
            )

        try:
            response = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").delete,
                path=f"/api/recipe/delete/{data.recipe_id}",
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if response is None or (isinstance(response, dict) and "error" in response):
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        return response

    #########################[ end delete_recipe ]###############################

    #########################[ start create_recipe_category ]#########################
    @staticmethod
    def create_recipe_category(
        authorization: str,
        request: "Request",
        author_id: str,
        category_name: str,
        create_category_form=None,
    ) -> Dict[str, Union[bool, Dict[str, str]]]:
        """
        Creates a new recipe category if needed or retrieves an existing one.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            author_id (str): The ID of the author.
            category_name (str): The name of the category to create.
            create_category_form: The category form, if provided.

        Returns:
            Dict[str, Union[bool, Dict[str, str]]]: A dictionary containing:
                - new_category_created (bool): Whether a new category was created.
                - category (Dict[str, str]): The category object.
                - error (str, optional): Any error message if there was a problem.
        """
        name = "recipe.create_recipe_category"
        response_msg = "An error occurred creating the recipe category"
        result = {"new_category_created": False, "category": {}}

        if category_name:
            if create_category_form and not create_category_form.validate_on_submit():
                response_msg = "New category name must be between 2 and 50 characters and can only contain letters, numbers, underscores, hypens, and spaces"
                return RecipezErrorUtils.handle_util_error(
                    name, request, response_msg, response_msg
                )

            try:
                response = RecipezCategoryUtils.create_category(
                    authorization=authorization,
                    request=request,
                    author_id=author_id,
                    category_name=category_name,
                )
            except Exception as e:
                return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

            if response is None or (isinstance(response, dict) and "error" in response):
                error_msg = response.get("error", response_msg)
                if "already exists" in error_msg.lower():
                    response_msg = error_msg
                return RecipezErrorUtils.handle_util_error(
                    name, request, error_msg, response_msg
                )

            result["new_category_created"] = True
            result["category"] = response.get("category", {})
            return result
        else:
            try:
                if not create_category_form:
                    return result
                response = RecipezCategoryUtils.read_category_by_id(
                    authorization, request, create_category_form.category_selector.data
                )
            except Exception as e:
                return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

            if response is None or (isinstance(response, dict) and "error" in response):
                error_msg = response.get("error", response_msg)
                return RecipezErrorUtils.handle_util_error(
                    name, request, error_msg, response_msg
                )

            result["category"] = response.get("category", {})
            return result

    #########################[ end create_recipe_category ]#########################

    #########################[ start create_recipe_image ]#########################
    @staticmethod
    def create_recipe_image(
        authorization: str,
        request: "Request",
        author_id: str,
        image_data=None,
    ) -> Dict[str, Union[bool, Dict[str, str]]]:
        """
        Creates a new recipe image.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            author_id (str): The ID of the author.
            image_data: The image data, if provided.

        Returns:
            Dict[str, Union[bool, Dict[str, str]]]: A dictionary containing:
                - new_image_created (bool): Whether a new image was created.
                - image (Dict[str, str]): The image object.
                - error (str, optional): Any error message if there was a problem.
        """
        name = "recipe.create_recipe_image"
        response_msg = "An error occurred creating the recipe image"
        result = {"new_image_created": False, "image": {}}

        if not image_data:
            from pathlib import Path

            default_img_path = (
                Path(__file__).parent.parent / "static" / "img" / "default_recipe.png"
            )
            with open(default_img_path, "rb") as f:
                image_data = f.read()
            # Issue 8 (MEDIUM): Sanitized logging - removed sensitive author_id from logs
            current_app.logger.info("Using default recipe image")

        try:
            response = RecipezImageUtils.create_image(
                authorization=authorization,
                request=request,
                author_id=author_id,
                image_data=image_data,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if response is None or (isinstance(response, dict) and "error" in response):
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        result["new_image_created"] = True
        result["image"] = response.get("image", {})
        return result

    #########################[ end create_recipe_image ]#########################

    #########################[ start create_recipe_recipe ]#########################
    @staticmethod
    def create_recipe_recipe(
        authorization: str,
        request: "Request",
        recipe_name: str,
        recipe_description: str,
        recipe_category_id: str,
        recipe_image_id: str,
        recipe_author_id: str,
    ) -> Dict[str, Union[bool, Dict[str, str]]]:
        """
        Creates a new recipe.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            recipe_name (str): The name of the recipe.
            recipe_description (str): The description of the recipe.
            recipe_category_id (str): The ID of the category.
            recipe_image_id (str): The ID of the image.
            recipe_author_id (str): The ID of the author.

        Returns:
            Dict[str, Union[bool, Dict[str, str]]]: A dictionary containing:
                - new_recipe_created (bool): Whether a new recipe was created.
                - recipe (Dict[str, str]): The recipe object.
                - error (str, optional): Any error message if there was a problem.
        """
        name = "recipe.create_recipe_recipe"
        response_msg = "An error occurred creating the recipe"
        result = {"new_recipe_created": False, "recipe": {}}

        try:
            response = RecipezRecipeUtils.create_recipe(
                authorization=authorization,
                request=request,
                recipe={
                    "recipe_name": recipe_name,
                    "recipe_description": recipe_description,
                    "recipe_category_id": str(recipe_category_id),
                    "recipe_image_id": str(recipe_image_id) if recipe_image_id else None,
                    "recipe_author_id": str(recipe_author_id),
                },
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if response is None or (isinstance(response, dict) and "error" in response):
            error_msg = response.get("error", response_msg)
            if "already exists" in error_msg.lower():
                response_msg = error_msg
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        result["new_recipe_created"] = True
        recipe = response.get("recipe", {})
        result["recipe"] = recipe
        return result

    #########################[ end create_recipe_recipe ]#########################

    #########################[ start create_recipe_ingredients ]#########################
    @staticmethod
    def create_recipe_ingredients(
        authorization: str,
        request: "Request",
        author_id: str,
        recipe_id: str,
        ingredient_forms,
    ) -> Dict[str, Union[bool, List[Dict[str, str]]]]:
        """
        Creates recipe ingredients.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            author_id (str): The ID of the author.
            recipe_id (str): The ID of the recipe.
            ingredient_forms: The ingredient form entries.

        Returns:
            Dict[str, Union[bool, List[Dict[str, str]]]]: A dictionary containing:
                - new_ingredients_created (bool): Whether new ingredients were created.
                - ingredients (List[Dict[str, str]]): The ingredients objects.
                - error (str, optional): Any error message if there was a problem.
        """
        name = "recipe.create_recipe_ingredients"
        response_msg = "An error occurred creating the recipe ingredients"
        result = {"new_ingredients_created": False, "ingredients": []}

        recipe_ingredients = []
        for ingredient_form in ingredient_forms:
            ingredient = {
                "ingredient_quantity": ingredient_form.quantity.data.strip(),
                "ingredient_measurement": ingredient_form.measurement.data,
                "ingredient_name": ingredient_form.ingredient_name.data.strip(),
            }
            recipe_ingredients.append(ingredient)

        try:
            response = RecipezIngredientUtils.create_ingredients(
                authorization=authorization,
                request=request,
                ingredients=recipe_ingredients,
                author_id=author_id,
                recipe_id=recipe_id,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if response is None or (isinstance(response, dict) and "error" in response):
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        result["new_ingredients_created"] = True
        result["ingredients"] = response.get("ingredients", [])
        return result

    #########################[ end create_recipe_ingredients ]#########################

    #########################[ start create_recipe_steps ]#########################
    @staticmethod
    def create_recipe_steps(
        authorization: str,
        request: "Request",
        author_id: str,
        recipe_id: str,
        step_forms,
    ) -> Dict[str, Union[bool, List[Dict[str, str]]]]:
        """
        Creates recipe steps.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            author_id (str): The ID of the author.
            recipe_id (str): The ID of the recipe.
            step_forms: The step form entries.

        Returns:
            Dict[str, Union[bool, List[Dict[str, str]]]]: A dictionary containing:
                - new_steps_created (bool): Whether new steps were created.
                - steps (List[Dict[str, str]]): The steps objects.
                - error (str, optional): Any error message if there was a problem.
        """
        name = "recipe.create_recipe_steps"
        response_msg = "An error occurred creating the recipe steps"
        result = {"new_steps_created": False, "steps": []}

        recipe_steps = []
        for step_form in step_forms:
            step = {
                "step_description": step_form.step.data.strip(),
            }
            recipe_steps.append(step)

        try:
            response = RecipezStepUtils.create_steps(
                authorization=authorization,
                request=request,
                steps=recipe_steps,
                author_id=author_id,
                recipe_id=recipe_id,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if response is None or (isinstance(response, dict) and "error" in response):
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        result["new_steps_created"] = True
        result["steps"] = response.get("steps", [])
        return result

    #########################[ end create_recipe_steps ]#########################

    #########################[ start cleanup_recipe_category ]#########################
    @staticmethod
    def cleanup_recipe_category(
        new_category_created: bool,
        authorization: str,
        category_id: str,
        request: "Request",
    ) -> None:
        """
        Cleans up the recipe category if the category was created and other failure occurs.

        Args:
            new_category_created (bool): Whether a new category was created.
            authorization (str): The authorization token.
            category_id (str): The ID of the category to delete.
            request (Request): The request object.
        """
        if new_category_created:
            RecipezCategoryUtils.delete_category(
                authorization=authorization,
                request=request,
                category_id=str(category_id),
            )

    #########################[ end cleanup_recipe_category ]#########################

    #########################[ start cleanup_recipe_image ]#########################
    @staticmethod
    def cleanup_recipe_image(
        new_image_created: bool, authorization: str, image_id: str, request: "Request"
    ) -> None:
        """
        Cleans up the recipe image if the image was created and other failure occurs.

        Args:
            new_image_created (bool): Whether a new image was created.
            authorization (str): The authorization token.
            image_id (str): The ID of the image to delete.
            request (Request): The request object.
        """
        if new_image_created:
            RecipezImageUtils.delete_image(
                authorization=authorization,
                request=request,
                image_id=str(image_id),
            )

    #########################[ end cleanup_recipe_image ]#########################

    #########################[ start cleanup_recipe ]#########################
    @staticmethod
    def cleanup_recipe(
        new_recipe_created: bool, authorization: str, recipe_id: str, request: "Request"
    ) -> None:
        """
        Cleans up the recipe if the recipe was created and other failure occurs.

        Args:
            new_recipe_created (bool): Whether a new recipe was created.
            authorization (str): The authorization token.
            recipe_id (str): The ID of the recipe to delete.
            request (Request): The request object.
        """
        if new_recipe_created:
            RecipezRecipeUtils.delete_recipe(
                authorization=authorization,
                request=request,
                recipe_id=str(recipe_id),
            )

    #########################[ end cleanup_recipe ]#########################

    #########################[ start cleanup_recipe_ingredients ]#########################
    @staticmethod
    def cleanup_recipe_ingredients(
        new_ingredients_created: bool,
        authorization: str,
        recipe_ingredients: List[Dict[str, str]],
        request: "Request",
    ) -> None:
        """
        Cleans up the recipe if the recipe was created and other failure occurs.

        Args:
            new_ingredients_created (bool): Whether new ingredients were created.
            authorization (str): The authorization token.
            recipe_ingredients (List[Dict[str, str]]): The ingredients to delete.
            request (Request): The request object.
        """
        if new_ingredients_created:
            for ingredient in recipe_ingredients:
                ingredient_id = ingredient.get("ingredient_id", "")
                RecipezIngredientUtils.delete_ingredient(
                    authorization=authorization,
                    request=request,
                    ingredient_id=str(ingredient_id),
                )

    #########################[ end cleanup_recipe_ingredients ]#########################

    #########################[ start update_recipe_category ]#########################
    @staticmethod
    def update_recipe_category(
        authorization: str,
        request: "Request",
        recipe_id: str,
        current_category_id: str,
        category_name: str,
        create_category_form=None,
    ) -> Dict[str, Union[bool, Dict[str, str]]]:
        """
        Updates a recipe category if needed or keeps the existing one.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            recipe_id (str): The ID of the recipe.
            current_category_id (str): The current category ID of the recipe.
            category_name (str): The new category name if creating a new category.
            create_category_form: The category form, if provided.

        Returns:
            Dict[str, Union[bool, Dict[str, str]]]: A dictionary containing:
                - new_category_created (bool): Whether a new category was created.
                - category (Dict[str, str]): The category object.
                - error (str, optional): Any error message if there was a problem.
        """
        name = "recipe.update_recipe_category"
        response_msg = "An error occurred updating the recipe category"
        result = {"new_category_created": False, "category": {}}

        if category_name:  # Create a new category
            if create_category_form and not create_category_form.validate_on_submit():
                response_msg = "New category name must be between 2 and 50 characters and can only contain letters, numbers, underscores, hypens, and spaces"
                return RecipezErrorUtils.handle_util_error(
                    name, request, response_msg, response_msg
                )

            from flask import session
            try:
                response = RecipezCategoryUtils.create_category(
                    authorization=authorization,
                    request=request,
                    author_id=session.get("user_id", ""),
                    category_name=category_name,
                )
            except Exception as e:
                return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

            if response is None or (isinstance(response, dict) and "error" in response):
                error_msg = response.get("error", response_msg)
                if "already exists" in error_msg.lower():
                    response_msg = error_msg
                return RecipezErrorUtils.handle_util_error(
                    name, request, error_msg, response_msg
                )

            result["new_category_created"] = True
            result["category"] = response.get("category", {})
            return result
        else:  # Use existing category from dropdown
            try:
                if not create_category_form:
                    return result
                selected_category_id = create_category_form.category_selector.data
                
                response = RecipezCategoryUtils.read_category_by_id(
                    authorization, request, create_category_form.category_selector.data
                )
            except Exception as e:
                return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

            if response is None or (isinstance(response, dict) and "error" in response):
                error_msg = response.get("error", response_msg)
                return RecipezErrorUtils.handle_util_error(
                    name, request, error_msg, response_msg
                )

            result["category"] = response.get("category", {})
            return result

    #########################[ end update_recipe_category ]#########################

    #########################[ start update_recipe_image ]#########################
    @staticmethod
    def update_recipe_image(
        authorization: str,
        request: "Request",
        recipe_id: str,
        current_image_id: str,
        image_data=None,
    ) -> Dict[str, Union[bool, Dict[str, str]]]:
        """
        Updates a recipe image if new image data is provided, otherwise keeps the existing one.
        Properly cleans up old image files and database records when updating.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            recipe_id (str): The ID of the recipe.
            current_image_id (str): The current image ID of the recipe.
            image_data: The new image data, if provided.

        Returns:
            Dict[str, Union[bool, Dict[str, str]]]: A dictionary containing:
                - image_updated (bool): Whether the image was updated.
                - image (Dict[str, str]): The image object.
                - error (str, optional): Any error message if there was a problem.
        """
        name = "recipe.update_recipe_image"
        response_msg = "An error occurred updating the recipe image"
        result = {"image_updated": False, "image": {}}

        # If no new image data provided, return current image info
        if not image_data:
            result["image"] = {"image_id": current_image_id}
            return result

        # Store old image info for cleanup after successful update
        old_image_id = current_image_id
        old_image_url = None
        if old_image_id:
            from recipez.repository.image import ImageRepository
            old_image = ImageRepository.read_image_by_id(old_image_id)
            if old_image:
                old_image_url = old_image.image_url

        # Create new image
        from flask import session
        try:
            response = RecipezImageUtils.create_image(
                authorization=authorization,
                request=request,
                author_id=session.get("user_id", ""),
                image_data=image_data,
            )
        except Exception as e:
            RecipezErrorUtils.log_error(name, e, request)
            return {"error": response_msg}

        # Check if response is a Flask Response object (error case)
        if hasattr(response, 'status_code'):
            RecipezErrorUtils.log_error(name, "Image creation failed", request)
            return {"error": response_msg}

        if response is None or (isinstance(response, dict) and "error" in response):
            error_msg = response.get("error", response_msg) if response else response_msg
            RecipezErrorUtils.log_error(name, error_msg, request)
            return {"error": response_msg}

        # New image created successfully, now clean up old image
        if old_image_id and old_image_url:
            try:
                # Delete old image from database
                from recipez.repository.image import ImageRepository
                ImageRepository.delete_image(old_image_id)

                # Delete old image file from filesystem
                import os
                from flask import current_app
                file_path = os.path.join(current_app.static_folder, 'uploads', os.path.basename(old_image_url))
                if os.path.exists(file_path):
                    os.remove(file_path)

            except Exception as e:
                # Log cleanup error but don't fail the update
                RecipezErrorUtils.log_error(name, f"Failed to clean up old image: {str(e)}", request)

        result["image_updated"] = True
        result["image"] = response.get("image", {})
        return result

    #########################[ end update_recipe_image ]#########################

    #########################[ start update_recipe_ingredients ]#########################
    @staticmethod
    def update_recipe_ingredients(
        authorization: str,
        request: "Request",
        recipe_id: str,
        current_ingredients: List[Dict[str, str]],
        ingredient_forms,
    ) -> Dict[str, Union[bool, List[Dict[str, str]]]]:
        """
        Updates recipe ingredients by intelligently updating existing ingredients,
        adding new ones, and removing deleted ones (instead of delete-all-recreate).

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            recipe_id (str): The ID of the recipe.
            current_ingredients (List[Dict[str, str]]): The existing ingredients.
            ingredient_forms: The ingredient form entries for new ingredients.

        Returns:
            Dict[str, Union[bool, List[Dict[str, str]]]]: A dictionary containing:
                - ingredients_updated (bool): Whether ingredients were updated.
                - ingredients (List[Dict[str, str]]): The updated ingredients objects.
                - error (str, optional): Any error message if there was a problem.
        """
        name = "recipe.update_recipe_ingredients"
        response_msg = "An error occurred updating the recipe ingredients"
        result = {"ingredients_updated": False, "ingredients": []}

        try:
            from flask import session
            from recipez.repository.ingredient import IngredientRepository

            # Create a mapping of existing ingredients by their index/position
            existing_ingredients_map = {i: ing for i, ing in enumerate(current_ingredients)}

            updated_ingredients = []

            # Process each form ingredient
            for i, ingredient_form in enumerate(ingredient_forms):
                ingredient_data = {
                    "ingredient_quantity": ingredient_form.quantity.data.strip(),
                    "ingredient_measurement": ingredient_form.measurement.data,
                    "ingredient_name": ingredient_form.ingredient_name.data.strip(),
                }

                # Check if we have an existing ingredient at this position
                if i < len(current_ingredients):
                    existing_ingredient = current_ingredients[i]
                    ingredient_id = existing_ingredient.get("ingredient_id")

                    # Check if the ingredient has actually changed
                    has_changed = (
                        existing_ingredient.get("ingredient_quantity") != ingredient_data["ingredient_quantity"] or
                        existing_ingredient.get("ingredient_measurement") != ingredient_data["ingredient_measurement"] or
                        existing_ingredient.get("ingredient_name") != ingredient_data["ingredient_name"]
                    )

                    if has_changed:
                        # Update existing ingredient
                        update_success = IngredientRepository.update_ingredient(
                            ingredient_id,
                            quantity=ingredient_data["ingredient_quantity"],
                            measurement=ingredient_data["ingredient_measurement"],
                            name=ingredient_data["ingredient_name"]
                        )

                        if update_success:
                            # Get the updated ingredient
                            updated_ingredient = IngredientRepository.read_ingredient_by_id(ingredient_id)
                            if updated_ingredient:
                                updated_ingredients.append(updated_ingredient.as_dict())
                        else:
                            return RecipezErrorUtils.handle_util_error(
                                name, request, f"Failed to update ingredient {ingredient_id}", response_msg
                            )
                    else:
                        # No change, keep existing ingredient
                        updated_ingredients.append(existing_ingredient)

                else:
                    # New ingredient - create it
                    create_response = RecipezIngredientUtils.create_ingredients(
                        authorization=authorization,
                        request=request,
                        ingredients=[ingredient_data],
                        author_id=session.get("user_id", ""),
                        recipe_id=recipe_id,
                    )

                    if create_response and "ingredients" in create_response:
                        updated_ingredients.extend(create_response["ingredients"])
                    else:
                        return RecipezErrorUtils.handle_util_error(
                            name, request, "Failed to create new ingredient", response_msg
                        )

            # Remove any ingredients that were deleted (existed before but not in forms now)
            if len(current_ingredients) > len(ingredient_forms):
                for i in range(len(ingredient_forms), len(current_ingredients)):
                    ingredient_to_delete = current_ingredients[i]
                    ingredient_id = ingredient_to_delete.get("ingredient_id")

                    delete_response = RecipezIngredientUtils.delete_ingredient(
                        authorization=authorization,
                        request=request,
                        ingredient_id=str(ingredient_id),
                    )

                    if not delete_response or "error" in delete_response:
                        return RecipezErrorUtils.handle_util_error(
                            name, request, f"Failed to delete ingredient {ingredient_id}", response_msg
                        )

        except Exception as e:
            # Rollback the session on any database error
            from recipez.extensions import sqla_db
            sqla_db.session.rollback()
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        result["ingredients_updated"] = True
        result["ingredients"] = updated_ingredients
        return result

    #########################[ end update_recipe_ingredients ]#########################

    #########################[ start update_recipe_steps ]#########################
    @staticmethod
    def update_recipe_steps(
        authorization: str,
        request: "Request",
        recipe_id: str,
        current_steps: List[Dict[str, str]],
        step_forms,
    ) -> Dict[str, Union[bool, List[Dict[str, str]]]]:
        """
        Updates recipe steps by intelligently updating existing steps,
        adding new ones, and removing deleted ones (instead of delete-all-recreate).

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            recipe_id (str): The ID of the recipe.
            current_steps (List[Dict[str, str]]): The existing steps.
            step_forms: The step form entries for new steps.

        Returns:
            Dict[str, Union[bool, List[Dict[str, str]]]]: A dictionary containing:
                - steps_updated (bool): Whether steps were updated.
                - steps (List[Dict[str, str]]): The updated steps objects.
                - error (str, optional): Any error message if there was a problem.
        """
        name = "recipe.update_recipe_steps"
        response_msg = "An error occurred updating the recipe steps"
        result = {"steps_updated": False, "steps": []}

        try:
            from flask import session
            from recipez.repository.step import StepRepository

            updated_steps = []

            # Process each form step
            for i, step_form in enumerate(step_forms):
                step_text = step_form.step.data.strip()

                # Check if we have an existing step at this position
                if i < len(current_steps):
                    existing_step = current_steps[i]
                    step_id = existing_step.get("step_id")

                    # Check if the step has actually changed
                    existing_step_text = existing_step.get("step_text", "")
                    has_changed = existing_step_text != step_text

                    if has_changed:
                        # Update existing step
                        update_success = StepRepository.update_step(step_id, step_text)

                        if update_success:
                            # Get the updated step
                            updated_step = StepRepository.read_step_by_id(step_id)
                            if updated_step:
                                updated_steps.append(updated_step.as_dict())
                        else:
                            return RecipezErrorUtils.handle_util_error(
                                name, request, f"Failed to update step {step_id}", response_msg
                            )
                    else:
                        # No change, keep existing step
                        updated_steps.append(existing_step)

                else:
                    # New step - create it
                    step_data = {"step_description": step_text}

                    create_response = RecipezStepUtils.create_steps(
                        authorization=authorization,
                        request=request,
                        steps=[step_data],
                        author_id=session.get("user_id", ""),
                        recipe_id=recipe_id,
                    )

                    if create_response and "steps" in create_response:
                        updated_steps.extend(create_response["steps"])
                    else:
                        return RecipezErrorUtils.handle_util_error(
                            name, request, "Failed to create new step", response_msg
                        )

            # Remove any steps that were deleted (existed before but not in forms now)
            if len(current_steps) > len(step_forms):
                for i in range(len(step_forms), len(current_steps)):
                    step_to_delete = current_steps[i]
                    step_id = step_to_delete.get("step_id")

                    delete_response = RecipezStepUtils.delete_step(
                        authorization=authorization,
                        request=request,
                        step_id=str(step_id),
                    )

                    if not delete_response or "error" in delete_response:
                        return RecipezErrorUtils.handle_util_error(
                            name, request, f"Failed to delete step {step_id}", response_msg
                        )

        except Exception as e:
            # Rollback the session on any database error
            from recipez.extensions import sqla_db
            sqla_db.session.rollback()
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        result["steps_updated"] = True
        result["steps"] = updated_steps
        return result

    #########################[ end update_recipe_steps ]#########################

###################################[ end RecipezRecipeUtils ]###################################
