from recipez.blueprint.api.category import bp as category_api_bp
from recipez.blueprint.api.code import bp as code_api_bp
from recipez.blueprint.api.email import bp as email_api_bp
from recipez.blueprint.api.image import bp as image_api_bp
from recipez.blueprint.api.ingredient import bp as ingredient_api_bp
from recipez.blueprint.api.recipe import bp as recipe_api_bp
from recipez.blueprint.api.step import bp as step_api_bp
from recipez.blueprint.api.user import bp as user_api_bp
from recipez.blueprint.api.ai import bp as ai_api_bp
from recipez.blueprint.api.profile import bp as profile_api_bp
from recipez.blueprint.api.grocery import bp as grocery_api_bp
from recipez.blueprint.api.health import health_api_bp

__all__ = [
    "category_api_bp",
    "code_api_bp",
    "email_api_bp",
    "image_api_bp",
    "ingredient_api_bp",
    "recipe_api_bp",
    "step_api_bp",
    "user_api_bp",
    "ai_api_bp",
    "profile_api_bp",
    "grocery_api_bp",
    "health_api_bp",
]
