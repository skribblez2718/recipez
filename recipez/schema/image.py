from pydantic import BaseModel, NewPath
from uuid import UUID

###################################[ start BaseImageSchema ]###################################


class BaseImageSchema(BaseModel):
    """
    Schema for validating image URL.

    Attributes:
        image_path (NewPath): The URL of the image.
    """

    image_path: NewPath


###################################[ end BaseImageSchema ]#####################################


###################################[ start CreateImageSchema ]###################################
class CreateImageSchema(BaseImageSchema):
    """
    Schema for creating an image.

    Attributes:
        author_id (UUID): The ID of the author uploading the image.
        image_path (NewPath): The path where the image will be stored.
        image_data (str): The base64-encoded image data.
    """

    author_id: UUID
    image_path: NewPath
    image_data: str


###################################[ end CreateImageSchema ]#####################################


###################################[ start DeleteImageSchema ]#########################
class DeleteImageSchema(BaseModel):
    """Schema for deleting an image."""

    image_id: UUID


###################################[ end DeleteImageSchema ]#########################
