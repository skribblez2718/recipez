import re

from flask import Blueprint, request, jsonify

from recipez.schema import CreateUserSchema, ReadUserByEmailSchema
from recipez.utils import RecipezAuthNUtils, RecipezAuthZUtils, RecipezErrorUtils, RecipezSecretsUtils
from recipez.repository import UserRepository
from recipez.dataclass import User
from dataclasses import asdict
from recipez.extensions import csrf

bp = Blueprint("api/user", __name__, url_prefix="/api/user")


#########################[ start add_user_api ]#########################
@bp.route("/create", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.user_create_required
def create_user_api() -> "Response":
    """
    Adds a new user to the database if they don't already exist.

    Expected JSON payload:
        - user_email: The email address of the user

    Returns:
        Response: JSON response with user_id and success status
    """
    name = f"user.{create_user_api.__name__}"
    log_msg = ""
    response_msg = "Failed to create user"

    try:
        data = CreateUserSchema(**request.json)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    email: str = data.email
    try:
        provided_username = email.split("@")[0]
        # Keep only alphanumeric, hyphen, and underscore characters
        username = re.sub(r"[^a-zA-Z0-9_-]", "", provided_username)
        if not username:
            log_msg = f"Invalid username derived from email: {email}"
            return RecipezErrorUtils.handle_api_error(name, request, log_msg, response_msg)

        encrypted_email = RecipezSecretsUtils.encrypt(email)
        email_hmac = RecipezSecretsUtils.generate_hmac(email)
        user_model = UserRepository.create_user(
            encrypted_email, email_hmac, username, "/static/img/default_user.png"
        )
        user = User(
            user_id=str(user_model.user_id),
            user_sub=str(user_model.user_sub),
            user_email=user_model.user_email,
            user_name=user_model.user_name,
            user_created_at=user_model.user_created_at,
            user_profile_image_url=user_model.user_profile_image_url,
        )
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    return jsonify({"response": asdict(user)})


#########################[ end add_user_api ]###########################


#########################[ start read_user_by_email_api ]#########################
@bp.route("/read/email", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.user_read_required
def read_user_by_email_api() -> "Response":
    """
    Adds a new user to the database if they don't already exist.

    Expected JSON payload:
        - user_email: The email address of the user

    Returns:
        Response: JSON response with user_id and success status
    """
    name = f"user.{read_user_by_email_api.__name__}"
    response_msg = "An unexpected error occurred"

    try:
        data = ReadUserByEmailSchema(**request.json)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    email: str = data.email
    email_hmac = RecipezSecretsUtils.generate_hmac(email)

    try:
        user_model = UserRepository.get_user_by_email_hmac(email_hmac)
        if user_model:
            user = User(
                user_id=str(user_model.user_id),
                user_sub=str(user_model.user_sub),
                user_email=user_model.user_email,
                user_name=user_model.user_name,
                user_created_at=user_model.user_created_at,
                user_profile_image_url=user_model.user_profile_image_url,
            )
            return jsonify({"response": asdict(user)})
        return jsonify({"response": {"error": "User not found"}})
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)


#########################[ end read_user_by_email_api ]###########################
