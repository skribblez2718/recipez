from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID
import re

###################################[ start BaseImageSchema ]###################################


class BaseImageSchema(BaseModel):
    """
    Schema for validating image path/filename.

    Attributes:
        image_path (str): The filename for the image (e.g., "recipe-image.jpg").
    """

    image_path: str

    @field_validator('image_path')
    @classmethod
    def validate_image_path(cls, v: str) -> str:
        """Validate that image_path is a safe filename."""
        # Extract just the filename in case a full path was provided
        from pathlib import Path
        filename = Path(v).name

        # Validate filename pattern
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
            raise ValueError('Filename must contain only alphanumeric characters, underscores, hyphens, and dots')

        # Validate extension
        ext = Path(filename).suffix.lower()
        if ext not in {'.jpg', '.jpeg', '.png'}:
            raise ValueError('File must have .jpg, .jpeg, or .png extension')

        return v


###################################[ end BaseImageSchema ]#####################################


###################################[ start CreateImageSchema ]###################################
class CreateImageSchema(BaseImageSchema):
    """
    Schema for creating an image.

    Attributes:
        image_path (str): The filename for the image (e.g., "recipe-image.jpg")
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
