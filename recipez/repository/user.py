from typing import Optional, List
from recipez.extensions import sqla_db
from recipez.model import RecipezUserModel


#####################################[ start UserRepository ]####################################
class UserRepository:
    """
    Repository for User model database operations using SQLAlchemy.

    This class provides methods to interact with the User model in the database,
    replacing the raw SQL queries with SQLAlchemy ORM operations.
    """

    #########################[ start create_user ]#########################
    @staticmethod
    def create_user(
        user_email: str, user_email_hmac: str, user_name: str, profile_image_url: str
    ) -> RecipezUserModel:
        """
        Create a new user in the database.

        Args:
            user_email (str): The encrypted email of the user.
            user_email_hmac (str): The HMAC of the user's email.
            user_name (str): The username of the user.

        Returns:
            RecipezUserModel: The created user object.
        """
        user = RecipezUserModel(
            user_email=user_email,
            user_email_hmac=user_email_hmac,
            user_name=user_name,
            user_profile_image_url=profile_image_url,
        )
        sqla_db.session.add(user)
        sqla_db.session.commit()
        return user

    #########################[ end create_user ]#########################

    #########################[ start get_user_by_id ]#########################
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[RecipezUserModel]:
        """
        Get a user by their ID.

        Args:
            user_id (str): The ID of the user to retrieve.

        Returns:
            Optional[RecipezUserModel]: The user object if found, None otherwise.
        """
        return (
            sqla_db.session.query(RecipezUserModel).filter_by(user_id=user_id).first()
        )

    #########################[ end get_user_by_id ]#########################

    #########################[ start get_user_by_username ]#########################
    @staticmethod
    def get_user_by_username(user_name: str) -> Optional[RecipezUserModel]:
        """
        Get a user by their username.

        Args:
            user_name (str): The username of the user to retrieve.

        Returns:
            Optional[RecipezUserModel]: The user object if found, None otherwise.
        """
        return (
            sqla_db.session.query(RecipezUserModel)
            .filter_by(user_name=user_name)
            .first()
        )

    #########################[ end get_user_by_username ]#########################

    #########################[ start get_user_by_sub ]#########################
    @staticmethod
    def get_user_by_sub(user_sub: str) -> Optional[RecipezUserModel]:
        """
        Get a user by their user_sub (UUID).
        Args:
            user_sub (str): The UUID string of the user to retrieve.
        Returns:
            Optional[RecipezUserModel]: The user object if found, None otherwise.
        """
        return (
            sqla_db.session.query(RecipezUserModel).filter_by(user_sub=user_sub).first()
        )

    #########################[ end get_user_by_sub ]#########################

    #########################[ start get_system_user ]#########################
    @staticmethod
    def get_system_user() -> Optional[RecipezUserModel]:
        """
        Get the system user based on the system user name in the Flask configuration.

        Returns:
            Optional[RecipezUserModel]: The system user object if found, None otherwise.
        """
        from flask import current_app

        system_user_name = current_app.config.get("RECIPEZ_SYSTEM_USER_NAME")
        if system_user_name:
            return UserRepository.get_user_by_username(system_user_name)
        return None

    #########################[ end get_system_user ]#########################

    #########################[ start get_user_by_email_hmac ]#########################
    @staticmethod
    def get_user_by_email_hmac(user_email_hmac: str) -> Optional[RecipezUserModel]:
        """
        Get a user by their email HMAC.

        Args:
            user_email_hmac (str): The email HMAC of the user to retrieve.

        Returns:
            Optional[RecipezUserModel]: The user object if found, None otherwise.
        """
        return (
            sqla_db.session.query(RecipezUserModel)
            .filter_by(user_email_hmac=user_email_hmac)
            .first()
        )

    #########################[ end get_user_by_email_hmac ]#########################

    #########################[ start update_user_name ]#########################
    @staticmethod
    def update_user_name(user_id: str, new_user_name: str) -> bool:
        """
        Update a user's username.

        Args:
            user_id (str): The ID of the user to update.
            new_user_name (str): The new username.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        user = UserRepository.get_user_by_id(user_id)
        if user:
            user.user_name = new_user_name
            sqla_db.session.commit()
            return True
        return False

    #########################[ end update_user_name ]#########################

    #########################[ start update_user_email ]#########################
    @staticmethod
    def update_user_email(user_id: str, new_user_email: str) -> bool:
        """
        Update a user's email.

        Args:
            user_id (str): The ID of the user to update.
            new_user_email (str): The new email.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        user = UserRepository.get_user_by_id(user_id)
        if user:
            user.user_email = new_user_email
            sqla_db.session.commit()
            return True
        return False

    #########################[ end update_user_email ]#########################

    #########################[ start delete_user ]#########################
    @staticmethod
    def delete_user(user_id: str) -> bool:
        """
        Delete a user from the database.

        Args:
            user_id (str): The ID of the user to delete.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        user = UserRepository.get_user_by_id(user_id)
        if user:
            sqla_db.session.delete(user)
            sqla_db.session.commit()
            return True
        return False

    #########################[ end delete_user ]#########################

    #########################[ start update_profile_image ]#########################
    @staticmethod
    def update_profile_image(user_id: str, image_url: str) -> bool:
        """Update a user's profile image URL.

        Args:
            user_id (str): The ID of the user to update.
            image_url (str): The new profile image URL.

        Returns:
            bool: True if the update succeeded, False otherwise.
        """
        user = UserRepository.get_user_by_id(user_id)
        if user:
            user.user_profile_image_url = image_url
            sqla_db.session.commit()
            return True
        return False

    #########################[ end update_profile_image ]#########################

    #########################[ start get_all_users ]#########################
    @staticmethod
    def get_all_users() -> List[RecipezUserModel]:
        """
        Get all users from the database.

        Returns:
            List[RecipezUserModel]: A list of all user objects.
        """
        return sqla_db.session.query(RecipezUserModel).all()

    #########################[ end get_all_users ]#########################

    #########################[ start get_users_by_ids ]#########################
    @staticmethod
    def get_users_by_ids(user_ids: List[str]) -> List[RecipezUserModel]:
        """
        Get multiple users by their IDs in a single query.

        Args:
            user_ids (List[str]): List of user IDs to retrieve.

        Returns:
            List[RecipezUserModel]: List of user objects found.
        """
        if not user_ids:
            return []

        return (
            sqla_db.session.query(RecipezUserModel)
            .filter(RecipezUserModel.user_id.in_(user_ids))
            .all()
        )

    #########################[ end get_users_by_ids ]#########################


#####################################[ end UserRepository ]####################################
