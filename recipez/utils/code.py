import string
import secrets

from typing import Any, Dict
from flask import (
    current_app,
)
from recipez.utils.api import RecipezAPIUtils
from recipez.utils.error import RecipezErrorUtils
from recipez.repository import CodeRepository


###################################[ start RecipezCodeUtils ]###################################
class RecipezCodeUtils:
    """
    A class to handle code generation and verification.

    This class provides static methods to generate and verify verification codes,
    which are used for user authentication and password recovery.
    """

    #########################[ start create_code ]##########################
    @staticmethod
    def create_code(
        authorization: str, email: str, session_id: "UUID", request: "Request"
    ) -> Dict[str, Any]:
        """
        Creates a new verification code in the database.

        Args:
            authorization (str): Authorization token.
            email (str): Email associated with the code.
            session_id (UUID): User session ID.
            request (Request): Flask request object.

        Returns:
            str: JSON response from the API.
        """
        name = f"code.create_code"
        response_msg = "An error occurred while creating the code"
        json_payload = {
            "email": email,
            "session_id": session_id,
        }
        try:
            return RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/code/create",
                authorization=authorization,
                json=json_payload,
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

    #########################[ end create_code ]############################

    #########################[ start read_code ]##########################
    @staticmethod
    def read_code(
        authorization: str, email: str, session_id: str, request: "Request"
    ) -> Dict[str, Any]:
        """
        Reads a verification code from the database.

        Args:
            authorization (str): Authorization token.
            email (str): Email associated with the code.
            session_id (str): User session ID.
            request (Request): Flask request object.

        Returns:
            str: JSON response from the API.
        """
        name = f"code.read_code"
        response_msg = "An error occurred while retrieving the code"
        json_payload = {
            "email": email,
            "session_id": session_id,
        }
        try:
            return RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/code/read",
                authorization=authorization,
                json=json_payload,
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

    #########################[ end read_code ]############################

    #########################[ start update_code ]##########################
    @staticmethod
    def update_code(
        authorization: str, code: Dict[str, str], email: str, request: "Request"
    ) -> Dict[str, Any]:
        """
        Updates a verification code in the database.

        Args:
            authorization (str): Authorization token.
            code (Dict[str, str]): The verification code.
            email (str): Email associated with the code.
            session_id (str): User session ID.
            request (Request): Flask request object.

        Returns:
            str: JSON response from the API.
        """
        name = f"code.update_code"
        response_msg = "An error occurred while creating the code"
        try:
            return RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/code/update",
                authorization=authorization,
                json={
                    "code": code,
                    "email": email,
                },
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

    #########################[ end update_code ]############################

    #########################[ start verify_code ]##########################
    @staticmethod
    def verify_code(
        authorization: str, received_code: str, code: Dict[str, str], request: "Request"
    ) -> Dict[str, Any]:
        """
        Verifies a user-submitted login code tied to their email and session.

        Args:
            authorization (str): Authorization token.
            received_code (str): The user-submitted code.
            code (Dict[str, str]): The verification code.
            request (Request): Flask request object.

        Returns:
            str: JSON response from the API.
        """
        name = f"code.verify_code"
        response_msg = "An error occurred while verifying the code"
        try:
            return RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/code/verify",
                authorization=authorization,
                json={
                    "code": code,
                    "received_code": received_code,
                },
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

    #########################[ end verify_code ]############################

    #########################[ start delete_code ]##########################
    @staticmethod
    def delete_code(authorization: str, code_id: str, request: "Request") -> str:
        """
        Deletes a verification code by its ID.

        Args:
            authorization (str): Authorization token.
            code_id (str): ID of the code to delete.
            request (Request): Flask request object.

        Returns:
            str: JSON response from the API.
        """
        name = f"code.delete_code"
        response_msg = "An error occurred while deleting the code"
        try:
            return RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/code/delete",
                authorization=authorization,
                json={
                    "code_id": code_id,
                },
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

    #########################[ end delete_code ]############################
    #########################[ start cleanup_codes ]#########################
    @staticmethod
    def cleanup_codes() -> int:
        """Clean up expired codes from the database."""
        return CodeRepository.cleanup_expired_codes()

    #########################[ end cleanup_codes ]###########################


###################################[ end RecipezCodeUtils ]####################################
