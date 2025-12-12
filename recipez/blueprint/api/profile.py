from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, g, current_app

from recipez.utils import (
    RecipezAuthNUtils,
    RecipezErrorUtils,
    RecipezSecretsUtils,
)
from recipez.utils.validation import validate_image_url
from recipez.repository import UserRepository, ApiKeyRepository
from recipez.extensions import csrf, limiter

bp = Blueprint("api/profile", __name__, url_prefix="/api/profile")


#########################[ start read_profile_api ]#########################
@bp.route("/me", methods=["GET"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
def read_profile_api() -> "Response":
    """Return the current user's profile."""
    name = f"profile.{read_profile_api.__name__}"
    response_msg = "Failed to load profile"
    try:
        user = UserRepository.get_user_by_id(g.user.user_id)
        if not user:
            return RecipezErrorUtils.handle_api_error(name, request, "User not found", response_msg)
        return jsonify(
            {
                "response": {
                    "user_id": str(user.user_id),
                    "user_name": user.user_name,
                    "user_email": user.user_email,
                    "profile_image_url": user.user_profile_image_url or "/static/img/default_user.png",
                }
            }
        )
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)


#########################[ end read_profile_api ]###########################


#########################[ start update_profile_image_api ]#################
@bp.route("/image", methods=["PUT"])
@limiter.limit("10 per minute")  # Issue 9 (MEDIUM): Rate limit profile updates
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
def update_profile_image_api() -> "Response":
    """Update current user's profile image."""
    name = f"profile.{update_profile_image_api.__name__}"
    response_msg = "Failed to update profile image"
    try:
        # Issue 3 (CRITICAL): Explicit authorization check - verify user exists and matches JWT
        user = UserRepository.get_user_by_id(g.user.user_id)
        if not user or str(user.user_id) != str(g.user.user_id):
            current_app.logger.error(f"Authorization mismatch: JWT user {g.user.user_id} attempted profile update")
            return jsonify({"error": "Unauthorized"}), 403

        image_url = request.json.get("image_url", "")
        if not isinstance(image_url, str) or not image_url:
            return RecipezErrorUtils.handle_api_error(name, request, "Invalid image url", response_msg)

        # Issue 1 (CRITICAL): Validate image URL to prevent XSS and path traversal
        if not validate_image_url(image_url):
            current_app.logger.warning(f"Rejected unsafe image URL from user {g.user.user_id}: {image_url[:100]}")
            return RecipezErrorUtils.handle_api_error(name, request, "Invalid or unsafe image URL", response_msg)

        updated = UserRepository.update_profile_image(g.user.user_id, image_url)
        if not updated:
            return RecipezErrorUtils.handle_api_error(name, request, "User not found", response_msg)
        return jsonify({"response": {"message": "Profile image updated"}})
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)


#########################[ end update_profile_image_api ]###################


#########################[ start create_api_key_api ]#########################
@bp.route("/api-keys", methods=["POST"])
@limiter.limit("10 per hour")  # Rate limit API key creation
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
def create_api_key_api() -> "Response":
    """Create a new API key for the current user."""
    name = f"profile.{create_api_key_api.__name__}"
    response_msg = "Failed to create API key"

    try:
        data = request.json or {}

        # Validate name
        key_name = data.get("name", "").strip()
        if not key_name:
            return jsonify({"error": "Name is required"}), 400
        if len(key_name) > 100:
            return jsonify({"error": "Name must be 100 characters or less"}), 400

        # Validate scopes
        scopes = data.get("scopes", [])
        if not isinstance(scopes, list) or not scopes:
            return jsonify({"error": "At least one scope is required"}), 400

        # Filter to only allowed scopes (from config)
        allowed_scopes = current_app.config.get("RECIPEZ_USER_JWT_SCOPES", [])
        valid_scopes = [s for s in scopes if s in allowed_scopes]
        if not valid_scopes:
            return jsonify({"error": "No valid scopes provided"}), 400

        # Parse expiration
        expires_at = None
        expires_str = data.get("expires_at")
        never_expires = data.get("never_expires", False)

        if not never_expires and expires_str:
            try:
                # Parse ISO format datetime
                expires_at = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                if expires_at < datetime.now(timezone.utc):
                    return jsonify({"error": "Expiration must be in the future"}), 400
            except (ValueError, AttributeError):
                return jsonify({"error": "Invalid expiration date format"}), 400

        # Generate the JWT
        jwt_token = RecipezSecretsUtils.generate_api_key_jwt(
            str(g.user.user_sub),
            valid_scopes,
            expires_at,
        )

        # Generate hash for storage
        jwt_hash = RecipezSecretsUtils.generate_jwt_hash(jwt_token)

        # Store in database
        api_key = ApiKeyRepository.create_api_key(
            user_id=str(g.user.user_id),
            name=key_name,
            jwt_hash=jwt_hash,
            scopes=valid_scopes,
            expires_at=expires_at,
        )

        # Return the token ONCE - it cannot be retrieved again
        return jsonify({
            "response": {
                "api_key": api_key.as_dict(),
                "token": jwt_token,  # Only returned at creation!
                "warning": "Save this token now. It cannot be retrieved later.",
            }
        }), 201

    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)


#########################[ end create_api_key_api ]###########################


#########################[ start list_api_keys_api ]##########################
@bp.route("/api-keys", methods=["GET"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
def list_api_keys_api() -> "Response":
    """List all API keys for the current user (metadata only)."""
    name = f"profile.{list_api_keys_api.__name__}"
    response_msg = "Failed to list API keys"

    try:
        api_keys = ApiKeyRepository.get_api_keys_by_user_id(str(g.user.user_id))
        return jsonify({
            "response": {
                "api_keys": [k.as_dict() for k in api_keys],
                "available_scopes": current_app.config.get("RECIPEZ_USER_JWT_SCOPES", []),
            }
        })
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)


#########################[ end list_api_keys_api ]############################


#########################[ start delete_api_key_api ]#########################
@bp.route("/api-keys/<api_key_id>", methods=["DELETE"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
def delete_api_key_api(api_key_id: str) -> "Response":
    """Delete an API key."""
    name = f"profile.{delete_api_key_api.__name__}"
    response_msg = "Failed to delete API key"

    try:
        # Validate UUID format
        try:
            from uuid import UUID
            UUID(api_key_id)
        except ValueError:
            return jsonify({"error": "Invalid API key ID"}), 400

        success = ApiKeyRepository.delete_api_key(
            api_key_id=api_key_id,
            user_id=str(g.user.user_id),
        )

        if not success:
            return jsonify({"error": "API key not found"}), 404

        return jsonify({
            "response": {"message": "API key deleted successfully"}
        })

    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)


#########################[ end delete_api_key_api ]###########################
