from uuid import UUID
from typing import Dict
from flask import (
    Blueprint,
    current_app,
    session,
    Response,
    request,
    jsonify,
)
from datetime import datetime, timedelta, timezone

from recipez.schema import (
    CreateCodeSchema,
    ReadCodeSchema,
    UpdateCodeSchema,
    VerifyCodeSchema,
    DeleteCodeSchema,
)
from recipez.extensions import csrf
from recipez.utils import (
    RecipezErrorUtils,
    RecipezSecretsUtils,
    RecipezAuthNUtils,
    RecipezAuthZUtils,
)
from recipez.repository import CodeRepository


MAX_SENDS: int = 3
MAX_CODE_ATTEMPTS: int = 3
CODE_EXPIRATION_MINUTES: int = 5

bp = Blueprint("api/code", __name__, url_prefix="/api/code")


#########################[ start create_code_api ]#######################
@bp.route("/create", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.code_create_required
def create_code_api() -> Response:
    """
    Creates a new verification code in the database.
    """
    name = f"code.{create_code_api.__name__}"
    response_msg = "Failed to create code"

    try:
        data: Dict[str, str] = CreateCodeSchema(**request.json)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    code_email: str = data.email
    code_session_id: str = data.session_id
    code_part_1: str = RecipezSecretsUtils.gen_code_part()
    code_part_2: str = RecipezSecretsUtils.gen_code_part()

    try:
        # Create a new code
        current_time = datetime.now(timezone.utc)
        code: str = f"{code_part_1}-{code_part_2}"
        code_value = RecipezSecretsUtils.generate_hash(code)
        code_expires_at: datetime = current_time + timedelta(
            minutes=CODE_EXPIRATION_MINUTES
        )
        code_attempts: int = 0
        code_count: int = 1
        code_session_id: str = code_session_id

        _ = CodeRepository.create_code(
            code_count=code_count,
            code_value=code_value,
            code_expires_at=code_expires_at,
            code_attempts=code_attempts,
            code_email=code_email,
            code_session_id=code_session_id,
        )

        # Store the session ID in the user's session
        if not session.get("session_id"):
            session["session_id"] = code_session_id

        return jsonify(
            {
                "response": {
                    "code": code,
                }
            }
        )
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)


#########################[ end create_code_api ]#########################


#########################[ start read_code_api ]#######################
@bp.route("/read", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.code_read_required
def read_code_api() -> Response:
    """
    Reads a verification code for a given email and session.

    Arguments:
        None (data comes from request.json)

    Returns:
        Response: Flask JSON response with code data or error message.
    """
    name = f"code.{read_code_api.__name__}"
    response_msg = "Code does not exist"

    try:
        data: Dict[str, str] = ReadCodeSchema(**request.json)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    email: str = data.email
    session_id: str = data.session_id

    try:
        code = CodeRepository.read_code(email, session_id)
        if code:
            # Convert RecipezCodeModel to a dictionary for JSON serialization
            return jsonify(
                {
                    "response": {
                        "code": {
                            "code_id": str(code.code_id),
                            "code_count": code.code_count,
                            "code_value": code.code_value,
                            "code_issued_at": (
                                code.code_issued_at.isoformat()
                                if code.code_issued_at
                                else None
                            ),
                            "code_expires_at": (
                                code.code_expires_at.isoformat()
                                if code.code_expires_at
                                else None
                            ),
                            "code_attempts": code.code_attempts,
                            "code_cooldown": (
                                code.code_cooldown.isoformat()
                                if code.code_cooldown
                                else None
                            ),
                            "code_email": code.code_email,
                            "code_session_id": str(code.code_session_id),
                        }
                    }
                }
            )
        else:
            return jsonify({"response": {"error": response_msg}})
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)


#########################[ end read_code_api ]#########################


#########################[ start update_code_api ]#######################
@bp.route("/update", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.code_update_required
def update_code_api() -> Response:
    """
    Updates an existing verification code's properties (count, attempts, cooldown).

    Arguments:
        None (data comes from request.json)

    Returns:
        Response: Flask JSON response with success or error message.
    """
    name = f"code.{update_code_api.__name__}"
    response_msg = "Failed to update code"

    try:
        data = UpdateCodeSchema(**request.json)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    code = data.code
    email = data.email

    # Parse datetime strings to datetime objects if present
    code_cooldown = (
        datetime.strptime(code.code_cooldown, "%Y-%m-%dT%H:%M:%S.%f")
        if code.code_cooldown
        else None
    )
    current_time = datetime.now()
    code_issued_at = (
        datetime.strptime(code.code_issued_at, "%Y-%m-%dT%H:%M:%S.%f")
        if code.code_issued_at
        else current_time
    )
    code_count = code.code_count
    code_id = code.code_id

    # Reset the send window after 15 minutes
    if current_time - code_issued_at >= timedelta(minutes=15):
        CodeRepository.reset_code(
            code_id,
            current_time,
            current_time + timedelta(minutes=CODE_EXPIRATION_MINUTES),
        )
        current_app.logger.info(f"Send window expired for {email}; code reset")
        return jsonify(
            {"response": {"message": "Send window expired. Please request a new code."}}
        )

    if code_cooldown:
        if code_cooldown <= current_time:
            CodeRepository.delete_code(code_id)
            current_app.logger.info(f"Expired code deleted for {email} after cooldown.")
            return jsonify(
                {
                    "response": {
                        "message": "Cool down has expired. Please request a new code."
                    }
                }
            )

        if code_cooldown > current_time:
            remaining_seconds = (code_cooldown - current_time).total_seconds()
            remaining_minutes = max(1, int(remaining_seconds // 60))
            log_msg = f"Login attempt made during cooldown period"
            response_msg = f"Too many attempts. Please wait {remaining_minutes} minute{'s' if remaining_minutes > 1 else ''} before trying again."
            return RecipezErrorUtils.handle_api_error(name, request, log_msg, response_msg)
    else:
        code_count += 1

    # If max sends reached again, apply cooldown
    if code_count > MAX_SENDS:
        # Use actual number of sends to determine tiered cooldown
        cooldown_delta = timedelta(
            minutes=5 * (code_count - MAX_SENDS)
        )  # 5 minutes per excess attempt
        code_cooldown = current_time + cooldown_delta
        cooldown_minutes = int(cooldown_delta.total_seconds() // 60)

        CodeRepository.update_code_cooldown(code_id, code_cooldown)
        log_msg = f"Too many codes sent"
        response_msg = f"Too many codes sent. Please wait {cooldown_minutes} minute{'s' if cooldown_minutes > 1 else ''} before trying again."
        return RecipezErrorUtils.handle_api_error(name, request, log_msg, response_msg)

    # Save incremented count
    CodeRepository.update_code_count(code_id, code_count)

    log_msg = f"Code already sent to {email}"
    response_msg = f"Code has already been sent to {email}. "
    response_msg += f"You have {MAX_SENDS - code_count} sends remaining."
    return RecipezErrorUtils.handle_api_error(name, request, log_msg, response_msg)


#########################[ end update_code_api ]#########################


#########################[ start verify_code_api ]#######################
@bp.route("/verify", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.code_verify_required
def verify_code_api() -> Response:
    """
    Verifies a user-submitted login code tied to their email and session.

    This endpoint:
    - Accepts JSON payload with email, and code
    - Validates if code is present, not expired, not abused (via attempts).
    - Triggers cooldown if max attempts exceeded.
    - Deletes code on successful validation.
    - Returns login success or descriptive failure.

    Arguments:
        None

    Returns:
        Response: A Flask JSON response with either a success or error message.
    """
    name = f"auth.{verify_code_api.__name__}"
    code_error = f"Failed to validate code"

    try:
        data: Dict[str, str] = VerifyCodeSchema(**request.json)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, code_error)

    user_code: str = data.received_code
    code: "CodeDataSchema" = data.code
    try:
        log_msg = ""
        response_msg = ""

        if not user_code or not code:
            log_msg = f"Invalid code"
            response_msg = f"Invalid code"
            return RecipezErrorUtils.handle_api_error(name, request, log_msg, response_msg)

        # Extract relevant code data
        code_id = code.code_id
        code_expires_at = datetime.strptime(
            code.code_expires_at, "%Y-%m-%dT%H:%M:%S.%f"
        )
        code_attempts = code.code_attempts
        code_cooldown = (
            datetime.strptime(code.code_cooldown, "%Y-%m-%dT%H:%M:%S.%f")
            if code.code_cooldown
            else None
        )
        code_value = code.code_value
        current_time = datetime.now()

        if code_cooldown and current_time < code_cooldown:
            log_msg = f"Code cooldown still in effect"
            _ = RecipezSecretsUtils.generate_hash(user_code)
            return RecipezErrorUtils.handle_api_error(
                name, request, log_msg, code_error
            )

        if current_time > code_expires_at:
            CodeRepository.delete_code(code_id)
            log_msg = f"Code has expired"
            _ = RecipezSecretsUtils.generate_hash(user_code)
            return RecipezErrorUtils.handle_api_error(
                name, request, log_msg, code_error
            )

        # Increment attempt count before verification
        code_attempts += 1
        CodeRepository.update_code_attempts(code_id, code_attempts)
        if code_attempts >= MAX_CODE_ATTEMPTS:
            current_app.logger.error(
                f"{current_app.config.get('RECIPEZ_ERROR_MESSAGE')} in auth.verify_code_api. "
                f"Code attempts exceeded"
            )
            cooldown_delta = timedelta(
                minutes=5 * (code_attempts - MAX_CODE_ATTEMPTS + 1)
            )  # 5 minutes per excess attempt
            cooldown_time = current_time + cooldown_delta
            CodeRepository.update_code_cooldown(code_id, cooldown_time)
            log_msg = f"Too many incorrect attempts"
            response_msg = f"Too many incorrect attempts. Please wait {int(cooldown_delta.total_seconds() // 60)} minutes before trying again."
            _ = RecipezSecretsUtils.generate_hash(user_code)
            return RecipezErrorUtils.handle_api_error(name, request, log_msg, response_msg)

        user_code_value = RecipezSecretsUtils.compare_hash(code_value, user_code)
        if not user_code_value:
            attempts_left = MAX_CODE_ATTEMPTS - code_attempts
            log_msg = "Code mismatch from"
            response_msg = f"Invalid code. You have {attempts_left} attempts remaining."
            return RecipezErrorUtils.handle_api_error(name, request, log_msg, response_msg)

        return jsonify(
            {
                "response": {
                    "message": "Code verified successfully",
                }
            }
        )

    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, code_error)


#########################[ end verify_code_api ]#########################


#########################[ start delete_code_api ]#######################
@bp.route("/delete", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.code_delete_required
def delete_code_api() -> Response:
    """
    Deletes a verification code by its ID.

    Arguments:
        None (data comes from request.json)

    Returns:
        Response: Flask JSON response with success or error message.
    """
    name = f"code.{delete_code_api.__name__}"
    response_msg = "Failed to delete code"

    try:
        data: Dict[str, str] = DeleteCodeSchema(**request.json)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    code_id = data.code_id
    if not code_id:
        return RecipezErrorUtils.handle_api_error(
            name, request, "Missing code_id", response_msg
        )

    try:
        CodeRepository.delete_code(code_id)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    return jsonify({"response": {"message": "Code deleted successfully"}})


#########################[ end delete_code_api ]#########################
