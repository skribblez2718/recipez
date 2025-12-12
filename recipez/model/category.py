from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from recipez.extensions import sqla_db
from recipez.model.mixin import AsDictMixin


###################################[ start Category ]###################################
class RecipezCategoryModel(AsDictMixin, sqla_db.Model):
    """Category model for recipe categorization.

    Attributes:
        category_id (str): Primary key for the category.
        category_name (str): Name of the category, must be unique.
        category_author_id (str): Foreign key to the user who created this category.
        created_at (datetime): Timestamp when the category was created.
        author (relationship): Relationship to the user who created this category.
        recipes (relationship): Relationship to recipes in this category.
    """

    __tablename__ = "recipez_category"
    __table_args__ = {"schema": "recipez"}

    category_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    category_name = Column(String, unique=True, nullable=False)
    category_author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipez.recipez_user.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationships
    author = relationship("RecipezUserModel", back_populates="categories")
    recipes = relationship(
        "RecipezRecipeModel", back_populates="category", cascade="all, delete-orphan"
    )


###################################[ end RecipezCategoryModel ]###################################
