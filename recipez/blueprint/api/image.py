import re
import uuid
from base64 import b64decode
from typing import Dict
from uuid import UUID
from pathlib import Path
from flask import Blueprint, g, jsonify, request, url_for, current_app

from recipez.utils import RecipezAuthNUtils, RecipezAuthZUtils, RecipezErrorUtils
from recipez.utils.image import RecipezImageValidator
from recipez.repository import ImageRepository
from recipez.schema import CreateImageSchema, DeleteImageSchema
from recipez.extensions import csrf

bp = Blueprint("api/image", __name__, url_prefix="/api/image")

# Valid filename pattern: alphanumeric, underscores, hyphens, dots
VALID_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]+$')
VALID_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png'}

# UUID filename pattern: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.ext
UUID_FILENAME_PATTERN = re.compile(
    r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\.(jpg|jpeg|png)$',
    re.IGNORECASE
)


#########################[ start create_image_api ]##############################
@bp.route("/create", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.image_create_required
def create_image_api() -> Dict:
    """Create a new image record."""
    name = "image.create_image_api"
    response_msg = "Failed to create image"

    try:
        data = CreateImageSchema(**request.json)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    try:
        # Extract just the filename (handles both full paths and simple filenames)
        raw_filename = Path(data.filename).name

        # Validate filename for security (basic pattern check)
        if not VALID_FILENAME_PATTERN.match(raw_filename):
            raise ValueError(f"Invalid filename: {raw_filename}")

        # Validate file extension
        ext = Path(raw_filename).suffix.lower()
        if ext not in VALID_IMAGE_EXTENSIONS:
            raise ValueError(f"Invalid image extension: {ext}")

        # Enforce UUID filename format - auto-convert if not UUID format
        if UUID_FILENAME_PATTERN.match(raw_filename):
            filename = raw_filename
        else:
            # Convert non-UUID filename to UUID format for safety
            filename = f"{uuid.uuid4()}{ext}"
            current_app.logger.info(
                f"Converted filename '{raw_filename}' to UUID format: '{filename}'"
            )

        # Construct the full upload path using the app's static/uploads directory
        upload_dir = Path(current_app.root_path) / "static" / "uploads"
        full_path = upload_dir / filename

        # Decode the image data
        image_bytes = b64decode(data.image_data)

        # Validate and scrub the image (removes metadata, converts RGBA to RGB for JPEG)
        validator = RecipezImageValidator(filename=filename, image_data=image_bytes)
        if not validator.is_valid:
            return RecipezErrorUtils.handle_validation_error(
                name, request, validator.error, "Invalid image format"
            )

        # Use scrubbed (sanitized) image data
        image_bytes = validator.scrubbed_image

        # Write the validated image
        full_path.write_bytes(image_bytes)

        image_url = url_for("static", filename=f"uploads/{filename}", _external=False)
        # Always use authenticated user's ID (never accept client-provided author_id)
        author_id = str(g.user.user_id)
        image = ImageRepository.create_image(image_url, author_id)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    return jsonify({"response": {"image": image.as_dict()}})


#########################[ end create_image_api ]###############################


#########################[ start delete_image_api ]##############################
@bp.route("/delete/<pk>", methods=["DELETE"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.image_delete_required
def delete_image_api(pk: str) -> Dict:
    """Delete an image."""
    name = "image.delete_image_api"
    response_msg = "Failed to delete image"

    try:
        data = DeleteImageSchema(image_id=UUID(pk))
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    try:
        deleted = ImageRepository.delete_image(str(data.image_id))
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)
    if not deleted:
        return jsonify({"response": {"error": response_msg}})

    return jsonify({"response": {"success": True}})


#########################[ end delete_image_api ]###############################
