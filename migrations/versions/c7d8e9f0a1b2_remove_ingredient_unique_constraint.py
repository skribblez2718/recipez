"""Remove ingredient unique constraint to allow duplicate ingredients

This migration removes the unique constraint on (ingredient_name, ingredient_quantity,
ingredient_measurement, ingredient_recipe_id) from the recipez_ingredient table.

The constraint was causing errors when AI-generated recipes contained duplicate ingredients
(e.g., same ingredient used twice in different parts of a recipe). Each ingredient already
has a unique ingredient_id (UUID) which is sufficient for data integrity.

NOTE: The original constraint was created without an explicit name in the initial migration,
so PostgreSQL auto-generated a truncated name. We use dynamic discovery to find it.

Revision ID: c7d8e9f0a1b2
Revises: b1c2d3e4f5g6
Create Date: 2025-12-14

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c7d8e9f0a1b2"
down_revision = "b1c2d3e4f5g6"
branch_labels = None
depends_on = None

# Short, explicit constraint name for future use (under 63 chars)
CONSTRAINT_NAME = "uq_ingredient_name_qty_meas_recipe"


def upgrade():
    # The original constraint was created without an explicit name, so PostgreSQL
    # auto-generated one. Since the full name would exceed 63 chars, it was truncated.
    # We need to dynamically discover the actual constraint name.
    connection = op.get_bind()

    # Find the unique constraint that covers our columns
    result = connection.execute(sa.text("""
        SELECT con.conname
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        WHERE rel.relname = 'recipez_ingredient'
          AND con.contype = 'u'
          AND nsp.nspname = 'public'
    """))

    constraint_name = result.scalar()

    if constraint_name:
        op.drop_constraint(constraint_name, "recipez_ingredient", type_="unique")
    else:
        # Constraint may have already been dropped or doesn't exist
        print("WARNING: Unique constraint not found on recipez_ingredient - may already be dropped")


def downgrade():
    # Re-add the unique constraint with an explicit short name
    op.create_unique_constraint(
        CONSTRAINT_NAME,
        "recipez_ingredient",
        ["ingredient_name", "ingredient_quantity", "ingredient_measurement", "ingredient_recipe_id"]
    )
