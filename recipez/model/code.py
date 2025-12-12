from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from recipez.extensions import sqla_db


###################################[ start RecipezCodeModel ]###################################
class RecipezCodeModel(sqla_db.Model):
    """Code model for login verification.

    Attributes:
        code_id (str): Primary key for the code.
        code_count (int): Count of code usage.
        code_value (str): Code value, must be unique.
        code_issued_at (datetime): Timestamp when the code was issued.
        code_expires_at (datetime): Timestamp when the code expires.
        code_attempts (int): Number of attempts made with this code.
        code_cooldown (datetime): Cooldown period after failed attempts.
        code_email (str): Email associated with the code.
        code_session_id (str): Session associated with the code.
    """

    __tablename__ = "recipez_code"
    __table_args__ = {"schema": "recipez"}

    code_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    code_count = Column(Integer, nullable=False)
    code_value = Column(String, unique=True, nullable=False)
    code_issued_at = Column(DateTime, default=datetime.now(timezone.utc))
    code_expires_at = Column(DateTime)
    code_attempts = Column(Integer, nullable=False)
    code_cooldown = Column(
        DateTime, nullable=True
    )  # Explicitly allow NULL for cooldown
    code_email = Column(String, nullable=False)
    code_session_id = Column(UUID(as_uuid=True), nullable=False)


###################################[ end RecipezCodeModel ]###################################
