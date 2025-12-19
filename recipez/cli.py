import click
from flask.cli import with_appcontext
from recipez.db import init_db


@click.command("init-sqlalchemy-db")
@with_appcontext
def init_sqlalchemy_db_command():
    """Initialize the database with SQLAlchemy models."""
    init_db()
    click.echo("Initialized the database with SQLAlchemy models.")


def init_app(app):
    """Register CLI commands with the Flask application."""
    app.cli.add_command(init_sqlalchemy_db_command)
