from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from recipez.extensions import sqla_db
from recipez.model.mixin import AsDictMixin


###################################[ start Image ]###################################
class RecipezImageModel(AsDictMixin, sqla_db.Model):
    """Image model for recipe images.

    Attributes:
        image_id (str): Primary key for the image.
        image_url (str): URL of the image.
        image_author_id (str): Foreign key to the user who uploaded this image.
        created_at (datetime): Timestamp when the image was uploaded.
        author (relationship): Relationship to the user who uploaded this image.
        recipes (relationship): Relationship to recipes using this image.
    """

    __tablename__ = "recipez_image"
    __table_args__ = {"schema": "recipez"}

    image_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    image_url = Column(String, nullable=False)
    image_author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipez.recipez_user.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationships
    author = relationship("RecipezUserModel", back_populates="images")
    recipes = relationship(
        "RecipezRecipeModel", back_populates="image"
    )


###################################[ end RecipezImageModel ]###################################
