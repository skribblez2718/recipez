from datetime import datetime, timezone
from typing import Callable, Any
from flask import (
    g,
    redirect,
    current_app,
    session,
    url_for,
    request,
    jsonify,
)
from functools import wraps
from werkzeug.wrappers import Response as WerkzeugResponse

from recipez.utils.secret import RecipezSecretsUtils
from recipez.repository import UserRepository, ApiKeyRepository


###################################[ start RecipezAuthNUtils ]###################################
class RecipezAuthNUtils:
    """
    A class to handle authentication functionalities for the Recipez application.

    This class provides static methods to manage user login requirements, send emails,
    generate codes, and load user session data into the application context.
    """

    #########################[ start login_required ]#########################
    @staticmethod
    def login_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the user is authenticated before accessing the route.

        First verifies that the session ID exists in the database, then checks whether
        'user_id' and 'user_email' are present in the session. If any check fails,
        it redirects the user to the login page.

        Args:
            view_func (Callable[..., Response]): The view function to protect.

        Returns:
            Callable[..., Response]: A wrapped view function enforcing login.
        """

        @wraps(view_func)
        def wrapper(*args: Any, **kwargs: Any) -> WerkzeugResponse:
            # First verify the session exists in the database
            from recipez.repository import SessionRepository
            from recipez.utils.session import RecipezSessionUtils

            # Ensure we have a valid session_id
            session_id = RecipezSessionUtils.ensure_session_id()

            # Check if the session exists in the database
            if not SessionRepository.get_session(session_id):
                # Session doesn't exist in DB - this could be a new session
                # For login_required, we should redirect to login
                current_app.logger.info(f"Session {session_id} not found in DB, redirecting to login")
                session.clear()  # Clear any potentially corrupted session data

                # Store the requested URL for redirecting after login
                next_url = request.url if request.method == "GET" else None
                if next_url:
                    return redirect(url_for("auth.login_email_view", next=next_url))
                return redirect(url_for("auth.login_email_view"))

            # Now check if user is authenticated in the session
            if (
                not session.get("user_id")
                or not session.get("user_email")
                or not session.get("user_jwt")
            ):
                # User is not authenticated
                session.clear()
                next_url = request.url if request.method == "GET" else None
                if next_url:
                    return redirect(url_for("auth.login_email_view", next=next_url))
                return redirect(url_for("auth.login_email_view"))
            return view_func(*args, **kwargs)

        return wrapper

    #########################[ end login_required ]###########################

    #########################[ start jwt_required ]#########################
    @staticmethod
    def jwt_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has a valid JWT token.

        This decorator validates the JWT token in the Authorization header and
        extracts the scopes, storing them in g.jwt_scopes for further validation.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing JWT validation.
        """

        @wraps(view_func)
        def wrapper(*args: Any, **kwargs: Any) -> WerkzeugResponse:

            auth_header = request.headers.get("Authorization", "")

            # Enhanced Bearer token validation to prevent IndexError
            if not auth_header.startswith("Bearer "):
                current_app.logger.warning(
                    f"JWT authentication failed: missing or invalid Authorization header format"
                )
                return (
                    jsonify({"error": "Missing or invalid Authorization header"}),
                    401,
                )

            # Security: Safely extract token with proper validation
            auth_parts = auth_header.split(" ", 1)  # Limit split to prevent issues
            if len(auth_parts) != 2 or not auth_parts[1].strip():
                current_app.logger.warning(
                    f"JWT authentication failed: malformed Authorization header"
                )
                return (
                    jsonify({"error": "Malformed Authorization header"}),
                    401,
                )

            token = auth_parts[1].strip()

            # Additional token format validation
            if not token or len(token) < 10:  # Minimum reasonable JWT length
                current_app.logger.warning(
                    f"JWT authentication failed: token too short or empty"
                )
                return (
                    jsonify({"error": "Invalid token format"}),
                    401,
                )

            # Validate JWT and extract scopes
            token_payload = RecipezSecretsUtils.verify_jwt(token)
            if not token_payload:
                # JWT verification already logs the specific failure
                return jsonify({"error": "Token validation failed"}), 401

            # Validate payload structure
            if not isinstance(token_payload, dict):
                current_app.logger.warning(
                    f"JWT authentication failed: invalid payload structure"
                )
                return jsonify({"error": "Invalid token payload"}), 401

            g.jwt_scopes = token_payload.get("scope")

            # Check if this is a managed API key and validate its status
            jwt_hash = RecipezSecretsUtils.generate_jwt_hash(token)
            api_key = ApiKeyRepository.get_api_key_by_hash(jwt_hash)

            if api_key:
                # This is a managed API key - check validity
                if api_key.api_key_revoked_at is not None:
                    current_app.logger.warning(
                        f"API key revoked: {api_key.api_key_id}"
                    )
                    return jsonify({"error": "API key has been revoked"}), 401

                if api_key.api_key_expires_at is not None:
                    if api_key.api_key_expires_at < datetime.now(timezone.utc):
                        current_app.logger.warning(
                            f"API key expired: {api_key.api_key_id}"
                        )
                        return jsonify({"error": "API key has expired"}), 401

            # Store API key status for potential downstream use
            g.is_api_key = api_key is not None
            g.api_key = api_key

            # Validate user exists
            user_sub = token_payload.get("sub")
            if not user_sub:
                current_app.logger.warning(
                    f"JWT authentication failed: missing user subject in token"
                )
                return jsonify({"error": "Invalid token claims"}), 401

            user = UserRepository.get_user_by_sub(user_sub)
            if not user:
                current_app.logger.warning(
                    f"JWT authentication failed: user not found for subject: {user_sub}"
                )
                return jsonify({"error": "User not found"}), 401

            g.user = user

            # All validations passed, proceed with the view function
            return view_func(*args, **kwargs)

        return wrapper

    #########################[ end jwt_required ]###########################


###################################[ end RecipezAuthNUtils ]####################################
