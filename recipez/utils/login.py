import re
from flask import Request, current_app, flash
from typing import Dict

from recipez.utils import (
    RecipezAPIUtils,
    RecipezErrorUtils,
)


###################################[ start RecipezLoginUtils ]###################################
class RecipezLoginUtils:
    """
    A class to handle login validation and insertion for the Recipez application.
    """

    #########################[ start login_email ]#############################
    @staticmethod
    def login_email(
        email: str, request: Request, session: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Sends a request to the backend API to initiate code delivery.
        This function now works with the refactored code API structure.

        Arguments:
            email (str): The email address to send the code to.
            request (Request): The Flask request object.
            session (Dict): The session dictionary containing the session ID.

        Returns:
            Union[Dict[str, str], None]: A dictionary containing the response data or None if an error occurred.
        """
        name = f"login.{login_email.__name__}"
        response_msg = "An error occurred while sending the email"
        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/auth/login/email",
                json={
                    "email": email,
                    "session_id": session.get("session_id"),
                },
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if response is None or (isinstance(response, dict) and "error" in response):
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        return response

    #########################[ end login_email ]###############################

    #########################[ start login_verify ]#############################
    @staticmethod
    def login_verify(
        email: str, request: Request, session: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Sends a request to the backend API to initiate code delivery.
        This function now works with the refactored code API structure.

        Arguments:
            email (str): The email address to send the code to.
            request (Request): The Flask request object.
            session (Dict): The session dictionary containing the session ID.

        Returns:
            Union[Dict[str, str], None]: A dictionary containing the response data or None if an error occurred.
        """
        name = f"login.login_verify"
        response_msg = "An error occurred while sending the email"
        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/auth/login/verify",
                json={
                    "email": code_form.email.data,
                    "code": complete_code,
                    "session_id": session.get("session_id"),
                },
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if response is None or (isinstance(response, dict) and "error" in response):
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        return response

    #########################[ end login_verify ]###############################


###################################[ end RecipezLoginUtils ]####################################
