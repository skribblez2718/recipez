import os
import click
from flask import current_app
from flask.cli import with_appcontext
from recipez import sqla_db
from recipez.db import init_db


@click.command("init-sqlalchemy-db")
@with_appcontext
def init_sqlalchemy_db_command():
    """Initialize the database with SQLAlchemy models."""
    init_db()
    click.echo("Initialized the database with SQLAlchemy models.")


@click.command("cleanup-orphaned-images")
@with_appcontext
def cleanup_orphaned_images_command():
    """
    Find and remove orphaned images from database and filesystem.

    Orphaned images are those that exist in the recipez_image table
    but are not referenced by any recipe or user profile.
    """
    from sqlalchemy import text

    click.echo("Scanning for orphaned images...")

    # Get all image IDs from the image table
    all_images_query = text('SELECT image_id, image_url FROM "recipez"."recipez_image"')
    all_images = sqla_db.session.execute(all_images_query).fetchall()

    # Get all recipe image IDs
    recipe_images_query = text(
        'SELECT DISTINCT recipe_image_id FROM "recipez"."recipez_recipe" '
        'WHERE recipe_image_id IS NOT NULL'
    )
    recipe_image_ids = {
        str(row[0]) for row in sqla_db.session.execute(recipe_images_query).fetchall()
    }

    # Get all user profile image URLs (stored directly as URLs, not FK)
    # We need to extract filenames and match against image URLs
    user_images_query = text(
        'SELECT DISTINCT user_profile_image_url FROM "recipez"."recipez_user" '
        'WHERE user_profile_image_url IS NOT NULL'
    )
    user_profile_urls = {
        row[0] for row in sqla_db.session.execute(user_images_query).fetchall()
    }

    # Find image IDs that match user profile URLs
    user_image_ids = set()
    for image_id, image_url in all_images:
        if image_url in user_profile_urls:
            user_image_ids.add(str(image_id))

    # Combine all used image IDs
    used_image_ids = recipe_image_ids | user_image_ids

    # Find orphaned images
    orphaned_images = []
    for image_id, image_url in all_images:
        if str(image_id) not in used_image_ids:
            orphaned_images.append((str(image_id), image_url))

    if not orphaned_images:
        click.echo("No orphaned images found.")
        return

    click.echo(f"Found {len(orphaned_images)} orphaned image(s):")
    for image_id, image_url in orphaned_images:
        click.echo(f"  - {image_id}: {image_url}")

    # Confirm deletion
    if not click.confirm("Do you want to delete these orphaned images?"):
        click.echo("Cleanup cancelled.")
        return

    # Delete orphaned images
    deleted_count = 0
    for image_id, image_url in orphaned_images:
        try:
            # Delete from database
            delete_query = text(
                'DELETE FROM "recipez"."recipez_image" WHERE image_id = :image_id'
            )
            sqla_db.session.execute(delete_query, {"image_id": image_id})

            # Delete file from filesystem (skip default images)
            if image_url and "default_recipe.png" not in image_url and "default_user.png" not in image_url:
                # Handle both /static/uploads/ and /static/img/ paths
                if "/static/uploads/" in image_url:
                    filename = os.path.basename(image_url)
                    file_path = os.path.join(
                        current_app.root_path, "static", "uploads", filename
                    )
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        click.echo(f"  Deleted file: {filename}")

            deleted_count += 1
            click.echo(f"  Deleted DB record: {image_id}")

        except Exception as e:
            click.echo(f"  Error deleting {image_id}: {e}")

    sqla_db.session.commit()
    click.echo(f"\nCleanup complete. Deleted {deleted_count} orphaned image(s).")


def init_app(app):
    """Register CLI commands with the Flask application."""
    app.cli.add_command(init_sqlalchemy_db_command)
    app.cli.add_command(cleanup_orphaned_images_command)
