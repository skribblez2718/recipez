from dataclasses import dataclass
from datetime import datetime
from typing import Optional


###################################[ start User ]###################################
@dataclass
class User:
    """
    Data class representing a user in the Recipez application.

    Attributes:
        user_id (str): The unique identifier for the user (UUID).
        user_sub (str): Secondary unique identifier used as JWT subject.
        user_email (str): The email address of the user.
        user_name (str): The display name of the user.
        user_created_at (Optional[datetime]): Timestamp when the user was created.
        user_api_key (Optional[str]): API key associated with the user, if any.
        user_profile_image_url (Optional[str]): URL to the user's profile image.
    """

    user_id: str
    user_sub: str
    user_email: str
    user_name: str
    user_created_at: Optional[datetime] = None
    user_api_key: Optional[str] = None
    user_profile_image_url: Optional[str] = None


###################################[ end User ]####################################
