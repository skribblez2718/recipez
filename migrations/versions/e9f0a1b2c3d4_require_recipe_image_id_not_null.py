"""Make recipe_image_id required (NOT NULL) with RESTRICT delete

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2025-12-16 12:00:00.000000

This migration:
1. Ensures all recipes have valid image_id (fixes corrupted 'None' strings)
2. Makes recipe_image_id NOT NULL
3. Changes FK constraint from SET NULL to RESTRICT
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9f0a1b2c3d4'
down_revision = 'd8e9f0a1b2c3'
branch_labels = None
depends_on = None


def upgrade():
    # First, fix any corrupted records (string 'None' instead of actual NULL)
    # and assign default image to recipes without valid image_id
    op.execute("""
        -- Create default image if not exists
        INSERT INTO recipez.recipez_image (image_url, image_author_id)
        SELECT '/static/uploads/default_recipe.png', user_id
        FROM recipez.recipez_user
        WHERE NOT EXISTS (
            SELECT 1 FROM recipez.recipez_image
            WHERE image_url LIKE '%default_recipe%'
        )
        LIMIT 1;

        -- Fix recipes with 'None' string or NULL image_id
        UPDATE recipez.recipez_recipe
        SET recipe_image_id = (
            SELECT image_id FROM recipez.recipez_image
            WHERE image_url LIKE '%default_recipe%' LIMIT 1
        )
        WHERE recipe_image_id IS NULL
           OR recipe_image_id::text = 'None';
    """)

    # Now make the column NOT NULL and update FK constraint
    with op.batch_alter_table('recipez_recipe', schema='recipez') as batch_op:
        # Make column NOT NULL
        batch_op.alter_column('recipe_image_id',
               existing_type=sa.UUID(),
               nullable=False)

        # Update FK constraint from SET NULL to RESTRICT
        batch_op.drop_constraint('recipez_recipe_recipe_image_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'recipez_recipe_recipe_image_id_fkey',
            'recipez_image',
            ['recipe_image_id'],
            ['image_id'],
            referent_schema='recipez',
            ondelete='RESTRICT'
        )


def downgrade():
    with op.batch_alter_table('recipez_recipe', schema='recipez') as batch_op:
        # Make column nullable again
        batch_op.alter_column('recipe_image_id',
               existing_type=sa.UUID(),
               nullable=True)

        # Revert FK constraint to SET NULL
        batch_op.drop_constraint('recipez_recipe_recipe_image_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'recipez_recipe_recipe_image_id_fkey',
            'recipez_image',
            ['recipe_image_id'],
            ['image_id'],
            referent_schema='recipez',
            ondelete='SET NULL'
        )
