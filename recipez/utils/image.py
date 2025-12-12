import re
import magic
import imghdr
import random
import os
import uuid
import base64
import json

from flask import current_app, jsonify
from uuid import UUID
from os import path
from io import BytesIO
from PIL import Image
from typing import List, Dict, Union

from recipez.utils.error import RecipezErrorUtils
from recipez.utils.api import RecipezAPIUtils
from recipez.schema.image import CreateImageSchema


###################################[ start RecipezImageValidator ]###################################
class RecipezImageValidator:
    """
    Class for handling image validation.

    Attributes:
        filename (str): The name of the image file.
        image_data (bytes): The binary data of the image.
        allowed_extensions (list[str]): List of allowed file extensions.
        allowed_types (list[str]): List of allowed MIME types.
        max_size (int): Maximum allowed file size in bytes.
        img_width (int): Desired width for resized images.
        img_height (int): Desired height for resized images.
        img_quality (int): Quality setting for saved images.
        intensity (int): Intensity for random noise addition.

    Methods:
        __init__(filename, image_data, allowed_extensions, allowed_types, max_size, img_width, img_height, img_quality, intensity):
            Initialize the RecipezImageValidator instance with provided parameters.
        (): Check if the filename is valid.
        _is_valid_extension(): Check if the file extension is allowed.
        _is_valid_filetype(): Check if the MIME type of the image is allowed.
        _is_valid_image(): Check if the image data is a valid image.
        _is_valid_file_size(): Check if the file size is within the allowed limit.
        _scrub_image(image_data, new_format): Scrub and resize the image.
        _resize(img): Resize the image to the specified dimensions.
        _add_random_noise(image_data, new_format): Add random noise to the image.
        _validate_image(): Validate the image against all checks.
    """

    #########################[ start __init__ ]#########################
    def __init__(
        self,
        filename: str,
        image_data: bytes,
        allowed_extensions: list[str] = ["jpg", "jpeg", "png"],
        allowed_types: list[str] = ["image/jpeg", "image/png"],
        max_size: int = 2097152,
        img_width: int = 500,
        img_height: int = 500,
        img_quality: int = 85,
        intensity: int = 1,
    ):
        """
        Initialize the RecipezImageValidator instance with provided parameters.

        Args:
            filename (str): The name of the image file.
            image_data (bytes): The binary data of the image.
            allowed_extensions (list[str]): List of allowed file extensions.
            allowed_types (list[str]): List of allowed MIME types.
            max_size (int): Maximum allowed file size in bytes.
            img_width (int): Desired width for resized images.
            img_height (int): Desired height for resized images.
            img_quality (int): Quality setting for saved images.
            intensity (int): Intensity for random noise addition.
        """
        self.filename = filename
        self.image_data = image_data

        self.allowed_extensions = allowed_extensions
        self.allowed_types = allowed_types
        self.max_size = max_size
        self.img_width = img_width
        self.img_height = img_height
        self.img_quality = img_quality
        self.intensity = intensity

    #########################[ end __init__ ]###########################

    #########################[ start _is_valid_filename ]#########################
    def _is_valid_filename(self) -> bool:
        """
        Check if the filename is valid.

        Returns:
            bool: True if the filename is valid, False otherwise.
        """
        pattern = re.compile(r"^[a-zA-Z0-9_\-\.]+$")
        return bool(pattern.match(self.filename))

    #########################[ end _is_valid_filename ]###########################

    #########################[ start _is_valid_extension ]#########################
    def _is_valid_extension(self) -> bool:
        """
        Check if the file extension is allowed.

        Returns:
            bool: True if the file extension is valid, False otherwise.
        """
        filename_parts = self.filename.split(".")
        return filename_parts[-1].lower() in self.allowed_extensions

    #########################[ end _is_valid_extension ]###########################

    #########################[ start _is_valid_filetype ]#########################
    def _is_valid_filetype(self) -> bool:
        """
        Check if the MIME type of the image is allowed.

        Returns:
            bool: True if the MIME type is valid, False otherwise.
        """
        file_type = magic.from_buffer(self.image_data, mime=True)
        return file_type in self.allowed_types

    #########################[ end _is_valid_filetype ]###########################

    #########################[ start _is_valid_image ]#########################
    def _is_valid_image(self) -> bool:
        """
        Check if the image data is a valid image.

        Returns:
            bool: True if the image data is valid, False otherwise.
        """
        image_type = imghdr.what(None, h=self.image_data)
        return image_type is not None

    #########################[ end _is_valid_image ]###########################

    #########################[ start _is_valid_file_size ]#########################
    def _is_valid_file_size(self) -> bool:
        """
        Check if the file size is within the allowed limit.

        Returns:
            bool: True if the file size is valid, False otherwise.
        """
        file_size = len(self.image_data)
        return file_size < self.max_size

    #########################[ end _is_valid_file_size ]###########################

    #########################[ start _scrub_image ]#########################
    def _scrub_image(self, image_data: bytes, new_format: str) -> bytes:
        """
        Scrub and resize the image.

        Args:
            image_data (bytes): The binary data of the image.
            new_format (str): The format to save the image in (e.g., "JPEG", "PNG").

        Returns:
            bytes: The processed image data.
        """
        with BytesIO(image_data) as img_stream:
            img = Image.open(img_stream)
            resized_img = self._resize(img)
            with BytesIO() as output_stream:
                resized_img.save(
                    output_stream, format=new_format, quality=self.img_quality
                )
                return output_stream.getvalue()

    #########################[ end _scrub_image ]###########################

    #########################[ start _resize ]#########################
    def _resize(self, img: Image.Image) -> Image.Image:
        """
        Resize the image to the specified dimensions.

        Args:
            img (Image.Image): The image to be resized.

        Returns:
            Image.Image: The resized image.
        """
        img.thumbnail((self.img_width, self.img_height))
        return img

    #########################[ end _resize ]###########################

    #########################[ start _add_random_noise ]#########################
    def _add_random_noise(self, image_data: bytes, new_format: str) -> bytes:
        """
        Add random noise to the image.

        Args:
            image_data (bytes): The binary data of the image.
            new_format (str): The format to save the image in (e.g., "JPEG", "PNG").

        Returns:
            bytes: The processed image data with added noise.
        """
        with Image.open(BytesIO(image_data)) as img:
            pixels = img.load()
            width, height = img.size

            for i in range(width):
                for j in range(height):
                    current_pixel = list(pixels[i, j])
                    for channel in range(3):
                        change = random.choice([-self.intensity, 0, self.intensity])
                        current_pixel[channel] = max(
                            0, min(255, current_pixel[channel] + change)
                        )
                    pixels[i, j] = tuple(current_pixel)

            with BytesIO() as output_stream:
                img.save(output_stream, format=new_format)
                return output_stream.getvalue()

    #########################[ end _add_random_noise ]###########################

    #########################[ start _validate_image ]#########################
    def _validate_image(self) -> list[str]:
        """
        Validate the image against all checks.

        Returns:
            list[str]: List of validation errors.
        """
        errors = []
        if not self._is_valid_filename():
            errors.append("Invalid file name")

        if not (self._is_valid_extension() and self._is_valid_filetype()):
            errors.append("File must be PNG or JPEG")

        if not self._is_valid_image():
            errors.append("Invalid image file")

        if not self._is_valid_file_size():
            errors.append("File must be 2MB or less")

        return errors

    #########################[ end _validate_image ]###########################


###################################[ end RecipezImageValidator ]###################################


###################################[ start RecipezImageUtils ]###################################
class RecipezImageUtils(RecipezImageValidator):
    """
    A class to handle image processing for recipes, including uploading new images
    and removing old ones.
    """

    #########################[ start create_image ]#########################
    @staticmethod
    def create_image(
        authorization: str,
        request: "Request",
        author_id: str,
        image_data: bytes,
        old_image_url: str = None,
    ) -> tuple:
        """
        Processes an image upload by validating the image, removing any old images if necessary,
        and saving the new image with a unique filename.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            author_id (str): The ID of the author.
            image_data (bytes): The binary data of the image.
            old_image_url (str, optional): The URL of the old image to be replaced. Defaults to None.

        Returns:
            tuple: A tuple containing the new image URL and a list of errors.
        """
        name = f"image.create_image"
        response_msg = "An error occurred while creating the image"

        if hasattr(image_data, "filename"):
            # Handle file upload object
            filename = image_data.filename
            file_data = image_data.read()
        else:
            # Handle raw bytes (e.g., from default recipe image)
            filename = "default_recipe.png"
            file_data = image_data

        validator = RecipezImageValidator(filename=filename, image_data=file_data)
        validation_errors = validator._validate_image()
        if validation_errors:
            return jsonify({"error": validation_errors}), 400

        # Remove old file if it's not a default image (recipe or user)
        # Issue 2 (CRITICAL): Enhanced path traversal protection
        if old_image_url and ("default_recipe.png" not in old_image_url and "default_user.png" not in old_image_url):
            # Validate old_image_url is safe before attempting deletion
            if not old_image_url.startswith('/static/uploads/'):
                current_app.logger.warning(f"Skipping deletion of unsafe path: {old_image_url[:100]}")
            else:
                old_filename = path.basename(old_image_url)

                # Additional validation: filename must be UUID-style format (alphanumeric with hyphens)
                if not re.match(r'^[a-zA-Z0-9-]+\.(png|jpg|jpeg)$', old_filename):
                    current_app.logger.warning(f"Skipping deletion of non-UUID filename: {old_filename}")
                else:
                    old_file_path = path.join(
                        current_app.root_path, "static", "uploads", old_filename
                    )

                    # Verify resolved path is still within uploads directory (prevent symlink attacks)
                    try:
                        resolved_path = path.realpath(old_file_path)
                        expected_prefix = path.realpath(path.join(current_app.root_path, "static", "uploads"))

                        if not resolved_path.startswith(expected_prefix):
                            current_app.logger.error(f"Path traversal attempt detected: {old_image_url}")
                        elif path.exists(resolved_path):
                            try:
                                os.remove(resolved_path)
                            except Exception as e:
                                current_app.logger.error(f"Error removing old image: {e}")
                    except (ValueError, OSError) as e:
                        current_app.logger.error(f"Path resolution error: {e}")

        # Determine the new format
        ext_lower = filename.rsplit(".", 1)[-1].lower()
        new_format = "JPEG" if ext_lower in ["jpg", "jpeg"] else "PNG"
        scrubbed_data: bytes = validator._scrub_image(file_data, new_format)

        # Generate a unique filename for the new image
        new_filename = f"{uuid.uuid4()}.{new_format.lower()}"
        upload_path = path.join(
            current_app.root_path, "static", "uploads", new_filename
        )

        # Encode image data as base64 string
        scrubbed_data_b64: str = base64.b64encode(scrubbed_data).decode("utf-8")

        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/image/create",
                json={
                    "author_id": author_id,
                    "image_path": upload_path,
                    "image_data": scrubbed_data_b64,
                },
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            response = RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if not response or "error" in response:
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        return response

    #########################[ end create_image ]##########################

    #########################[ start delete_image ]#############################
    @staticmethod
    def delete_image(
        authorization: str, request: "Request", image_id: str
    ) -> List[Dict[str, str]]:
        """
        Deletes an existing image.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            image_id (str): The ID of the image to delete.

        Returns:
            List[Dict[str, str]]: A list of images.
        """
        name = f"image.delete_image"
        response_msg = "An error occurred while deleting the image"

        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").delete,
                path=f"/api/image/delete/{str(image_id)}",
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if not response or "error" in response:
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        return response

    #########################[ end delete_image ]###############################


###################################[ end RecipezImageUtils ]###################################
