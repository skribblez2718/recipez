from flask import (
    g,
    session,
    current_app,
)
from typing import List
import uuid


###################################[ start RecipezSessionUtils ]###################################
class RecipezSessionUtils:
    """ """

    #########################[ start load_user ]####################
    @staticmethod
    def load_user() -> None:
        """
        Load the user from the session, verify session exists in DB, and populate g.user.

        Steps:
        1. Ensure the session object has a UUID-based sid (custom interface sets this).
        2. Save that sid to `session["session_id"]` if not already set.
        3. Verify the session is still valid in the DB (using SessionRepository).
        4. If a user_id is present in the session, fetch and assign the user to `g.user`.
        """
        # Initialize user context
        g.user = None

        # Get UUID session ID from the custom interface
        flask_session_id = getattr(session, "sid", None)
        if flask_session_id:
            from recipez.repository import SessionRepository

            # Sync it into session["session_id"] if not already present
            if not session.get("session_id"):
                session_obj = SessionRepository.get_session(flask_session_id)
                if session_obj:
                    session["session_id"] = flask_session_id
                else:
                    # If no session object exists in DB, create one
                    # This ensures the session is properly initialized
                    session["session_id"] = flask_session_id
                    current_app.logger.debug(
                        f"[Session] Initialized session_id from flask_session_id: {flask_session_id}"
                    )
        else:
            # If there's no flask_session_id (shouldn't happen with our interface)
            # but we still need to ensure a valid session_id exists
            if not session.get("session_id"):
                # Generate a new UUID v4 for the session
                new_session_id = str(uuid.uuid4())
                session["session_id"] = new_session_id
                session.permanent = True
                current_app.logger.warning(
                    f"[Session] Generated new session_id as fallback: {new_session_id}"
                )
        # Load user if available
        user_id = session.get("user_id")
        jwt_scopes = session.get("jwt_scopes")
        if user_id:
            try:
                from recipez.repository import UserRepository

                user = UserRepository.get_user_by_id(user_id)
                if user:
                    g.user = user
                else:
                    session.pop("user_id", None)
                    session.pop("user_email", None)
            except Exception as e:
                current_app.logger.error(
                    f"[Session] Error loading user ID {user_id}: {e}"
                )
                session.pop("user_id", None)
                session.pop("user_email", None)
        if jwt_scopes:
            g.jwt_scopes = jwt_scopes

    #########################[ end load_user ]######################

    #########################[ start login_user ]#############################
    @staticmethod
    def login_user(
        user_id: str,
        user_email: str,
        user_jwt: str,
        jwt_scopes: List[str],
        remember: bool = True,
    ) -> None:
        """
        Log in a user by storing their ID and email in the session.

        Args:
            user_id (str): The ID of the user to log in.
            user_email (str): The email of the user to log in.
            user_jwt (str): The JWT token for the user.
            remember (bool): Whether to make the session permanent.
        """
        # Keep the session_id if it exists (important for session continuity)
        existing_session_id = session.get("session_id")
        flask_session_id = getattr(session, "sid", None)

        session.clear()

        # Restore the session_id after clearing
        if existing_session_id:
            session["session_id"] = existing_session_id
        elif flask_session_id:
            session["session_id"] = flask_session_id
        else:
            # Generate a new one if somehow neither exists
            session["session_id"] = str(uuid.uuid4())

        session["user_id"] = user_id
        session["user_email"] = user_email
        session["user_jwt"] = user_jwt
        session["jwt_scopes"] = jwt_scopes
        session.permanent = remember

    #########################[ end login_user ]###############################

    #########################[ start logout_user ]############################
    @staticmethod
    def logout_user() -> None:
        """
        Log out the current user by clearing their session data.
        """
        session.clear()

    #########################[ end logout_user ]##############################

    #########################[ start ensure_session_id ]######################
    @staticmethod
    def ensure_session_id() -> str:
        """
        Ensure a valid session_id exists in the session.

        This method checks for an existing session_id and creates one if needed.
        It prioritizes the Flask session interface's sid, but will generate
        a new UUID v4 if necessary.

        Returns:
            str: The session_id (UUID string)
        """
        # Check if session_id already exists
        session_id = session.get("session_id")
        if session_id:
            return session_id

        # Try to get the flask_session_id from the interface
        flask_session_id = getattr(session, "sid", None)
        if flask_session_id:
            session["session_id"] = flask_session_id
            session.permanent = True
            current_app.logger.debug(
                f"[Session] Ensured session_id from flask interface: {flask_session_id}"
            )
            return flask_session_id

        # Generate a new UUID v4 if nothing exists
        new_session_id = str(uuid.uuid4())
        session["session_id"] = new_session_id
        session.permanent = True
        current_app.logger.warning(
            f"[DEBUG FIX] Generated NEW session_id: {new_session_id}"
        )
        current_app.logger.info(
            f"[Session] Generated new session_id: {new_session_id}"
        )
        return new_session_id

    #########################[ end ensure_session_id ]########################

    #########################[ start cleanup_sessions ]#######################
    @staticmethod
    def cleanup_sessions() -> int:
        """
        Clean up expired sessions from the database.

        Returns:
            int: The number of sessions removed.
        """
        return SessionRepository.cleanup_expired_sessions()

    #########################[ end cleanup_sessions ]#########################


###################################[ end RecipezSessionUtils ]####################################
