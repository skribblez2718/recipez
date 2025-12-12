from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Text, String, JSON, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from recipez.extensions import sqla_db
from recipez.model.mixin import AsDictMixin


###################################[ start RecipezApiKeyModel ]###################################
class RecipezApiKeyModel(AsDictMixin, sqla_db.Model):
    """API Key model for managing user-generated API keys.

    Attributes:
        api_key_id (UUID): Primary key UUID.
        api_key_user_id (UUID): Foreign key to recipez_user.
        api_key_name (str): User-provided name for the key.
        api_key_hash (str): HMAC hash of the JWT for revocation lookup.
        api_key_scopes (list): JSON array of selected scopes.
        api_key_expires_at (datetime): Expiration timestamp (null = never).
        api_key_created_at (datetime): Creation timestamp.
        api_key_revoked_at (datetime): Revocation timestamp (null = not revoked).
    """

    __tablename__ = "recipez_api_key"
    __table_args__ = {"schema": "recipez"}

    api_key_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    api_key_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipez.recipez_user.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    api_key_name = Column(Text, nullable=False)
    api_key_hash = Column(String(128), nullable=False, unique=True, index=True)
    api_key_scopes = Column(JSON, nullable=False)
    api_key_expires_at = Column(DateTime(timezone=True), nullable=True)
    api_key_created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )
    api_key_revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    author = relationship("RecipezUserModel", backref="api_keys")

    def as_dict(self) -> dict:
        """Return safe API key metadata (never the hash).

        Overrides the AsDictMixin.as_dict() method to expose only
        safe fields that can be shared publicly via the API.

        Returns:
            dict: Dictionary containing only safe API key fields.
        """
        now = datetime.now(timezone.utc)
        return {
            "api_key_id": str(self.api_key_id),
            "api_key_name": self.api_key_name,
            "api_key_scopes": self.api_key_scopes,
            "api_key_expires_at": (
                self.api_key_expires_at.isoformat() if self.api_key_expires_at else None
            ),
            "api_key_created_at": (
                self.api_key_created_at.isoformat() if self.api_key_created_at else None
            ),
            "is_expired": (
                self.api_key_expires_at is not None
                and self.api_key_expires_at < now
            ),
        }


###################################[ end RecipezApiKeyModel ]###################################
