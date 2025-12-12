from sqlalchemy import Column, String, LargeBinary, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from recipez.extensions import sqla_db


###################################[ start RecipezSessionModel ]###################################
class RecipezSessionModel(sqla_db.Model):
    """Session model for storing Flask server-side sessions.

    Attributes:
        id (UUID): Primary key used as the unique session identifier (maps to Flask session ID).
        session_id (str): Optional user-defined session reference or alias.
        data (bytes): Serialized session data, typically a pickled dictionary.
        expiry (datetime): Expiration timestamp of the session.
    """

    __tablename__ = "recipez_session"
    __table_args__ = {"schema": "recipez"}

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    session_id = Column(String(255), nullable=True)
    data = Column(LargeBinary, nullable=False)
    expiry = Column(DateTime(timezone=True), nullable=False)


###################################[ end RecipezSessionModel ]###################################
