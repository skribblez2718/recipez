from flask import (
    Response,
    Blueprint,
    current_app,
    flash,
    redirect,
    request,
    session,
    url_for,
)

from recipez.utils.session import RecipezSessionUtils

from recipez.utils import (
    RecipezCodeUtils,
    RecipezEmailUtils,
    RecipezUserUtils,
    RecipezResponseUtils,
    RecipezSecretsUtils,
    RecipezErrorUtils,
)
from recipez.form import (
    EmailForm,
    CodeForm,
    AICreateRecipeForm,
    AIModifyRecipeForm,
)

bp = Blueprint("auth", __name__, url_prefix="/auth")


#########################[ start login_email_view ]########################
@bp.route("/login/email", methods=["GET", "POST"])
def login_email_view() -> Response:
    """
    Renders the login email form and processes the submission of an email address
    to request a verification code.

    This view:
    - Displays a form for entering a user email address.
    - Validates the form input on POST requests.
    - Sends a request to the backend API to initiate code delivery.
    - Handles form validation errors and API errors with user feedback.
    - Navigates to the verification code form if email submission succeeds.

    Arguments:
        None

    Returns:
        Response: A rendered HTML page, either the email input view or the code verification view,
                  based on form state and backend response.
    """
    name = f"auth.{login_email_view.__name__}"
    email_error = "{method} returned an invalid response: {error_msg}"
    response_msg = "An error occurred while sending the verification code"
    script_nonce, link_nonce = RecipezResponseUtils.generate_nonces()
    ai_create_form = AICreateRecipeForm()
    ai_modify_form = AIModifyRecipeForm()
    template_params = {
        "template": "auth/email.html",
        "script_nonce": script_nonce,
        "link_nonce": link_nonce,
        "form": EmailForm(),
        "ai_create_form": ai_create_form,
        "ai_modify_form": ai_modify_form,
    }
    received_email: str = ""

    email_form = template_params["form"]
    if request.method == "POST":
        if not email_form.validate_on_submit():
            return RecipezErrorUtils.handle_view_error(
                name, request, None, None, **template_params
            )

        received_email = email_form.email.data.strip().lower()
        session["verify_email"] = received_email

        # Ensure a valid UUID session_id exists for API calls
        # This handles both new sessions and existing ones
        session_id = RecipezSessionUtils.ensure_session_id()
        authorization = RecipezSecretsUtils.get_valid_system_jwt()
        if not authorization:
            current_app.logger.error("Failed to obtain valid system JWT for login email")
            flash("An internal error occurred. Please try again.", category="danger")
            return RecipezResponseUtils.process_response(request, **template_params)

        try:
            response = RecipezCodeUtils.read_code(
                authorization, received_email, session_id, request
            )
        except Exception as e:
            response = RecipezErrorUtils.handle_api_error(name, request, e, email_error)

        code = response.get("code", "")
        if code:
            try:
                response = RecipezCodeUtils.update_code(
                    authorization, code, received_email, request
                )
            except Exception as e:
                response = RecipezErrorUtils.handle_api_error(
                    name, request, e, email_error
                )

            if response and "message" in response:
                message = response.get("message", "")
                flash(message, category="info")
                return redirect(url_for("auth.login_verify_view"))

            if response and "error" in response:
                error_msg = response.get("error", response_msg)
                if "You have" in error_msg and "sends remaining" in error_msg:
                    flash(error_msg, category="warning")
                    return redirect(url_for("auth.login_verify_view"))
                if "Too many codes sent" in error_msg:
                    RecipezErrorUtils.log_error(
                        name, error_msg, request, received_email
                    )
                    flash(error_msg, category="danger")
                    return redirect(url_for("auth.login_verify_view"))
                error_msg = response.get("error", email_error)
                error = email_error.format(
                    method="RecipezCodeUtils.update_code", error_msg=error_msg
                )
                return RecipezErrorUtils.handle_view_error(
                    name, request, error, response_msg, **template_params
                )

        try:
            response = RecipezCodeUtils.create_code(
                authorization, received_email, session_id, request
            )
        except Exception as e:
            response = RecipezErrorUtils.handle_api_error(name, request, e, email_error)

        if not response or "error" in response:
            error_msg = response.get("error", email_error)
            error = email_error.format(
                method="RecipezCodeUtils.create_code", error_msg=error_msg
            )
            return RecipezErrorUtils.handle_view_error(
                name, request, error, response_msg, **template_params
            )

        code_value = response.get("code", "")
        try:
            response = RecipezEmailUtils.email_code(
                authorization, received_email, code_value, request
            )
        except Exception as e:
            response = RecipezErrorUtils.handle_api_error(name, request, e, email_error)

        if not response or "error" in response:
            error_msg = response.get("error", email_error)
            error = email_error.format(
                method="RecipezEmailUtils.email_code", error_msg=error_msg
            )
            return RecipezErrorUtils.handle_view_error(
                name, request, error, response_msg, **template_params
            )

        message = response.get(
            "message", f"Verification code successfully sent to {received_email}"
        )
        current_app.logger.info(message)
        flash(message, category="success")
        return redirect(url_for("auth.login_verify_view"))

    return RecipezResponseUtils.process_response(request, **template_params)


#########################[ end login_email_view ]##########################


#########################[ start login_verify_view ]#########################
@bp.route("/login/verify", methods=["GET", "POST"])
def login_verify_view() -> Response:
    """
    Handles the verification of a login code submitted by a user, checks for existing user, creates one if needed,
    and stores user info in the session with a 24-hour expiry.

    Returns:
        Response: Redirect to index on success, or re-render verification form on failure.
    """

    name = f"auth.{login_verify_view.__name__}"
    verify_error = "{method} returned an invalid response: {error_msg}"
    response_msg = "An error occurred while verifying the code"
    script_nonce, link_nonce = RecipezResponseUtils.generate_nonces()
    ai_create_form = AICreateRecipeForm()
    ai_modify_form = AIModifyRecipeForm()
    template_params = {
        "template": "auth/verify.html",
        "script_nonce": script_nonce,
        "link_nonce": link_nonce,
        "form": CodeForm(),
        "email": session.get("verify_email", ""),
        "js_modules": {"verify": True},  # Enable verify.js for this view
        "ai_create_form": ai_create_form,
        "ai_modify_form": ai_modify_form,
    }

    code_form = template_params["form"]
    if request.method == "POST":
        if not code_form.validate_on_submit():
            return RecipezErrorUtils.handle_view_error(
                name, request, None, None, **template_params
            )

        received_email = code_form.email.data

        # Ensure a valid UUID session_id exists for API calls
        # This handles both new sessions and existing ones
        session_id = RecipezSessionUtils.ensure_session_id()
        received_code = code_form.code_hidden.data
        authorization = RecipezSecretsUtils.get_valid_system_jwt()
        if not authorization:
            current_app.logger.error("Failed to obtain valid system JWT for login verify")
            flash("An internal error occurred. Please try again.", category="danger")
            return RecipezResponseUtils.process_response(request, **template_params)
        if not received_code:
            code_parts = [
                code_form.code1.data,
                code_form.code2.data,
                code_form.code3.data,
                code_form.code4.data,
                code_form.code5.data,
                code_form.code6.data,
                code_form.code7.data,
                code_form.code8.data,
            ]
            received_code = "".join(code_parts[:4]) + "-" + "".join(code_parts[4:])

        try:
            response = RecipezCodeUtils.read_code(
                authorization, received_email, session_id, request
            )
        except Exception as e:
            response = RecipezErrorUtils.handle_api_error(
                name, request, e, response_msg
            )

        if not response or "error" in response:
            error_msg = response.get("error", response_msg)
            error = verify_error.format(
                method="RecipezCodeUtils.read_code", error_msg=error_msg
            )
            return RecipezErrorUtils.handle_view_error(
                name, request, error, response_msg, **template_params
            )

        code = response.get("code", "")
        try:
            response = RecipezCodeUtils.verify_code(
                authorization, received_code, code, request
            )
        except Exception as e:
            response = RecipezErrorUtils.handle_api_error(
                name, request, e, response_msg
            )

        if not response or "error" in response:
            error_msg = response.get("error", response_msg)
            if "attempts remaining" in error_msg:
                flash(error_msg, category="warning")
                return RecipezResponseUtils.process_response(request, **template_params)
            if "Too many incorrect attempts" in error_msg:
                RecipezErrorUtils.log_error(name, error_msg, request, received_email)
                flash(error_msg, category="danger")
                return RecipezResponseUtils.process_response(request, **template_params)
            error = verify_error.format(
                method="RecipezCodeUtils.verify_code", error_msg=error_msg
            )
            return RecipezErrorUtils.handle_view_error(
                name, request, error, response_msg, **template_params
            )

        code_id = code.get("code_id", "")
        try:
            response = RecipezCodeUtils.delete_code(authorization, code_id, request)
        except Exception as e:
            response = RecipezErrorUtils.handle_api_error(
                name, request, e, response_msg
            )

        if not response or "error" in response:
            error_msg = response.get("error", response_msg)
            error = verify_error.format(
                method="RecipezCodeUtils.delete_code", error_msg=error_msg
            )
            return RecipezErrorUtils.handle_view_error(
                name, request, error, response_msg, **template_params
            )

        try:
            response = RecipezUserUtils.read_user_by_email(
                authorization, received_email, request
            )
        except Exception as e:
            response = RecipezErrorUtils.handle_api_error(
                name, request, e, response_msg
            )

        if not response:
            error_msg = "No response received from RecipezUserUtils.read_user_by_email"
            error = verify_error.format(
                method="RecipezUserUtils.read_user_by_email", error_msg=error_msg
            )
            return RecipezErrorUtils.handle_view_error(
                name, request, error, response_msg, **template_params
            )

        if "error" in response:
            try:
                response = RecipezUserUtils.create_user(
                    authorization, received_email, request
                )
            except Exception as e:
                response = RecipezErrorUtils.handle_api_error(
                    name, request, e, response_msg
                )

        if not response or "error" in response:
            error_msg = "No response received from RecipezUserUtils.create_user"
            error = verify_error.format(
                method="RecipezUserUtils.create_user", error_msg=error_msg
            )
            return RecipezErrorUtils.handle_view_error(
                name, request, error, response_msg, **template_params
            )

        user_id = response.get("user_id", "")
        user_sub = response.get("user_sub", "")
        user_email = response.get("user_email", "")
        jwt_scopes = current_app.config.get("RECIPEZ_USER_JWT_SCOPES")
        additional_ai_scopes = ["ai:create-recipe", "ai:modify-recipe"]
        user_jwt = RecipezSecretsUtils.generate_jwt(user_sub, jwt_scopes, additional_ai_scopes)
        RecipezSessionUtils.login_user(
            user_id, user_email, user_jwt, jwt_scopes, remember=True
        )

        current_app.logger.info(f"User {user_sub} successfully logged in.")
        flash(response.get("message", "Logged in successfully"), category="success")
        return redirect(url_for("index.index"))

    return RecipezResponseUtils.process_response(request, **template_params)


#########################[ end login_verify_view ]###########################


###################################[ start logout ]###################################
@bp.route("/logout", methods=["GET", "POST"])
def logout() -> "Response":
    """
    Logs out the current user by clearing the session and redirecting to login.

    Returns:
        Response: A redirect response to the login email view.
    """
    RecipezSessionUtils.logout_user()
    flash("You have been logged out.", category="info")
    return redirect(url_for("auth.login_email_view"))


###################################[ end logout ]#####################################
