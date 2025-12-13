from flask import current_app
from typing import List

from recipez.utils.api import RecipezAPIUtils
from recipez.utils.error import RecipezErrorUtils
from recipez.utils.image import RecipezImageUtils


###################################[ start RecipezProfileUtils ]###################################
class RecipezProfileUtils:
    """Utilities for user profile operations."""

    #########################[ start read_profile ]#########################
    @staticmethod
    def read_profile(authorization: str, request: "Request") -> dict:
        """Read current user's profile via API."""
        name = "profile.read_profile"
        response_msg = "An error occurred while loading the profile"
        try:
            return RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").get,
                path="/api/profile/me",
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

    #########################[ end read_profile ]###########################

    #########################[ start update_profile_image ]################
    @staticmethod
    def update_profile_image(
        authorization: str,
        request: "Request",
        author_id: str,
        image_file,
    ) -> dict:
        """Upload and set a new profile image."""
        name = "profile.update_profile_image"
        response_msg = "An error occurred while updating the profile image"

        # Get current profile to retrieve old image URL for cleanup
        # This ensures old custom images are deleted (but default_user.png is preserved)
        try:
            current_profile = RecipezProfileUtils.read_profile(authorization, request)
            old_image_url = current_profile.get("profile_image_url") if current_profile else None
        except Exception:
            old_image_url = None

        try:
            response = RecipezImageUtils.create_image(
                authorization, request, author_id, image_file, old_image_url
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)
        if response is None or (isinstance(response, dict) and "error" in response):
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(name, request, error_msg, response_msg)
        image_url = response.get("image", {}).get("image_url")
        if not image_url:
            return RecipezErrorUtils.handle_util_error(name, request, "missing image", response_msg)
        try:
            return RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").put,
                path="/api/profile/image",
                authorization=authorization,
                json={"image_url": image_url},
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

    #########################[ end update_profile_image ]##################

    #########################[ start generate_api_key ]####################
    @staticmethod
    def generate_api_key(authorization: str, request: "Request") -> dict:
        """Generate an API key (JWT)."""
        name = "profile.generate_api_key"
        response_msg = "An error occurred while generating the API key"
        try:
            return RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/profile/api-key",
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

    #########################[ end generate_api_key ]######################

    #########################[ start create_grocery_list ]#################
    @staticmethod
    def create_grocery_list(
        authorization: str, request: "Request", recipe_ids: List[str]
    ) -> dict:
        """Create grocery list from recipes and email to user."""
        name = "profile.create_grocery_list"
        response_msg = "An error occurred while creating the grocery list"
        try:
            return RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/profile/grocery-list",
                authorization=authorization,
                json={"recipe_ids": recipe_ids},
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

    #########################[ end create_grocery_list ]###################


###################################[ end RecipezProfileUtils ]####################################
