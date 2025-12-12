from typing import Optional, Dict, Any
from datetime import datetime, timezone
from flask import current_app
from recipez.extensions import sqla_db
from recipez.model.session import RecipezSessionModel


###################################[ start SessionRepository ]###################################
class SessionRepository:
    """
    Repository for managing Flask-Session data via SQLAlchemy ORM,
    using the RecipezSessionModel with UUID-based session IDs.
    """

    #########################[ start get_session ]#########################
    @staticmethod
    def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a session from the database by its UUID-based session ID.

        Args:
            session_id (UUID): The session UUID (as string).

        Returns:
            Optional[Dict[str, Any]]: The session record as a dict, or None.
        """
        try:
            session_obj = sqla_db.session.get(RecipezSessionModel, session_id)
            if not session_obj:
                return None

            return {
                "id": str(session_obj.id),
                "session_id": session_obj.session_id,
                "data": session_obj.data,
                "expiry": session_obj.expiry,
            }

        except Exception as e:
            current_app.logger.error(
                f"[SessionRepository] Failed to retrieve session {session_id}: {e}"
            )
            return None

    #########################[ end get_session ]###########################

    #########################[ start set_session ]#########################
    @staticmethod
    def set_session(
        session_id: str, data: bytes, expiry: Optional[datetime] = None
    ) -> bool:
        """
        Create or update a session in the database.

        Args:
            session_id (UUID): UUID string used as the session's primary key.
            data (bytes): Serialized session payload.
            expiry (datetime, optional): Expiry timestamp.

        Returns:
            bool: True if operation succeeds, False otherwise.
        """
        try:
            session_obj = sqla_db.session.get(RecipezSessionModel, session_id)

            if session_obj:
                session_obj.data = data
                session_obj.expiry = expiry
            else:
                session_obj = RecipezSessionModel(
                    id=session_id, data=data, expiry=expiry
                )
                sqla_db.session.add(session_obj)

            sqla_db.session.commit()
            return True

        except Exception as e:
            current_app.logger.error(
                f"[SessionRepository] Failed to set session {session_id}: {e}"
            )
            sqla_db.session.rollback()
            return False

    #########################[ end set_session ]###########################

    #########################[ start delete_session ]######################
    @staticmethod
    def delete_session(session_id: str) -> bool:
        """
        Delete a session by its UUID session ID.

        Args:
            session_id (UUID): UUID session ID as string.

        Returns:
            bool: True if deleted, False otherwise.
        """
        try:
            session_obj = sqla_db.session.get(RecipezSessionModel, session_id)
            if not session_obj:
                return False

            sqla_db.session.delete(session_obj)
            sqla_db.session.commit()
            return True

        except Exception as e:
            current_app.logger.error(
                f"[SessionRepository] Failed to delete session {session_id}: {e}"
            )
            sqla_db.session.rollback()
            return False

    #########################[ end delete_session ]########################

    #########################[ start cleanup_expired_sessions ]################
    @staticmethod
    def cleanup_expired_sessions() -> int:
        """
        Remove all expired sessions from the database.

        Returns:
            int: Number of sessions deleted.
        """
        try:
            now = datetime.now(timezone.utc)
            count = (
                sqla_db.session.query(RecipezSessionModel)
                .filter(RecipezSessionModel.expiry < now)
                .delete(synchronize_session=False)
            )

            sqla_db.session.commit()
            return count

        except Exception as e:
            current_app.logger.error(
                f"[SessionRepository] Failed to cleanup sessions: {e}"
            )
            sqla_db.session.rollback()
            return 0

    #########################[ end cleanup_expired_sessions ]##################


###################################[ end SessionRepository ]###################################
