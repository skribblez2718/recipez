from typing import Optional, List
import psycopg
from sqlalchemy import exc
from flask import flash
from recipez import sqla_db
from recipez.model import RecipezRecipeModel


#####################################[ start RecipeRepository ]####################################
class RecipeRepository:
    """
    Repository for recipe-related database operations using SQLAlchemy.

    This class provides methods to interact with the Recipe model in the database,
    replacing raw SQL queries with SQLAlchemy ORM operations.
    """

    #########################[ start get_recipe_by_id ]#########################
    @staticmethod
    def get_recipe_by_id(recipe_id: str) -> Optional[RecipezRecipeModel]:
        """
        Get a recipe by its ID.

        Args:
            recipe_id (str): The ID of the recipe to retrieve.

        Returns:
            Optional[RecipezRecipeModel]: The recipe object if found, None otherwise.
        """
        return (
            sqla_db.session.query(RecipezRecipeModel)
            .filter_by(recipe_id=recipe_id)
            .first()
        )

    #########################[ end get_recipe_by_id ]#########################

    #########################[ start read_all_recipes ]#########################
    @staticmethod
    def read_all_recipes() -> List[RecipezRecipeModel]:
        """
        Get all recipes from the database.

        Returns:
            List[RecipezRecipeModel]: A list of all recipe objects.
        """
        return sqla_db.session.query(RecipezRecipeModel).all()

    #########################[ end read_all_recipes ]#########################

    #########################[ start get_recipes_by_author_id ]#########################
    @staticmethod
    def get_recipes_by_author_id(author_id: str) -> List[RecipezRecipeModel]:
        """
        Get all recipes created by a specific author.

        Args:
            author_id (str): The ID of the author.

        Returns:
            List[RecipezRecipeModel]: A list of recipe objects created by the author.
        """
        return (
            sqla_db.session.query(RecipezRecipeModel)
            .filter_by(recipe_author_id=author_id)
            .all()
        )

    #########################[ end get_recipes_by_author_id ]#########################

    #########################[ start get_recipes_by_category_id ]#########################
    @staticmethod
    def get_recipes_by_category_id(category_id: str) -> List[RecipezRecipeModel]:
        """
        Get all recipes in a specific category.

        Args:
            category_id (str): The ID of the category.

        Returns:
            List[RecipezRecipeModel]: A list of recipe objects in the category.
        """
        return (
            sqla_db.session.query(RecipezRecipeModel)
            .filter_by(recipe_category_id=category_id)
            .all()
        )

    #########################[ end get_recipes_by_category_id ]#########################

    #########################[ start create_recipe ]#########################
    @staticmethod
    def create_recipe(
        name: str,
        description: str,
        category_id: str,
        image_id: str,
        author_id: str,
    ) -> RecipezRecipeModel:
        """
        Create a new recipe in the database.

        Args:
            name (str): The name of the recipe.
            description (str): The description of the recipe.
            category_id (str): The ID of the category for this recipe.
            image_id (str): The ID of the image for this recipe.
            author_id (str): The ID of the author who created this recipe.

        Returns:
            RecipezRecipeModel: The created recipe object.

        Raises:
            ValueError: If a recipe with the given name already exists.
        """
        recipe = RecipezRecipeModel(
            recipe_name=name,
            recipe_description=description,
            recipe_category_id=category_id,
            recipe_image_id=image_id,
            recipe_author_id=author_id,
        )
        sqla_db.session.add(recipe)
        try:
            sqla_db.session.commit()
            return recipe
        except (exc.IntegrityError, psycopg.errors.UniqueViolation) as e:
            sqla_db.session.rollback()
            raise ValueError(f"Recipe with name '{name}' already exists")
        except Exception as e:
            raise e

    #########################[ end create_recipe ]#########################

    #########################[ start update_recipe ]#########################
    @staticmethod
    def update_recipe(
        recipe_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category_id: Optional[str] = None,
        image_id: Optional[str] = None,
    ) -> bool:
        """
        Update a recipe in the database.

        Args:
            recipe_id (str): The ID of the recipe to update.
            name (Optional[str]): The new name of the recipe.
            description (Optional[str]): The new description of the recipe.
            category_id (Optional[str]): The new category ID for this recipe.
            image_id (Optional[str]): The new image ID for this recipe.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        recipe = RecipeRepository.get_recipe_by_id(recipe_id)
        if recipe:
            if name is not None:
                recipe.recipe_name = name
            if description is not None:
                recipe.recipe_description = description
            if category_id is not None:
                recipe.recipe_category_id = category_id
            if image_id is not None:
                recipe.recipe_image_id = image_id
            sqla_db.session.commit()
            return True
        return False

    #########################[ end update_recipe ]#########################

    #########################[ start delete_recipe ]#########################
    @staticmethod
    def delete_recipe(recipe_id: str) -> bool:
        """
        Delete a recipe from the database.

        Args:
            recipe_id (str): The ID of the recipe to delete.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        recipe = RecipeRepository.get_recipe_by_id(recipe_id)
        if recipe:
            sqla_db.session.delete(recipe)
            sqla_db.session.commit()
            return True
        return False

    #########################[ end delete_recipe ]#########################

    #########################[ start is_recipe_author ]#########################
    @staticmethod
    def is_recipe_author(recipe_id: str, author_id: str) -> bool:
        """
        Check if a user is the author of a recipe.

        Args:
            recipe_id (str): The ID of the recipe.
            author_id (str): The ID of the user to check.

        Returns:
            bool: True if the user is the author, False otherwise.
        """
        recipe = RecipeRepository.get_recipe_by_id(recipe_id)
        return recipe is not None and recipe.recipe_author_id == author_id

    #########################[ end is_recipe_author ]#########################


#####################################[ end RecipeRepository ]####################################
