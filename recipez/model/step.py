from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, DateTime, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from recipez.extensions import sqla_db
from recipez.model.mixin import AsDictMixin


###################################[ start RecipezStepModel ]###################################
class RecipezStepModel(sqla_db.Model, AsDictMixin):
    """Step model for recipe steps.

    Attributes:
        step_id (str): Primary key for the step.
        step_text (str): Text of the step.
        step_author_id (str): Foreign key to the user who created this step.
        step_recipe_id (str): Foreign key to the recipe this step belongs to.
        created_at (datetime): Timestamp when the step was created.
        author (relationship): Relationship to the user who created this step.
        recipe (relationship): Relationship to the recipe this step belongs to.
    """

    __tablename__ = "recipez_step"
    __table_args__ = {"schema": "recipez"}

    step_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    step_text = Column(Text, nullable=False)
    step_author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipez.recipez_user.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    step_recipe_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipez.recipez_recipe.recipe_id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationships
    author = relationship("RecipezUserModel", back_populates="steps")
    recipe = relationship("RecipezRecipeModel", back_populates="steps")


###################################[ end RecipezStepModel ]###################################
