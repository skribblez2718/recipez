import click
import shutil

from flask import current_app
from flask.cli import with_appcontext
from pathlib import Path

from recipez.repository import (
    UserRepository,
    CategoryRepository,
)
from recipez.utils import RecipezSecretsUtils


# Seed categories to be created on initialization and synced on startup
SEED_CATEGORIES = [
    "Chinese",
    "Japanese",
    "Thai",
    "Indian",
    "Italian",
    "French",
    "Greek",
    "Mediterranean",
    "Middle Eastern",
    "Korean",
    "Vietnamese",
    "Spanish",
    "American",
    "Barbeque",
    "Cajun",
    "Mexican",
    "Caribbean",
    "German",
    "British",
    "Ethiopian",
    "Moroccan",
    "Brazilian",
    "Peruvian",
    "Hawaiian",
    "Breakfast",
    "Snacks",
    "Salads",
    "Desserts",
    "Cakes",
    "Cookies",
    "Pies",
    "Pastries",
    "Breads",
    "Muffins",
    "Cocktails",
    "Smoothies",
    "Seasonings",
    "Marinades",
    "Dressings",
    "Dog Treats",
]


#########################[ start delete_images ]##########################
def delete_images() -> None:
    """
    Delete all images in the uploads directory to ensure clean initialization.
    """
    uploads_dir = Path(__file__).parent / "static" / "uploads"

    if uploads_dir.exists() and uploads_dir.is_dir():
        # Delete all files in the directory
        for file_path in uploads_dir.glob("*"):
            try:
                if file_path.is_file():
                    file_path.unlink()  # Delete file
                elif file_path.is_dir():
                    shutil.rmtree(file_path)  # Delete directory and its contents
            except Exception as e:
                current_app.logger.error(f"Failed to delete {file_path}: {e}")
    else:
        # Create the directory if it doesn't exist
        uploads_dir.mkdir(parents=True, exist_ok=True)

    current_app.logger.info(f"Cleaned uploads directory: {uploads_dir}")


#########################[ end delete_images ]##########################


#########################[ start init_db ]##########################
def init_db() -> None:
    """
    Initialize/update seed data in the database (idempotent - safe to run multiple times).
    Preserves all existing data. Only adds missing seed data.
    """
    # Ensure uploads directory exists (without deleting existing files)
    uploads_dir = Path(__file__).parent / "static" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Load/update seed data (idempotent - always runs, skips existing data)
    _load_initial_data()


#########################[ end init_db ]##########################


#########################[ start _load_initial_data ]###############
def _load_initial_data() -> None:
    """
    Load/update seed data in the database (idempotent - safe to run multiple times).
    Preserves all existing data. Only adds missing seed data.
    """
    # Get or create the system user
    system_user = UserRepository.get_system_user()
    if not system_user:
        system_user_name = current_app.config["RECIPEZ_SYSTEM_USER_NAME"]
        system_user_email = current_app.config["RECIPEZ_SYSTEM_USER_EMAIL"]
        encrypted_email = RecipezSecretsUtils.encrypt(system_user_email)
        email_hmac = RecipezSecretsUtils.generate_hmac(system_user_email)
        system_user = UserRepository.create_user(
            encrypted_email, email_hmac, system_user_name, "/static/img/default_user.png"
        )
        current_app.logger.info(f"Created system user: {system_user_name}")

    system_user_id = system_user.user_id

    # Get or create the Uncategorized fallback category (already idempotent)
    CategoryRepository.get_or_create_uncategorized(system_user_id)

    # Sync seed categories (adds missing ones only)
    created = CategoryRepository.sync_seed_categories(SEED_CATEGORIES, system_user_id)
    if created > 0:
        current_app.logger.info(f"Created {created} new seed categories")


#########################[ end _load_initial_data ]###############


#########################[ start init_db_command ]##################
@click.command("init-db")
@with_appcontext
def init_db_command() -> None:
    """
    Initialize seed data (idempotent). Preserves all existing data.
    """
    init_db()
    click.echo("Seed data initialized. Existing data preserved.")


#########################[ end init_db_command ]##################


#########################[ start reset_uploads_command ]##################
@click.command("reset-uploads")
@with_appcontext
def reset_uploads_command() -> None:
    """
    Delete all uploaded images. USE WITH CAUTION - destructive operation.
    """
    if click.confirm("This will PERMANENTLY delete all uploaded images. Continue?"):
        delete_images()
        click.echo("Uploads directory cleared.")
    else:
        click.echo("Operation cancelled.")


#########################[ end reset_uploads_command ]##################


#########################[ start get_db_session ]###################
def get_db_session():
    """
    Get the SQLAlchemy database session.

    Returns:
        SQLAlchemy session: The current database session.
    """
    return sqla_db.session


#########################[ start get_db_session ]###################


#########################[ start init_app ]#########################
def init_app(app) -> None:
    """
    Initialize the Flask application with necessary CLI commands.

    Parameters:
        app (Flask): The Flask application instance.
    """
    app.cli.add_command(init_db_command)
    app.cli.add_command(reset_uploads_command)


#########################[ start init_app ]#########################
