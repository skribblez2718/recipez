import smtplib

from typing import Dict
from flask import (
    Blueprint,
    request,
    jsonify,
)
from recipez.schema import (
    EmailCodeSchema,
    EmailInviteSchema,
    EmailRecipeShareSchema,
    EmailRecipeShareFullSchema,
)
from recipez.dataclass import EmailInvite, EmailRecipeShare, EmailRecipeShareFull
from recipez.utils import (
    RecipezAuthNUtils,
    RecipezAuthZUtils,
    RecipezErrorUtils,
    RecipezEmailUtils,
)
from recipez.extensions import csrf

bp = Blueprint("api/email", __name__, url_prefix="/api/email")


###########################[ start email_code ] ##########################
@bp.route("/code", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.email_code_create_required
def email_code_api() -> Dict[str, Dict[str, str]]:
    """
    Sends an email with a verification code to the specified recipient.

    Args:
        None (data comes from request.json)

    Returns:
        Dict[str, Dict[str, str]]: A Flask JSON response with success or error message.
    """
    name = f"email.{email_code_api.__name__}"
    response_msg = "Failed to send verification code"

    try:
        data: Dict[str, str] = EmailCodeSchema(**request.json)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    recipient_email: str = data.email
    code: str = data.code
    subject = "Your Verification Code"
    html_content = RecipezEmailUtils.get_verification_code_email(code)

    try:
        result = RecipezEmailUtils.send_email(
            recipient_email, subject, html_content, request
        )
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    if not result or "error" in result:
        return RecipezErrorUtils.handle_api_error(
            name, request, result["error"], response_msg
        )

    return result


###########################[ end email_code ] ############################


###########################[ start email_invite ] ##########################
@bp.route("/invite", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.scope_required("email:invite:send")
def email_invite_api() -> Dict[str, Dict[str, str]]:
    """
    Sends an invitation email to join Recipez.

    Args:
        None (data comes from request.json)

    Returns:
        Dict[str, Dict[str, str]]: A Flask JSON response with success or error message.
    """
    name = f"email.{email_invite_api.__name__}"
    response_msg = "Failed to send invitation email"

    try:
        data = EmailInviteSchema(**request.json)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    payload = EmailInvite(
        email=data.email,
        invite_link=str(data.invite_link),
        sender_name=data.sender_name,
    )

    result = RecipezEmailUtils.email_invite(request, payload)

    if "error" in result:
        return RecipezErrorUtils.handle_api_error(
            name, request, result["error"], response_msg
        )

    return jsonify(result)


###########################[ end email_invite ] ############################


###########################[ start email_recipe_share ] ##########################
@bp.route("/recipe-share", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.scope_required("email:recipe:share")
def email_recipe_share_api() -> Dict[str, Dict[str, str]]:
    """
    Sends an email sharing a recipe.

    Args:
        None (data comes from request.json)

    Returns:
        Dict[str, Dict[str, str]]: A Flask JSON response with success or error message.
    """
    name = f"email.{email_recipe_share_api.__name__}"
    response_msg = "Failed to send recipe sharing email"

    try:
        data = EmailRecipeShareSchema(**request.json)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    payload = EmailRecipeShare(
        email=data.email,
        recipe_name=data.recipe_name,
        recipe_link=str(data.recipe_link),
        sender_name=data.sender_name,
    )

    result = RecipezEmailUtils.email_recipe_share(request, payload)

    if "error" in result:
        return RecipezErrorUtils.handle_api_error(
            name, request, result["error"], response_msg
        )

    return jsonify(result)


###########################[ end email_recipe_share ] ############################


###########################[ start email_recipe_share_full ] ##########################
@bp.route("/recipe-share-full", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.scope_required("email:recipe:share")
def email_recipe_share_full_api() -> Dict[str, Dict[str, str]]:
    """
    Sends an email sharing a full recipe with complete recipe content.

    Args:
        None (data comes from request.json)

    Returns:
        Dict[str, Dict[str, str]]: A Flask JSON response with success or error message.
    """
    name = f"email.{email_recipe_share_full_api.__name__}"
    response_msg = "Failed to send recipe sharing email"

    try:
        data = EmailRecipeShareFullSchema(**request.json)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    payload = EmailRecipeShareFull(
        email=data.email,
        recipe_name=data.recipe_name,
        recipe_description=data.recipe_description or "",
        recipe_ingredients=data.recipe_ingredients,
        recipe_steps=data.recipe_steps,
        sender_name=data.sender_name,
    )

    result = RecipezEmailUtils.email_recipe_share_full(request, payload)

    if "error" in result:
        return RecipezErrorUtils.handle_api_error(
            name, request, result["error"], response_msg
        )

    return jsonify(result)


###########################[ end email_recipe_share_full ] ############################
