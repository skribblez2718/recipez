from recipez.blueprint.api import (
    category_api_bp,
    code_api_bp,
    image_api_bp,
    email_api_bp,
    ingredient_api_bp,
    recipe_api_bp,
    step_api_bp,
    user_api_bp,
    ai_api_bp,
    profile_api_bp,
    grocery_api_bp,
    health_api_bp,
)
from recipez.blueprint.view import (
    ai_view_bp,
    login_view_bp,
    category_view_bp,
    index_view_bp,
    recipe_view_bp,
    profile_view_bp,
)


#########################[ start register_blueprints ]#########################
def register_blueprints(app):
    """
    Register all blueprints with the Flask application.

    Parameters:
        app (Flask): The Flask application instance.
    """
    # API Blueprints
    app.register_blueprint(category_api_bp)
    app.register_blueprint(code_api_bp)
    app.register_blueprint(image_api_bp)
    app.register_blueprint(email_api_bp)
    app.register_blueprint(ingredient_api_bp)
    app.register_blueprint(recipe_api_bp)
    app.register_blueprint(step_api_bp)
    app.register_blueprint(user_api_bp)
    app.register_blueprint(ai_api_bp)
    app.register_blueprint(profile_api_bp)
    app.register_blueprint(grocery_api_bp)
    app.register_blueprint(health_api_bp)

    # View Blueprints
    app.register_blueprint(ai_view_bp)
    app.register_blueprint(login_view_bp)
    app.register_blueprint(category_view_bp)
    app.register_blueprint(index_view_bp)
    app.register_blueprint(recipe_view_bp)
    app.register_blueprint(profile_view_bp)


#########################[ start register_blueprints ]#########################
