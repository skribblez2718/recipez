from datetime import datetime, timezone
from typing import Optional, Dict, Any
import uuid

from flask import Flask, current_app
from flask.sessions import SessionMixin
from flask_session.base import ServerSideSession
from flask_session.sqlalchemy import SqlAlchemySessionInterface
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.datastructures import CallbackDict
from datetime import timedelta as TimeDelta

# Import the RecipezSessionModel directly to ensure we're using the correct model
from recipez.model.session import RecipezSessionModel


class UUIDSqlAlchemySessionInterface(SqlAlchemySessionInterface):
    has_same_site_capability = True
    """
    Custom SQLAlchemy session interface that uses UUID4 session IDs with the RecipezSessionModel.
    This interface properly handles UUID-based session IDs for both generation and storage.
    
    This implementation bypasses the default Flask-Session table creation and uses the RecipezSessionModel directly,
    ensuring that UUID primary keys are properly handled.
    """

    def __init__(self, app, db, table_name, key_prefix):
        self.sql_session_model = RecipezSessionModel  # ⬅️ FORCE custom model
        self.app = app
        self.db = db
        self.serializer = (
            app.session_interface.serializer
            if hasattr(app.session_interface, "serializer")
            else None
        )
        self.permanent = app.permanent_session_lifetime.total_seconds() > 0
        self.use_signer = app.config.get("SESSION_USE_SIGNER", False)
        self.key_prefix = key_prefix
        self.session_class = ServerSideSession
        self.client = db

    def generate_sid(self) -> str:
        """
        Generate a UUID4 session ID as a string.

        Returns:
            str: A UUID4 string to use as the session ID.
        """
        return str(uuid.uuid4())

    def _get_store_id(self, sid: str) -> str:
        """
        Get the store ID for a session ID.
        This is overridden to handle the case where we're using UUIDs as session IDs.

        Args:
            sid (str): The session ID.

        Returns:
            str: The session ID to use for storage (without prefix).
        """
        # For UUID-based sessions, we don't use a prefix in the database
        # We just return the sid directly
        return sid

    def _retrieve_session_data(self, store_id: str) -> Optional[dict]:
        """
        Get the saved session from the database using the UUID-based store_id.

        Args:
            store_id (str): The session ID to retrieve.

        Returns:
            Optional[dict]: The session data if found, None otherwise.
        """
        # Get the saved session (record) from the database using the UUID
        try:
            # Use a direct query with the RecipezSessionModel to ensure correct table and column types
            stmt = select(RecipezSessionModel).where(RecipezSessionModel.id == store_id)
            record = self.client.session.execute(stmt).scalar_one_or_none()
        except Exception as e:
            self.app.logger.error(f"Error retrieving session {store_id}: {e}")
            return None

        # Delete the session record if it is expired
        # Use timezone-aware UTC datetime for comparison with timezone-aware expiry
        now = datetime.now(timezone.utc)
        if record and (record.expiry is None or record.expiry <= now):
            try:
                self.client.session.delete(record)
                self.client.session.commit()
            except Exception as e:
                self.app.logger.error(f"Error deleting expired session {store_id}: {e}")
                self.client.session.rollback()
                raise
            record = None

        if record:
            try:
                serialized_session_data = record.data
                if isinstance(serialized_session_data, bytes):
                    serialized_session_data = serialized_session_data.decode("utf-8")
                return self.serializer.loads(serialized_session_data)
            except Exception as e:
                self.app.logger.error(
                    f"Error deserializing session data for {store_id}: {e}"
                )
                return None
        return None

    def _delete_session(self, store_id: str) -> None:
        """
        Delete session from the database using the UUID-based store_id.

        Args:
            store_id (str): The session ID to delete.
        """
        try:
            # Use a direct query with the RecipezSessionModel to ensure correct table and column types
            stmt = delete(RecipezSessionModel).where(RecipezSessionModel.id == store_id)
            self.client.session.execute(stmt)
            self.client.session.commit()
        except Exception as e:
            self.app.logger.error(f"Error deleting session {store_id}: {e}")
            self.client.session.rollback()
            raise

    def _upsert_session(
        self, session_lifetime: TimeDelta, session: ServerSideSession, store_id: str
    ) -> None:
        """
        Update existing or create new session in the database using UUID-based store_id.

        Args:
            session_lifetime (TimeDelta): The lifetime of the session.
            session (ServerSideSession): The session object containing the data.
            store_id (str): The session ID to update or create.
        """
        # Use timezone-aware UTC datetime
        storage_expiration_datetime = datetime.now(timezone.utc) + session_lifetime

        # Serialize session data
        try:
            serialized_session_data = self.serializer.dumps(session)
            if isinstance(serialized_session_data, str):
                serialized_session_data = serialized_session_data.encode("utf-8")
        except Exception as e:
            self.app.logger.error(f"Error serializing session data for {store_id}: {e}")
            raise

        # Update existing or create new session in the database
        try:
            # Use a direct query with the RecipezSessionModel to ensure correct table and column types
            stmt = select(RecipezSessionModel).where(RecipezSessionModel.id == store_id)
            record = self.client.session.execute(stmt).scalar_one_or_none()

            if record:
                record.data = serialized_session_data
                record.expiry = storage_expiration_datetime
            else:
                # Create a new session record with the UUID as the primary key
                record = RecipezSessionModel(
                    id=store_id,  # Use the UUID string as the primary key
                    data=serialized_session_data,
                    expiry=storage_expiration_datetime,
                )
                self.client.session.add(record)
            self.client.session.commit()
        except Exception as e:
            self.app.logger.error(f"Error upserting session {store_id}: {e}")
            self.client.session.rollback()
            raise

    def _delete_expired_sessions(self) -> None:
        """
        Delete expired sessions from the database.
        """
        try:
            # Use a direct query with the RecipezSessionModel to ensure correct table and column types
            # Use timezone-aware UTC datetime for comparison with timezone-aware expiry
            stmt = delete(RecipezSessionModel).where(
                RecipezSessionModel.expiry <= datetime.now(timezone.utc)
            )
            self.client.session.execute(stmt)
            self.client.session.commit()
        except Exception as e:
            self.app.logger.error(f"Error deleting expired sessions: {e}")
            self.client.session.rollback()
            raise

    def open_session(self, app: Flask, request) -> ServerSideSession:
        """
        Open a session. If the session doesn't exist, create a new one.
        This is overridden to properly handle UUID-based session IDs.

        Args:
            app (Flask): The Flask application.
            request: The Flask request object.

        Returns:
            ServerSideSession: The session object.
        """
        # Get the session ID from the cookie
        sid = request.cookies.get(app.config["SESSION_COOKIE_NAME"])

        # If there's no session ID, generate a new one
        if not sid:
            sid = self.generate_sid()
            return self.session_class(sid=sid, permanent=self.permanent)

        # If the session ID is signed, unsign it
        if self.use_signer:
            try:
                sid = self._unsign(app, sid)
            except Exception:
                # If the signature is invalid, generate a new session ID
                sid = self.generate_sid()
                return self.session_class(sid=sid, permanent=self.permanent)

        # Retrieve the session data from the database using the UUID directly
        saved_session_data = self._retrieve_session_data(sid)

        # If the saved session exists, load the session data
        if saved_session_data is not None:
            return self.session_class(saved_session_data, sid=sid)

        # If the saved session does not exist, create a new session
        sid = self.generate_sid()
        return self.session_class(sid=sid, permanent=self.permanent)

    def save_session(self, app: Flask, session: ServerSideSession, response) -> None:
        """
        Save the session to the database and set the session cookie.
        This is overridden to properly handle UUID-based session IDs.

        Args:
            app (Flask): The Flask application.
            session (ServerSideSession): The session object.
            response: The Flask response object.
        """
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        name = app.config["SESSION_COOKIE_NAME"]

        # If the session is empty, do not save it to the database or set a cookie
        if not session:
            # If the session was deleted (empty and modified), delete the saved session from the database and tell the client to delete the cookie
            if session.modified:
                self._delete_session(session.sid)
                response.delete_cookie(key=name, domain=domain, path=path)
                response.vary.add("Cookie")
            return

        if not self.should_set_storage(app, session):
            return

        # Update existing or create new session in the database
        self._upsert_session(app.permanent_session_lifetime, session, session.sid)

        if not self.should_set_cookie(app, session):
            return

        # Get the additional required cookie settings
        value = self._sign(app, session.sid) if self.use_signer else session.sid
        expires = self.get_expiration_time(app, session)
        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        samesite = (
            self.get_cookie_samesite(app) if self.has_same_site_capability else None
        )

        # Set the browser cookie
        response.set_cookie(
            key=name,
            value=value,
            expires=expires,
            httponly=httponly,
            domain=domain,
            path=path,
            secure=secure,
            samesite=samesite,
        )
        response.vary.add("Cookie")
