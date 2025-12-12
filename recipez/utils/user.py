from typing import Tuple, Dict
from flask import (
    current_app,
    g,
)

from recipez.utils.api import RecipezAPIUtils
from recipez.utils.error import RecipezErrorUtils
from recipez.utils.secret import RecipezSecretsUtils


###################################[ start RecipezUserUtils ]###################################
class RecipezUserUtils:
    """
    User management utilities.
    """

    #########################[ start create_user ]######################
    @staticmethod
    def create_user(authorization: str, email: str, request: "Request") -> str:
        """
        Creates a new user in the database.

        Args:
            authorization (str): Authorization token.
            email (str): Email address of the new user.
            request (Request): Flask request object.

        Returns:
            str: JSON response from the API.
        """
        name = f"user.create_user"
        response_msg = "An error occurred while creating the user"
        try:
            return RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/user/create",
                authorization=authorization,
                json={
                    "email": email,
                },
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

    #########################[ end create_user ]########################

    #########################[ start read_user_by_email ]######################
    @staticmethod
    def read_user_by_email(authorization: str, email: str, request: "Request") -> str:
        """
        Retrieves a user by email address.

        Args:
            authorization (str): Authorization token.
            email (str): Email address of the user.
            request (Request): Flask request object.

        Returns:
            str: JSON response from the API.
        """
        name = f"user.read_user_by_email"
        response_msg = "An error occurred while retrieving the user"
        try:
            return RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/user/read/email",
                authorization=authorization,
                json={
                    "email": email,
                },
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

    #########################[ end read_user_by_email ]########################

    #########################[ start read_user_by_id ]######################
    @staticmethod
    def read_user_by_id(authorization: str, user_id: str, request: "Request") -> str:
        """
        Retrieves a user by user ID.

        Args:
            authorization (str): Authorization token.
            user_id (str): User ID of the user.
            request (Request): Flask request object.

        Returns:
            str: JSON response from the API.
        """
        name = f"user.read_user_by_id"
        response_msg = "An error occurred while retrieving the user"
        try:
            return RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/user/read/id",
                authorization=authorization,
                json={
                    "user_id": user_id,
                },
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

    #########################[ end read_user_by_id ]########################


###################################[ end RecipezUserUtils ]####################################
