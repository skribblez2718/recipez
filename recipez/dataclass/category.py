from dataclasses import dataclass


###################################[ start Category ]###################################
@dataclass
class Category:
    """
    Represents a category with an ID, name, and author ID.

    Attributes:
        category_id (str): The unique identifier for the category.
        category_name (str): The name of the category.
        category_author_id (str): The unique identifier for the author of the category.
    """

    category_id: str
    category_name: str
    category_author_id: str


###################################[ end Category ]###################################
