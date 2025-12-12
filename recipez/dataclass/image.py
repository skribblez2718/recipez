from dataclasses import dataclass

###################################[ start Image ]###################################


@dataclass
class Image:
    """
    Represents an image with various attributes including ID, URL, and author.

    Attributes:
        image_id (str): The unique identifier for the image.
        image_url (str): The URL of the image.
        image_author_id (str): The unique identifier for the author of the image.
    """

    image_id: str
    image_url: str
    image_author_id: str


###################################[ end Image ]###################################
