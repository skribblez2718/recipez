import requests

from flask import (
    current_app,
    jsonify,
)
from typing import Any, Dict, Optional

from recipez.utils.error import RecipezErrorUtils
from recipez.utils.secret import RecipezSecretsUtils


###################################[ start RecipezAPIUtils ]###################################
class RecipezAPIUtils:
    """
    A class to handle HTTP requests and error handling for the Recipez API.
    """

    #########################[ start make_request ]#########################
    @staticmethod
    def make_request(
        method: str, path: str, authorization: str, request: "FlaskRequest", **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Makes a request to the Recipez API with proactive JWT renewal for system users.

        Args:
            method (str): The HTTP method to use.
            path (str): The path to the API endpoint.
            authorization (str): The authorization token.
            request (FlaskRequest): The request object.
            **kwargs: Additional keyword arguments to pass to the `requests` library.

        Returns:
            Optional[Dict]: The response from the API.
        """
        from flask import current_app

        name = "api.make_request"
        response_msg = f"An error occured while fetching {path}"
        log_msg = ""

        try:
            # Proactive JWT renewal for system user
            effective_authorization = authorization

            # Check if this is a system JWT that needs renewal
            if RecipezSecretsUtils.is_system_jwt(authorization):
                # Check if the JWT is expired or expiring within 10 minutes
                if RecipezSecretsUtils.is_jwt_expired_or_expiring(authorization, buffer_minutes=10):
                    current_app.logger.info(
                        f"Attempting proactive system JWT renewal before API call to {path}"
                    )

                    # Attempt to renew the system JWT
                    new_jwt = RecipezSecretsUtils.renew_system_jwt()
                    if new_jwt:
                        effective_authorization = new_jwt
                        current_app.logger.info(
                            f"Successfully renewed system JWT before API call to {path}"
                        )
                    else:
                        # Log warning but continue with existing JWT (reactive renewal as fallback)
                        current_app.logger.warning(
                            f"Proactive system JWT renewal failed for {path}, "
                            f"continuing with existing token (reactive renewal available as fallback)"
                        )

            url = f"{current_app.config.get('RECIPEZ_WEB_HOSTNAME')}{path}"
            headers = {"Authorization": f"Bearer {effective_authorization}"}

            response = method(url, headers=headers, **kwargs)
            response.raise_for_status()

            try:
                response = response.json()
            except ValueError as e:
                log_msg = f"Invalid JSON response from {path}: {response.text}"
                response = RecipezErrorUtils.handle_util_error(
                    name, request, log_msg, response_msg
                )

            if not response or "error" in response:
                error_msg = response.get("error", response_msg)
                log_msg = f"An error occured for {path}: {error_msg}"
                if "already exists" in error_msg.lower():
                    response_msg = error_msg
                return RecipezErrorUtils.handle_util_error(
                    name, request, log_msg, response_msg
                )

            return response.get("response", None)
        except requests.RequestException as e:
            return RecipezErrorUtils.handle_util_error(
                name, request, e, "An internal error occurred"
            )

    #########################[ end make_request ]###########################


###################################[ end RecipezAPIUtils ]####################################
