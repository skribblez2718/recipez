import re
import json
from flask import current_app, flash, jsonify
from uuid import UUID
from typing import List, Dict, Any, Union
from wtforms import ValidationError

from recipez.utils.api import RecipezAPIUtils
from recipez.utils.error import RecipezErrorUtils
from recipez.schema import (
    CreateIngredientSchema,
    ReadIngredientSchema,
    UpdateIngredientSchema,
    DeleteIngredientSchema,
)


###################################[ start RecipezIngredientUtils ]###################################
class RecipezIngredientUtils:
    """
    A class to handle ingredient validation and insertion for the Recipez application.
    """

    #########################[ start create_ingredient ]#############################
    @staticmethod
    def create_ingredients(
        authorization: str,
        request: "Request",
        ingredients: List[Dict[str, str]],
        author_id: str,
        recipe_id: str,
    ) -> List[Dict[str, str]]:
        """
        Creates a new ingredient.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            author_id (str): The ID of the author.
            recipe_id (str): The ID of the recipe.
            ingredients (List[Dict[str, str]]): The ingredients to create.

        Returns:
            List[Dict[str, str]]: A list of ingredients.
        """
        name = f"ingredient.create_ingredient"
        response_msg = "An error occurred while creating the ingredient"
        request_json = {
            "ingredients": ingredients,
            "author_id": author_id,
            "recipe_id": recipe_id,
        }

        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/ingredient/create",
                json=request_json,
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            response = RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if response is None or (isinstance(response, dict) and "error" in response):
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        return response

    #########################[ end create_ingredient ]###############################

    #########################[ start read_ingredient_by_id ]#############################
    @staticmethod
    def read_ingredient_by_id(
        authorization: str, request: "Request", ingredient_id: str
    ) -> List[Dict[str, str]]:
        """
        Fetch a single ingredient from the API.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            ingredient_id (str): The ID of the ingredient to fetch.

        Returns:
            List[Dict[str, str]]: The ingredient data.
        """
        name = "ingredient.read_ingredient_by_id"
        response_msg = "An error occurred while fetching ingredients"

        try:
            data: ReadIngredientSchema = ReadIngredientSchema(
                **{"ingredient_id": UUID(ingredient_id)}
            )
        except Exception as e:
            ingredient_error = "Invalid ingredient id."
            return RecipezErrorUtils.handle_util_error(
                name, request, e, ingredient_error
            )

        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").get,
                path=f"/api/ingredient/{data.ingredient_id}",
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            response = RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if response is None or (isinstance(response, dict) and "error" in response):
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        return response

    #########################[ end read_ingredient_by_id ]###############################

    #########################[ start read_all_ingredients ]#############################
    @staticmethod
    def read_all_ingredients(
        authorization: str, request: "Request"
    ) -> List[Dict[str, str]]:
        """
        Fetches all ingredients from the API.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.

        Returns:
            List[Dict[str, str]]: A list of ingredients.
        """
        name = "ingredient.read_all_ingredients"
        response_msg = "An error occurred while fetching ingredients"
        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").get,
                path="/api/ingredient/all",
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            response = RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if response is None or (isinstance(response, dict) and "error" in response):
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        return response

    #########################[ end read_all_ingredients ]###############################

    #########################[ start update_ingredient ]#############################
    @staticmethod
    def update_ingredient(
        authorization: str, request: "Request", ingredient_id: str, ingredient_name: str
    ) -> List[Dict[str, str]]:
        """
        Updates an existing ingredient.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            ingredient_id (str): The ID of the ingredient to update.
            ingredient_name (str): The name of the ingredient to update.

        Returns:
            List[Dict[str, str]]: A list of ingredients.
        """
        name = "ingredient.update_ingredient"
        response_msg = "An error occurred while updating the ingredient"

        try:
            data: UpdateIngredientSchema = UpdateIngredientSchema(
                **{
                    "ingredient_name": ingredient_name,
                    "ingredient_id": UUID(ingredient_id),
                }
            )
        except Exception as e:
            ingredient_error = "Invalid ingredient name or id"
            return RecipezErrorUtils.handle_util_error(
                name, request, e, ingredient_error
            )

        ingredient_name = data.ingredient_name
        ingredient_id = data.ingredient_id
        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").put,
                path=f"/api/ingredient/update/{str(ingredient_id)}",
                json={
                    "ingredient_name": ingredient_name,
                },
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

    #########################[ end update_ingredient ]###############################

    #########################[ start delete_ingredient ]#############################
    @staticmethod
    def delete_ingredient(
        authorization: str, request: "Request", ingredient_id: str
    ) -> List[Dict[str, str]]:
        """
        Deletes an existing ingredient.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            ingredient_id (str): The ID of the ingredient to delete.

        Returns:
            List[Dict[str, str]]: A list of ingredients.
        """
        name = "ingredient.delete_ingredient"
        response_msg = "An error occurred while deleting the ingredient"

        try:
            data: DeleteIngredientSchema = DeleteIngredientSchema(
                **{"ingredient_id": UUID(ingredient_id)}
            )
        except Exception as e:
            ingredient_error = "Invalid ingredient id."
            return RecipezErrorUtils.handle_util_error(
                name, request, e, ingredient_error
            )

        ingredient_id = data.ingredient_id
        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").delete,
                path=f"/api/ingredient/delete/{str(ingredient_id)}",
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

    #########################[ end delete_ingredient ]###############################


###################################[ end RecipezIngredientUtils ]####################################
