from typing import Optional, List
from recipez import sqla_db
from recipez.model import RecipezIngredientModel


#####################################[ start IngredientRepository ]####################################
class IngredientRepository:
    """
    Repository for ingredient-related database operations using SQLAlchemy.

    This class provides methods to interact with the Ingredient model in the database,
    replacing raw SQL queries with SQLAlchemy ORM operations.
    """

    #########################[ start create_ingredient ]#########################
    @staticmethod
    def create_ingredient(
        name: str, quantity: str, measurement: str, recipe_id: str, author_id: str
    ) -> RecipezIngredientModel:
        """
        Create a new ingredient in the database.

        Args:
            name (str): The name of the ingredient.
            quantity (str): The quantity of the ingredient.
            measurement (str): The measurement unit of the ingredient.
            recipe_id (str): The ID of the recipe this ingredient belongs to.
            author_id (str): The ID of the author who created this ingredient.

        Returns:
            RecipezIngredientModel: The created ingredient object.
        """
        ingredient = RecipezIngredientModel(
            ingredient_name=name,
            ingredient_quantity=quantity,
            ingredient_measurement=measurement,
            ingredient_recipe_id=recipe_id,
            ingredient_author_id=author_id,
        )
        sqla_db.session.add(ingredient)
        sqla_db.session.commit()
        return ingredient

    #########################[ end create_ingredient ]#########################

    #########################[ start read_ingredient_by_id ]#########################
    @staticmethod
    def read_ingredient_by_id(ingredient_id: str) -> Optional[RecipezIngredientModel]:
        """
        Get an ingredient by its ID.

        Args:
            ingredient_id (str): The ID of the ingredient to retrieve.

        Returns:
            Optional[RecipezIngredientModel]: The ingredient object if found, None otherwise.
        """
        return (
            sqla_db.session.query(RecipezIngredientModel)
            .filter_by(ingredient_id=ingredient_id)
            .first()
        )

    #########################[ end read_ingredient_by_id ]#########################

    #########################[ start read_ingredients_by_recipe_id ]#########################
    @staticmethod
    def read_ingredients_by_recipe_id(recipe_id: str) -> List[RecipezIngredientModel]:
        """
        Get all ingredients for a specific recipe.

        Args:
            recipe_id (str): The ID of the recipe.

        Returns:
            List[RecipezIngredientModel]: A list of ingredient objects for the recipe.
        """
        return (
            sqla_db.session.query(RecipezIngredientModel)
            .filter_by(ingredient_recipe_id=recipe_id)
            .all()
        )

    #########################[ end read_ingredients_by_recipe_id ]#########################

    #########################[ start update_ingredient ]#########################
    @staticmethod
    def update_ingredient(
        ingredient_id: str,
        name: Optional[str] = None,
        quantity: Optional[str] = None,
        measurement: Optional[str] = None,
    ) -> bool:
        """
        Update an ingredient in the database.

        Args:
            ingredient_id (str): The ID of the ingredient to update.
            name (Optional[str]): The new name of the ingredient.
            quantity (Optional[str]): The new quantity of the ingredient.
            measurement (Optional[str]): The new measurement unit of the ingredient.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        ingredient = IngredientRepository.read_ingredient_by_id(ingredient_id)
        if ingredient:
            if name is not None:
                ingredient.ingredient_name = name
            if quantity is not None:
                ingredient.ingredient_quantity = quantity
            if measurement is not None:
                ingredient.ingredient_measurement = measurement
            sqla_db.session.commit()
            return True
        return False

    #########################[ end update_ingredient ]#########################

    #########################[ start delete_ingredient ]#########################
    @staticmethod
    def delete_ingredient(ingredient_id: str) -> bool:
        """
        Delete an ingredient from the database.

        Args:
            ingredient_id (str): The ID of the ingredient to delete.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        ingredient = IngredientRepository.read_ingredient_by_id(ingredient_id)
        if ingredient:
            sqla_db.session.delete(ingredient)
            sqla_db.session.commit()
            return True
        return False

    #########################[ end delete_ingredient ]#########################

    #########################[ start is_ingredient_author ]#########################
    @staticmethod
    def is_ingredient_author(ingredient_id: str, author_id: str) -> bool:
        """
        Check if a user is the author of an ingredient.

        Args:
            ingredient_id (str): The ID of the ingredient.
            author_id (str): The ID of the user to check.

        Returns:
            bool: True if the user is the author, False otherwise.
        """
        ingredient = IngredientRepository.read_ingredient_by_id(ingredient_id)
        return ingredient is not None and ingredient.ingredient_author_id == author_id

    #########################[ end is_ingredient_author ]#########################


#####################################[ end IngredientRepository ]####################################
