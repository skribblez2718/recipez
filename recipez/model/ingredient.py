from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from recipez.extensions import sqla_db
from recipez.model.mixin import AsDictMixin


###################################[ start RecipezIngredientModel ]###################################
class RecipezIngredientModel(AsDictMixin, sqla_db.Model):
    """Ingredient model for recipe ingredients.

    Attributes:
        ingredient_id (str): Primary key for the ingredient.
        ingredient_name (str): Name of the ingredient.
        ingredient_quantity (str): Quantity of the ingredient.
        ingredient_measurement (str): Measurement unit of the ingredient.
        ingredient_author_id (str): Foreign key to the user who created this ingredient.
        ingredient_recipe_id (str): Foreign key to the recipe this ingredient belongs to.
        created_at (datetime): Timestamp when the ingredient was created.
        author (relationship): Relationship to the user who created this ingredient.
        recipe (relationship): Relationship to the recipe this ingredient belongs to.
    """

    __tablename__ = "recipez_ingredient"
    __table_args__ = {"schema": "recipez"}

    ingredient_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ingredient_name = Column(String, nullable=False)
    ingredient_quantity = Column(String, nullable=False)
    ingredient_measurement = Column(String, nullable=False)
    ingredient_author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipez.recipez_user.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    ingredient_recipe_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipez.recipez_recipe.recipe_id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationships
    author = relationship("RecipezUserModel", back_populates="ingredients")
    recipe = relationship("RecipezRecipeModel", back_populates="ingredients")


###################################[ end RecipezIngredientModel ]###################################
