from typing import Optional
from datetime import datetime, timezone
from recipez import sqla_db
from recipez.model import RecipezCodeModel


####################################[ start CodeRepository ]####################################
class CodeRepository:
    """
    Repository for code-related database operations using SQLAlchemy.

    This class provides methods to interact with the Code model in the database,
    replacing raw SQL queries with SQLAlchemy ORM operations.
    """

    #########################[ start create_code ]#########################
    @staticmethod
    def create_code(
        code_count: int,
        code_value: str,
        code_expires_at: datetime,
        code_attempts: int,
        code_email: str,
        code_session_id: str,
    ) -> RecipezCodeModel:
        """
        Create a new verification code in the database.

        Args:
            code_count (int): Count of code usage.
            code_value (str): Code value, must be unique.
            code_expires_at (datetime): Expiration timestamp for the code.
            code_attempts (int): Number of attempts allowed.
            code_email (str): Email associated with the code.
            code_session_id (UUID): Session associated with the code.

        Returns:
            RecipezCodeModel: The created code object.
        """
        code = RecipezCodeModel(
            code_count=code_count,
            code_value=code_value,
            code_expires_at=code_expires_at,
            code_attempts=code_attempts,
            code_email=code_email,
            code_session_id=code_session_id,
            code_cooldown=None,  # Initially no cooldown
        )
        sqla_db.session.add(code)
        sqla_db.session.commit()
        return code

    #########################[ end create_code ]#########################

    #########################[ start read_code ]#########################
    @staticmethod
    def read_code(email: str, session_id: str) -> Optional[RecipezCodeModel]:
        """
        Get a code by email and session_id.

        Args:
            email (str): The email associated with the code.
            session_id (UUID): The session_id associated with the code.

        Returns:
            Optional[RecipezCodeModel]: The code object if found, None otherwise.
        """
        return (
            sqla_db.session.query(RecipezCodeModel)
            .filter_by(code_email=email, code_session_id=session_id)
            .first()
        )

    #########################[ end read_code ]#########################

    #########################[ start delete_code ]#########################
    @staticmethod
    def delete_code(code_id: str) -> bool:
        """
        Delete a code from the database.

        Args:
            code_id (str): The ID of the code to delete.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        code = (
            sqla_db.session.query(RecipezCodeModel).filter_by(code_id=code_id).first()
        )
        if code:
            sqla_db.session.delete(code)
            sqla_db.session.commit()
            return True
        return False

    #########################[ end delete_code ]#########################

    #########################[ start update_code_count ]#########################
    @staticmethod
    def update_code_count(code_id: str, count: int) -> bool:
        """
        Update the count of a code.

        Args:
            code_id (str): The ID of the code to update.
            count (int): The new count value.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        code = (
            sqla_db.session.query(RecipezCodeModel).filter_by(code_id=code_id).first()
        )
        if code:
            code.code_count = count
            sqla_db.session.commit()
            return True
        return False

    #########################[ end update_code_count ]#########################

    #########################[ start update_code_attempts ]#########################
    @staticmethod
    def update_code_attempts(code_id: str, attempts: int) -> bool:
        """
        Update the attempts of a code.

        Args:
            code_id (str): The ID of the code to update.
            attempts (int): The new attempts value.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        code = (
            sqla_db.session.query(RecipezCodeModel).filter_by(code_id=code_id).first()
        )
        if code:
            code.code_attempts = attempts
            sqla_db.session.commit()
            return True
        return False

    #########################[ end update_code_attempts ]#########################

    #########################[ start update_code_cooldown ]#########################
    @staticmethod
    def update_code_cooldown(code_id: str, cooldown: Optional[datetime] = None) -> bool:
        """
        Update the cooldown of a code.

        Args:
            code_id (str): The ID of the code to update.
            cooldown (Optional[datetime]): The new cooldown timestamp or None to clear cooldown.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        code = (
            sqla_db.session.query(RecipezCodeModel).filter_by(code_id=code_id).first()
        )
        if code:
            code.code_cooldown = cooldown
            sqla_db.session.commit()
            return True
        return False

    #########################[ end update_code_cooldown ]#########################
    #########################[ start reset_code ]###############################
    @staticmethod
    def reset_code(code_id: str, issued_at: datetime, expires_at: datetime) -> bool:
        """Reset send count and expiration when the resend window has passed."""
        code = (
            sqla_db.session.query(RecipezCodeModel).filter_by(code_id=code_id).first()
        )
        if code:
            code.code_count = 1
            code.code_attempts = 0
            code.code_issued_at = issued_at
            code.code_expires_at = expires_at
            code.code_cooldown = None
            sqla_db.session.commit()
            return True
        return False

    #########################[ end reset_code ]###############################
    #########################[ start cleanup_expired_codes ]###################
    @staticmethod
    def cleanup_expired_codes() -> int:
        """Remove all expired codes from the database."""
        try:
            now = datetime.now(timezone.utc)
            count = (
                sqla_db.session.query(RecipezCodeModel)
                .filter(RecipezCodeModel.code_expires_at < now)
                .delete(synchronize_session=False)
            )
            sqla_db.session.commit()
            return count
        except Exception as e:
            from flask import current_app

            current_app.logger.error(f"[CodeRepository] Failed to cleanup codes: {e}")
            sqla_db.session.rollback()
            return 0

    #########################[ end cleanup_expired_codes ]#####################


####################################[ end CodeRepository ]####################################
