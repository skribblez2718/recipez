import re
import json
from flask import current_app, flash, jsonify
from uuid import UUID
from typing import List, Dict, Union
from wtforms import ValidationError

from recipez.utils.api import RecipezAPIUtils
from recipez.utils.error import RecipezErrorUtils
from recipez.schema import (
    ReadCategorySchema,
    UpdateCategorySchema,
    DeleteCategorySchema,
)


###################################[ start RecipezCategoryUtils ]###################################
class RecipezCategoryUtils:
    """
    A class to handle category validation and insertion for the Recipez application.
    """

    #########################[ start create_category ]#############################
    @staticmethod
    def create_category(
        authorization: str, request: "Request", category_name: str
    ) -> List[Dict[str, str]]:
        """
        Creates a new category.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            category_name (str): The name of the category.

        Returns:
            List[Dict[str, str]]: A list of categories.
        """
        name = f"category.create_category"
        response_msg = "An error occurred while creating the category"

        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/category/create",
                json={
                    "category_name": category_name,
                },
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            response = RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if response is None or (isinstance(response, dict) and "error" in response):
            error_msg = response.get("error", response_msg)
            if "already exists" in error_msg.lower():
                response_msg = error_msg
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        return response

    #########################[ end create_category ]###############################

    #########################[ start read_category_by_id ]#############################
    @staticmethod
    def read_category_by_id(
        authorization: str, request: "Request", category_id: str
    ) -> List[Dict[str, str]]:
        """
        Fetches all categories from the API.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            category_id (UUID): The ID of the category to fetch.

        Returns:
            List[Dict[str, str]]: A list of categories.
        """
        name = f"category.read_category_by_id"
        response_msg = "An error occurred while fetching categories"

        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").get,
                path=f"/api/category/{category_id}",
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

    #########################[ end read_category_by_id ]###############################

    #########################[ start read_all_categories ]#############################
    @staticmethod
    def read_all_categories(
        authorization: str, request: "Request"
    ) -> List[Dict[str, str]]:
        """
        Fetches all categories from the API.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.

        Returns:
            List[Dict[str, str]]: A list of categories.
        """
        name = f"category.read_all_categories"
        response_msg = "An error occurred while fetching categories"
        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").get,
                path="/api/category/all",
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

    #########################[ end read_all_categories ]###############################

    #########################[ start update_category ]#############################
    @staticmethod
    def update_category(
        authorization: str, request: "Request", category_id: str, category_name: str
    ) -> List[Dict[str, str]]:
        """
        Updates an existing category.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            category_id (str): The ID of the category to update.
            category_name (str): The name of the category to update.

        Returns:
            List[Dict[str, str]]: A list of categories.
        """
        name = f"category.update_category"
        response_msg = "An error occurred while updating the category"

        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").put,
                path=f"/api/category/update/{category_id}",
                json={
                    "category_name": category_name,
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

    #########################[ end update_category ]###############################

    #########################[ start delete_category ]#############################
    @staticmethod
    def delete_category(
        authorization: str, request: "Request", category_id: str
    ) -> List[Dict[str, str]]:
        """
        Deletes an existing category.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            category_id (str): The ID of the category to delete.

        Returns:
            List[Dict[str, str]]: A list of categories.
        """
        name = f"category.delete_category"
        response_msg = "An error occurred while deleting the category"

        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").delete,
                path=f"/api/category/delete/{category_id}",
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

    #########################[ end delete_category ]###############################

    #########################[ start validate_number_or_fraction ]###################################
    def validate_number_or_fraction(form, field) -> None:
        """
        Validates that the input is a valid integer, decimal, fraction, or range of these.

        Parameters:
        form (Form): The form containing the field to be validated.
        field (Field): The field to be validated.

        Raises:
        ValidationError: If the input does not match any of the allowed patterns.
        """
        value = field.data.strip()

        integer_regex = r"^\d+( ?- ?\d+)?$"
        decimal_pattern = r"^\d?+\.\d+( ?- ?\d?+\.\d+)?$"
        fraction_regex = r"^(\d+ )?(\d+/\d+)?( ?- ?(\d+ ?)?\d+/\d+)?$"

        if (
            (not re.match(integer_regex, value))
            and (not re.match(decimal_pattern, value))
            and (not re.match(fraction_regex, value))
        ):
            raise ValidationError(
                "Quantity must be an integer, decimal or fraction, or a range of integers, decimals or fractions"
            )

    #########################[ end validate_number_or_fraction ]#####################################

    #########################[ start validate_measurement ]###################################
    def validate_measurement(form, field) -> None:
        """
        Validates that the measurement is one of the allowed measurements.

        Parameters:
        form (Form): The form containing the field to be validated.
        field (Field): The field to be validated.

        Raises:
        ValidationError: If the measurement is not in the list of allowed measurements.
        """
        allowed_measurements = current_app.config.get("RECIPEZ_ALLOWED_MEASUREMENTS")
        if field.data.lower() not in allowed_measurements:
            raise ValidationError(
                f"Invalid measurement. Allowed measurements are: {', '.join(allowed_measurements)}"
            )

    #########################[ end validate_measurement ]#####################################


###################################[ end RecipezCategoryUtils ]####################################
