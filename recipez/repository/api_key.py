from typing import Optional, List
from datetime import datetime, timezone
from recipez.extensions import sqla_db
from recipez.model import RecipezApiKeyModel


#####################################[ start ApiKeyRepository ]####################################
class ApiKeyRepository:
    """
    Repository for API Key model database operations using SQLAlchemy.

    This class provides methods to interact with the API Key model in the database,
    supporting create, read, and revoke operations for user-generated API keys.
    """

    #########################[ start create_api_key ]#########################
    @staticmethod
    def create_api_key(
        user_id: str,
        name: str,
        jwt_hash: str,
        scopes: List[str],
        expires_at: Optional[datetime] = None,
    ) -> RecipezApiKeyModel:
        """
        Create a new API key record.

        Args:
            user_id (str): The UUID of the user creating the key.
            name (str): User-provided name for the API key.
            jwt_hash (str): HMAC hash of the JWT token.
            scopes (List[str]): List of scopes for the API key.
            expires_at (Optional[datetime]): Expiration datetime (None = never).

        Returns:
            RecipezApiKeyModel: The created API key object.
        """
        api_key = RecipezApiKeyModel(
            api_key_user_id=user_id,
            api_key_name=name,
            api_key_hash=jwt_hash,
            api_key_scopes=scopes,
            api_key_expires_at=expires_at,
        )
        sqla_db.session.add(api_key)
        sqla_db.session.commit()
        return api_key

    #########################[ end create_api_key ]#########################

    #########################[ start get_api_key_by_id ]#########################
    @staticmethod
    def get_api_key_by_id(api_key_id: str) -> Optional[RecipezApiKeyModel]:
        """
        Get an API key by its ID.

        Args:
            api_key_id (str): The UUID of the API key to retrieve.

        Returns:
            Optional[RecipezApiKeyModel]: The API key object if found, None otherwise.
        """
        return (
            sqla_db.session.query(RecipezApiKeyModel)
            .filter_by(api_key_id=api_key_id)
            .first()
        )

    #########################[ end get_api_key_by_id ]#########################

    #########################[ start get_api_key_by_hash ]#########################
    @staticmethod
    def get_api_key_by_hash(jwt_hash: str) -> Optional[RecipezApiKeyModel]:
        """
        Get an API key by its JWT hash (for revocation check).

        Args:
            jwt_hash (str): The HMAC hash of the JWT token.

        Returns:
            Optional[RecipezApiKeyModel]: The API key object if found, None otherwise.
        """
        return (
            sqla_db.session.query(RecipezApiKeyModel)
            .filter_by(api_key_hash=jwt_hash)
            .first()
        )

    #########################[ end get_api_key_by_hash ]#########################

    #########################[ start get_api_keys_by_user_id ]#########################
    @staticmethod
    def get_api_keys_by_user_id(user_id: str) -> List[RecipezApiKeyModel]:
        """
        Get all API keys for a user.

        Args:
            user_id (str): The UUID of the user.

        Returns:
            List[RecipezApiKeyModel]: List of API key objects for the user.
        """
        return (
            sqla_db.session.query(RecipezApiKeyModel)
            .filter_by(api_key_user_id=user_id)
            .order_by(RecipezApiKeyModel.api_key_created_at.desc())
            .all()
        )

    #########################[ end get_api_keys_by_user_id ]#########################

    #########################[ start delete_api_key ]#########################
    @staticmethod
    def delete_api_key(api_key_id: str, user_id: str) -> bool:
        """
        Delete an API key from the database.

        Args:
            api_key_id (str): The UUID of the API key to delete.
            user_id (str): The UUID of the user (for ownership check).

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        api_key = (
            sqla_db.session.query(RecipezApiKeyModel)
            .filter_by(api_key_id=api_key_id, api_key_user_id=user_id)
            .first()
        )
        if api_key:
            sqla_db.session.delete(api_key)
            sqla_db.session.commit()
            return True
        return False

    #########################[ end delete_api_key ]#########################

    #########################[ start is_api_key_valid ]#########################
    @staticmethod
    def is_api_key_valid(jwt_hash: str) -> bool:
        """
        Check if an API key is valid (exists and not expired).

        Note: Returns True if the hash is NOT found (not a managed API key).
        This allows session JWTs to pass through.

        Args:
            jwt_hash (str): The HMAC hash of the JWT token.

        Returns:
            bool: True if valid or not a managed key, False if expired.
        """
        api_key = ApiKeyRepository.get_api_key_by_hash(jwt_hash)
        if not api_key:
            # Not found = not an API key (could be session JWT)
            return True

        # Check if expired
        if api_key.api_key_expires_at is not None:
            if api_key.api_key_expires_at < datetime.now(timezone.utc):
                return False

        return True

    #########################[ end is_api_key_valid ]#########################

    #########################[ start is_managed_api_key ]#########################
    @staticmethod
    def is_managed_api_key(jwt_hash: str) -> bool:
        """
        Check if a JWT hash is a managed API key (vs session JWT).

        Args:
            jwt_hash (str): The HMAC hash of the JWT token.

        Returns:
            bool: True if this is a managed API key, False otherwise.
        """
        return ApiKeyRepository.get_api_key_by_hash(jwt_hash) is not None

    #########################[ end is_managed_api_key ]#########################


#####################################[ end ApiKeyRepository ]####################################
