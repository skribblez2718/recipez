from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, DateTime, Text, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from recipez.extensions import sqla_db
from recipez.model.mixin import AsDictMixin


###################################[ start RecipezRecipeModel ]###################################
class RecipezRecipeModel(AsDictMixin, sqla_db.Model):
    """Recipe model for storing recipe information.

    Attributes:
        recipe_id (str): Primary key for the recipe.
        recipe_name (str): Name of the recipe, must be unique per author.
        recipe_description (str): Description of the recipe.
        recipe_category_id (str): Foreign key to the category of this recipe.
        recipe_image_id (str): Foreign key to the image of this recipe.
        recipe_author_id (str): Foreign key to the user who created this recipe.
        created_at (datetime): Timestamp when the recipe was created.
        category (relationship): Relationship to the category of this recipe.
        image (relationship): Relationship to the image of this recipe.
        author (relationship): Relationship to the user who created this recipe.
        ingredients (relationship): Relationship to ingredients in this recipe.
        steps (relationship): Relationship to steps in this recipe.
    """

    __tablename__ = "recipez_recipe"
    __table_args__ = (
        UniqueConstraint("recipe_name", "recipe_author_id", name="uq_recipe_name_per_author"),
        {"schema": "recipez"}
    )

    recipe_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    recipe_name = Column(String, nullable=False)
    recipe_description = Column(Text, nullable=False)
    recipe_category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipez.recipez_category.category_id", ondelete="RESTRICT"),
        nullable=False,
    )
    recipe_image_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipez.recipez_image.image_id", ondelete="SET NULL"),
        nullable=True,  # Allow NULL so recipes can use default image when custom image is deleted
    )
    recipe_author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipez.recipez_user.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationships
    category = relationship("RecipezCategoryModel", back_populates="recipes")
    image = relationship("RecipezImageModel", back_populates="recipes")
    author = relationship("RecipezUserModel", back_populates="recipes")
    ingredients = relationship(
        "RecipezIngredientModel", back_populates="recipe", cascade="all, delete-orphan"
    )
    steps = relationship(
        "RecipezStepModel", back_populates="recipe", cascade="all, delete-orphan"
    )


###################################[ end RecipezRecipeModel ]###################################
