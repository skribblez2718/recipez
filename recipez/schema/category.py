from pydantic import BaseModel, constr
from uuid import UUID


###################################[ start BaseCategorySchema ]###################################
class BaseCategorySchema(BaseModel):
    """
    Schema for validating category name.

    Attributes:
        category_name (str): The name of the category.
    """

    category_name: constr(min_length=2, max_length=50, pattern=r"^[a-zA-Z0-9\-_' \u2010-\u2015\u2018\u2019\u2212éèêëàâäùûüôöîïçñáíóúÉÈÊËÀÂÄÙÛÜÔÖÎÏÇÑÁÍÓÚ]+$")


###################################[ end BaseCategorySchema ]#####################################


###################################[ start CreateCategorySchema ]###################################
class CreateCategorySchema(BaseCategorySchema):
    """
    Schema for validating category creation.

    Attributes:
        author_id (UUID): The ID of the author.
    """

    author_id: UUID


###################################[ end CreateCategorySchema ]#####################################


###################################[ start ReadCategorySchema ]#####################################
class ReadCategorySchema(BaseModel):
    """
    Schema for validating category read.

    Attributes:
        category_id (UUID): The ID of the category.
    """

    category_id: UUID


###################################[ end ReadCategorySchema ]#######################################


###################################[ start UpdateCategorySchema ]#####################################
class UpdateCategorySchema(BaseCategorySchema):
    """
    Schema for validating category update.

    Attributes:
        category_id (UUID): The ID of the category.
    """

    category_id: UUID


###################################[ end UpdateCategorySchema ]#######################################


###################################[ start DeleteCategorySchema ]#####################################
class DeleteCategorySchema(BaseModel):
    """
    Schema for validating category update.

    Attributes:
        category_id (UUID): The ID of the category.
    """

    category_id: UUID


###################################[ end DeleteCategorySchema ]#######################################
