from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID
import re

###################################[ start BaseImageSchema ]###################################


class BaseImageSchema(BaseModel):
    """
    Schema for validating image filename.

    Attributes:
        filename (str): The filename for the image (e.g., "550e8400-e29b-41d4-a716-446655440000.jpg").
                       Non-UUID filenames will be auto-converted to UUID format by the API.
    """

    filename: str

    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate that filename is safe. UUID enforcement happens in API layer."""
        # Extract just the filename in case a full path was provided
        from pathlib import Path
        name = Path(v).name

        # Block dangerous patterns first (defense in depth)
        if re.search(r'(\.\.|/|\\|\x00)', name):
            raise ValueError('Filename contains unsafe characters')

        # Validate filename pattern (basic safety - UUID enforcement in API layer)
        if not re.match(r'^[a-zA-Z0-9_\-\.\s\(\)\[\]]+$', name):
            raise ValueError('Filename contains unsupported characters')

        # Validate extension
        ext = Path(name).suffix.lower()
        if ext not in {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp'}:
            raise ValueError('File must have .jpg, .jpeg, .png, .heic, .heif, or .webp extension')

        return v


###################################[ end BaseImageSchema ]#####################################


###################################[ start CreateImageSchema ]###################################
class CreateImageSchema(BaseImageSchema):
    """
    Schema for creating an image.

    Attributes:
        filename (str): The filename for the image (e.g., "550e8400-e29b-41d4-a716-446655440000.jpg").
                       Non-UUID filenames will be auto-converted to UUID format by the API.
        image_data (str): The base64-encoded image data
    """

    model_config = ConfigDict(extra="forbid")

    image_data: str


###################################[ end CreateImageSchema ]#####################################


###################################[ start DeleteImageSchema ]#########################
class DeleteImageSchema(BaseModel):
    """Schema for deleting an image."""

    image_id: UUID


###################################[ end DeleteImageSchema ]#########################
