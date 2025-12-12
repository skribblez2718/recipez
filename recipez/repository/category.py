from typing import Optional, List
import psycopg
from sqlalchemy import exc
from flask import flash
from recipez import sqla_db
from recipez.model import RecipezCategoryModel


####################################[ start CategoryRepository ]###################################
class CategoryRepository:
    """
    Repository for category-related database operations using SQLAlchemy.

    This class provides methods to interact with the Category model in the database,
    replacing raw SQL queries with SQLAlchemy ORM operations.
    """

    #########################[ start create_category ]#########################
    @staticmethod
    def create_category(name: str, author_id: str) -> RecipezCategoryModel:
        """
        Create a new category in the database.

        Args:
            name (str): The name of the category.
            author_id (str): The ID of the author who created this category.

        Returns:
            RecipezCategoryModel: The created category object.

        Raises:
            ValueError: If a category with the given name already exists.
        """
        category = RecipezCategoryModel(
            category_name=name, category_author_id=author_id
        )
        sqla_db.session.add(category)
        try:
            sqla_db.session.commit()
            return category
        except (exc.IntegrityError, psycopg.errors.UniqueViolation) as e:
            sqla_db.session.rollback()
            raise ValueError(f"Category with name '{name}' already exists")
        except Exception as e:
            raise e

    #########################[ end create_category ]#########################

    #########################[ start read_category_by_id ]#########################
    @staticmethod
    def read_category_by_id(category_id: str) -> Optional[RecipezCategoryModel]:
        """
        Get a category by its ID.

        Args:
            category_id (str): The ID of the category to retrieve.

        Returns:
            Optional[RecipezCategoryModel]: The category object if found, None otherwise.
        """
        return (
            sqla_db.session.query(RecipezCategoryModel)
            .filter_by(category_id=category_id)
            .first()
        )

    #########################[ end read_category_by_id ]#########################

    #########################[ start read_all_categories ]#########################
    @staticmethod
    def read_all_categories() -> List[RecipezCategoryModel]:
        """
        Get all categories from the database.

        Returns:
            List[RecipezCategoryModel]: A list of all category objects.
        """
        return sqla_db.session.query(RecipezCategoryModel).all()

    #########################[ end read_all_categories ]#########################

    #########################[ start get_categories_by_author_id ]#########################
    @staticmethod
    def get_categories_by_author_id(author_id: str) -> List[RecipezCategoryModel]:
        """
        Get all categories created by a specific author.

        Args:
            author_id (str): The ID of the author.

        Returns:
            List[RecipezCategoryModel]: A list of category objects created by the author.
        """
        return (
            sqla_db.session.query(RecipezCategoryModel)
            .filter_by(category_author_id=author_id)
            .all()
        )

    #########################[ end get_categories_by_author_id ]#########################

    #########################[ start update_category ]#########################
    @staticmethod
    def update_category(category_id: str, category_name: str) -> Optional[RecipezCategoryModel]:
        """
        Update a category in the database.

        Args:
            category_id (str): The ID of the category to update.
            category_name (str): The new category_name of the category.

        Returns:
            Optional[RecipezCategoryModel]: The updated category object if successful, None otherwise.
        """
        category = CategoryRepository.read_category_by_id(category_id)
        if category:
            category.category_name = category_name
            sqla_db.session.commit()
            return category
        return None

    #########################[ end update_category ]#########################

    #########################[ start delete_category ]#########################
    @staticmethod
    def delete_category(category_id: str) -> bool:
        """
        Delete a category from the database.

        Args:
            category_id (str): The ID of the category to delete.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        category = CategoryRepository.read_category_by_id(category_id)
        if category:
            sqla_db.session.delete(category)
            sqla_db.session.commit()
            return True
        return False

    #########################[ end delete_category ]#########################

    #########################[ start is_category_author ]#########################
    @staticmethod
    def is_category_author(category_id: str, author_id: str) -> bool:
        """
        Check if a user is the author of a category.

        Args:
            category_id (str): The ID of the category.
            author_id (str): The ID of the user to check.

        Returns:
            bool: True if the user is the author, False otherwise.
        """
        category = CategoryRepository.read_category_by_id(category_id)
        return category is not None and category.category_author_id == author_id

    #########################[ end is_category_author ]#########################

    #########################[ start can_delete_category ]#########################
    @staticmethod
    def can_delete_category(category_id: str, user_id: str) -> tuple[bool, str]:
        """
        Check if a user can delete a category.

        A user can delete a category only if:
        1. They are the author of the category
        2. No OTHER users' recipes are using this category

        Args:
            category_id (str): The ID of the category.
            user_id (str): The ID of the user attempting to delete.

        Returns:
            tuple[bool, str]: (can_delete, reason) - True if can delete, False with reason if not.
        """
        from recipez.model import RecipezRecipeModel

        # Check if user owns the category
        category = CategoryRepository.read_category_by_id(category_id)
        if category is None:
            return False, "Category not found"

        if str(category.category_author_id) != str(user_id):
            return False, "You do not have permission to delete this category"

        # Check if any OTHER users' recipes use this category
        other_users_recipes = (
            sqla_db.session.query(RecipezRecipeModel)
            .filter(RecipezRecipeModel.recipe_category_id == category_id)
            .filter(RecipezRecipeModel.recipe_author_id != user_id)
            .count()
        )

        if other_users_recipes > 0:
            return False, f"Cannot delete: {other_users_recipes} recipe(s) by other users use this category"

        return True, "OK"

    #########################[ end can_delete_category ]#########################

    #########################[ start get_user_recipes_by_category ]#########################
    @staticmethod
    def get_user_recipes_by_category(category_id: str, user_id: str) -> List[dict]:
        """
        Get all recipes by a specific user that use a specific category.

        Args:
            category_id (str): The ID of the category.
            user_id (str): The ID of the user.

        Returns:
            List[dict]: A list of recipe dicts with id, name, and url for the user's recipes in this category.
        """
        from recipez.model import RecipezRecipeModel

        recipes = (
            sqla_db.session.query(RecipezRecipeModel)
            .filter(RecipezRecipeModel.recipe_category_id == category_id)
            .filter(RecipezRecipeModel.recipe_author_id == user_id)
            .all()
        )

        return [
            {
                "recipe_id": str(recipe.recipe_id),
                "recipe_name": recipe.recipe_name,
                "recipe_url": f"/recipe/{recipe.recipe_id}",
                "update_url": f"/recipe/update/{recipe.recipe_id}",
            }
            for recipe in recipes
        ]

    #########################[ end get_user_recipes_by_category ]#########################

    #########################[ start get_or_create_uncategorized ]#########################
    @staticmethod
    def get_or_create_uncategorized(system_user_id: str) -> RecipezCategoryModel:
        """
        Get the 'Uncategorized' category, creating it if it doesn't exist.

        Args:
            system_user_id (str): The system user ID to use as author if creating.

        Returns:
            RecipezCategoryModel: The Uncategorized category.
        """
        category = (
            sqla_db.session.query(RecipezCategoryModel)
            .filter(RecipezCategoryModel.category_name == "Uncategorized")
            .first()
        )

        if category is None:
            category = RecipezCategoryModel(
                category_name="Uncategorized",
                category_author_id=system_user_id,
            )
            sqla_db.session.add(category)
            sqla_db.session.commit()

        return category

    #########################[ end get_or_create_uncategorized ]#########################


####################################[ end CategoryRepository ]####################################
