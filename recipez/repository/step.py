from typing import Optional, List
from recipez import sqla_db
from recipez.model import RecipezStepModel


#####################################[ start StepRepository ]####################################
class StepRepository:
    """
    Repository for step-related database operations using SQLAlchemy.

    This class provides methods to interact with the Step model in the database,
    replacing raw SQL queries with SQLAlchemy ORM operations.
    """

    #########################[ start create_step ]#########################
    @staticmethod
    def create_step(text: str, recipe_id: str, author_id: str) -> RecipezStepModel:
        """
        Create a new step in the database.

        Args:
            text (str): The text of the step.
            recipe_id (str): The ID of the recipe this step belongs to.
            author_id (str): The ID of the author who created this step.

        Returns:
            RecipezStepModel: The created step object.
        """
        step = RecipezStepModel(
            step_text=text, step_recipe_id=recipe_id, step_author_id=author_id
        )
        sqla_db.session.add(step)
        sqla_db.session.commit()
        return step

    #########################[ end create_step ]#########################

    #########################[ start read_step_by_id ]#########################
    @staticmethod
    def read_step_by_id(step_id: str) -> Optional[RecipezStepModel]:
        """
        Get a step by its ID.

        Args:
            step_id (str): The ID of the step to retrieve.

        Returns:
            Optional[RecipezStepModel]: The step object if found, None otherwise.
        """
        return (
            sqla_db.session.query(RecipezStepModel).filter_by(step_id=step_id).first()
        )

    #########################[ end read_step_by_id ]#########################

    #########################[ start read_steps_by_recipe_id ]#########################
    @staticmethod
    def read_steps_by_recipe_id(recipe_id: str) -> List[RecipezStepModel]:
        """
        Get all steps for a specific recipe.

        Args:
            recipe_id (str): The ID of the recipe.

        Returns:
            List[RecipezStepModel]: A list of step objects for the recipe.
        """
        return (
            sqla_db.session.query(RecipezStepModel)
            .filter_by(step_recipe_id=recipe_id)
            .all()
        )

    #########################[ end read_steps_by_recipe_id ]#########################

    #########################[ start update_step ]#########################
    @staticmethod
    def update_step(step_id: str, text: str) -> bool:
        """
        Update a step in the database.

        Args:
            step_id (str): The ID of the step to update.
            text (str): The new text of the step.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        step = StepRepository.read_step_by_id(step_id)
        if step:
            step.step_text = text
            sqla_db.session.commit()
            return True
        return False

    #########################[ end update_step ]#########################

    #########################[ start delete_step ]#########################
    @staticmethod
    def delete_step(step_id: str) -> bool:
        """
        Delete a step from the database.

        Args:
            step_id (str): The ID of the step to delete.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        step = StepRepository.read_step_by_id(step_id)
        if step:
            sqla_db.session.delete(step)
            sqla_db.session.commit()
            return True
        return False

    #########################[ end delete_step ]#########################

    #########################[ start is_step_author ]#########################
    @staticmethod
    def is_step_author(step_id: str, author_id: str) -> bool:
        """
        Check if a user is the author of a step.

        Args:
            step_id (str): The ID of the step.
            author_id (str): The ID of the user to check.

        Returns:
            bool: True if the user is the author, False otherwise.
        """
        step = StepRepository.read_step_by_id(step_id)
        return step is not None and step.step_author_id == author_id

    #########################[ end is_step_author ]#########################


#####################################[ end StepRepository ]####################################
