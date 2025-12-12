from flask import current_app, flash, Request, jsonify, Response
from typing import List, Dict
from wtforms import Form

from recipez.utils.response import RecipezResponseUtils


###################################[ start RecipezErrorUtils ]###################################
class RecipezErrorUtils:
    """
    A class to handle errors.
    """

    #########################[ start log_error ]########################
    @staticmethod
    def log_error(
        name: str, e: Exception | str, request: Request = None, user_context: str = None
    ) -> None:
        """
        Logs exceptions with robust and secure details for troubleshooting and security.

        Args:
            name (str): The name of the view or function where the error occurred.
            e (Exception | str): The exception or error string.
            request (Request, optional): The Flask request object for IP/user context.
            user_context (str, optional): Additional user context (e.g., user ID or email).
        """
        import traceback

        # Collect context
        client_ip = (
            request.remote_addr
            if request and hasattr(request, "remote_addr")
            else "unknown"
        )
        user_info = f" user={user_context}" if user_context else ""
        # Build base log message
        if isinstance(e, Exception):
            exc_type = type(e).__name__
            exc_msg = str(e)
            log_msg = (
                f"{current_app.config.get('RECIPEZ_ERROR_MESSAGE')} in {name} "
                f"[{exc_type}] from {client_ip}{user_info}: {exc_msg}"
            )
        else:
            log_msg = (
                f"{current_app.config.get('RECIPEZ_ERROR_MESSAGE')} in {name} "
                f"from {client_ip}{user_info}: {str(e)}"
            )
        # Add stack trace only in debug mode
        if current_app.config.get("DEBUG", False) and isinstance(e, Exception):
            tb = traceback.format_exc()
            log_msg += f"\nTraceback:\n{tb}"
        current_app.logger.error(log_msg)

    #########################[ end log_error ]##########################

    #########################[ start _get_form_errors ]###############################
    @staticmethod
    def _get_form_errors(form_errors: Dict, parent_field: str = "") -> List[str]:
        """
        Recursively extracts and flattens WTForms error messages from a form error dictionary.
        Args:
            form_errors (Dict): WTForms form.errors dict.
            parent_field (str): For nested fields, the parent field name prefix.
        Returns:
            List[str]: Flat list of error messages.
        """
        errors: List[str] = []
        for field, error_list in form_errors.items():
            field_name = f"{parent_field}.{field}" if parent_field else field
            if isinstance(error_list, dict):
                # Nested dictionary (e.g., ingredient: {quantity: [...]})
                errors.extend(
                    RecipezErrorUtils._get_form_errors(
                        error_list, parent_field=field_name
                    )
                )
            elif isinstance(error_list, list):
                for error in error_list:
                    if isinstance(error, dict):
                        # Nested dict inside a list (rare, but possible)
                        errors.extend(
                            RecipezErrorUtils._get_form_errors(
                                error, parent_field=field_name
                            )
                        )
                    else:
                        # Leaf error message
                        # Format: Ingredient - Quantity: ...
                        pretty_field = field_name.replace(".", " - ").capitalize()
                        errors.append(f"{pretty_field}: {error}")
            else:
                # Catch any other structure
                pretty_field = field_name.replace(".", " - ").capitalize()
                errors.append(f"{pretty_field}: {error_list}")
        return errors

    #########################[ end _get_form_errors ]###############################

    #########################[ start handle_view_error ]########################
    @staticmethod
    def handle_view_error(
        name: str,
        request: Request,
        error: Exception | str | None,
        response_msg: str | None,
        **template_params,
    ) -> str:
        """
        Handle view errors by logging, flashing, and rendering a response.
        Supports both general exceptions and form/API errors in views.
        Args:
            name (str): The name of the view where the error occurred.
            error (Exception | str | None, optional): The exception or error string, or None for form/API errors.
            request (Request, optional): The current request object.
            **template_params: Additional template context for rendering.
        Returns:
            str: The rendered template as a string.
        """
        form = template_params.get("form")
        form_errors_flashed = False
        if form and hasattr(form, "errors") and form.errors:
            errors = RecipezErrorUtils._get_form_errors(form.errors)
            for err in errors:
                RecipezErrorUtils.log_error(name, err)
                flash(str(err), "danger")
            form_errors_flashed = True
        # Only flash/log the error if form errors weren't already handled
        if response_msg is not None and not form_errors_flashed:
            RecipezErrorUtils.log_error(name, error)
            flash(str(response_msg), category="danger")
        return RecipezResponseUtils.process_response(request, **template_params)

    #########################[ end handle_view_error ]##########################

    #########################[ start handle_api_error ]########################
    @staticmethod
    def handle_api_error(
        name: str, request: Request, error: Exception | str, response_msg: str
    ) -> tuple[Response, int]:
        """Log an API error and return a standardized JSON response for API endpoints.

        All API endpoints should use this helper to ensure consistent error
        messages and to avoid leaking sensitive internal details to clients.

        Args:
            name: Location where the error occurred.
            request: The current request object.
            error: Exception instance or error string.
            response_msg: User facing error message.

        Returns:
            A tuple containing the JSON error payload and HTTP status code.
        """
        RecipezErrorUtils.log_error(name, error, request)
        return jsonify({"response": {"error": response_msg}}), 500

    #########################[ end handle_api_error ]########################

    #########################[ start handle_util_error ]########################
    @staticmethod
    def handle_util_error(
        name: str, request: Request, error: Exception | str, response_msg: str
    ) -> dict:
        """Log a utility function error and return a standardized dictionary response.

        Utility functions should use this helper to return consistent error
        dictionaries that can be consumed by view functions.

        Args:
            name: Location where the error occurred.
            request: The current request object.
            error: Exception instance or error string.
            response_msg: User facing error message.

        Returns:
            A dictionary containing the error information.
        """
        RecipezErrorUtils.log_error(name, error, request)
        return {"error": response_msg}

    #########################[ end handle_api_error ]########################

###################################[ end RecipezErrorUtils ]####################################
