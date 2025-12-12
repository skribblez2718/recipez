from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Text, text, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from recipez.extensions import sqla_db
from recipez.model.mixin import AsDictMixin


###################################[ start RecipezUserModel ]###################################
class RecipezUserModel(AsDictMixin, sqla_db.Model):
    """User model representing application users.

    Attributes:
        user_id (str): Primary key for the user.
        user_email (str): User"s email address, must be unique.
        user_name (str): User"s username, must be unique.
        user_created_at (datetime): Timestamp when the user was created.
        recipes (relationship): Relationship to recipes created by this user.
        categories (relationship): Relationship to categories created by this user.
        images (relationship): Relationship to images uploaded by this user.
        ingredients (relationship): Relationship to ingredients created by this user.
        steps (relationship): Relationship to steps created by this user.
    """

    __tablename__ = "recipez_user"
    __table_args__ = {"schema": "recipez"}

    user_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_sub = Column(
        UUID(as_uuid=True), nullable=False, server_default=text("gen_random_uuid()")
    )
    user_email = Column(Text, unique=True, nullable=False)
    user_email_hmac = Column(String(128), nullable=False, unique=True, index=True)
    user_name = Column(Text, unique=True, nullable=False)
    user_created_at = Column(DateTime, default=datetime.now(timezone.utc))
    user_profile_image_url = Column(Text, nullable=True)

    # Relationships
    recipes = relationship(
        "RecipezRecipeModel", back_populates="author", cascade="all, delete-orphan"
    )
    categories = relationship(
        "RecipezCategoryModel", back_populates="author", cascade="all, delete-orphan"
    )
    images = relationship(
        "RecipezImageModel", back_populates="author", cascade="all, delete-orphan"
    )
    ingredients = relationship(
        "RecipezIngredientModel", back_populates="author", cascade="all, delete-orphan"
    )
    steps = relationship(
        "RecipezStepModel", back_populates="author", cascade="all, delete-orphan"
    )

    def as_dict(self) -> dict:
        """Return only safe, public user data.

        Overrides the AsDictMixin.as_dict() method to expose only
        safe fields that can be shared publicly via the API.

        Returns:
            dict: Dictionary containing only safe user fields
        """
        return {
            "user_id": str(self.user_id),
            "user_name": self.user_name,
            "user_profile_image_url": self.user_profile_image_url,
            "user_created_at": self.user_created_at.isoformat() if self.user_created_at else None
        }


###################################[ end RecipezUserModel ]###################################
