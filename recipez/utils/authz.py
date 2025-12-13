from typing import Callable, Any, Dict, Union
from flask import (
    current_app,
    request,
    g,
    jsonify,
    session,
    flash,
    redirect,
    url_for,
)
from functools import wraps
from uuid import UUID

from recipez.repository import (
    CategoryRepository,
    RecipeRepository,
    IngredientRepository,
    StepRepository,
    ImageRepository,
)

from werkzeug.wrappers import Response as WerkzeugResponse


NOT_AUTHORIZED_MESSAGE = "You are not authorized to take this action"
INVALID_TOKEN_MESSAGE = "Invalid or expired token"
INSUFFICIENT_SCOPE_MESSAGE = "Insufficient permissions for this operation"


###################################[ start RecipezAuthZUtils ]###################################
class RecipezAuthZUtils:
    """
    A class to handle authorization functionalities for the Recipez application.

    This class provides static methods to enforce access control policies,
    such as ownership verification, API key validation, and scope checking.
    """

    #########################[ start _is_api_request ]#########################
    @staticmethod
    def _is_api_request() -> bool:
        """
        Determines if the current Flask request is an API request.
        Returns:
            bool: True if the request is for an API endpoint or prefers JSON, False otherwise.
        """
        if (
            request.accept_mimetypes.accept_json
            and not request.accept_mimetypes.accept_html
        ):
            return True
        if request.path.startswith("/api"):
            return True
        return False

    #########################[ end _is_api_request ]#########################

    #########################[ start scope_required ]#######################
    @staticmethod
    def scope_required(
        required_scope: str,
    ) -> Callable[..., Callable[..., WerkzeugResponse]]:
        """
        Decorator factory to ensure that the request has the required scope.

        This decorator checks if the required scope is in the list of scopes
        extracted from the JWT token. It should be applied after the jwt_required decorator.

        Args:
            required_scope (str): The scope required for the operation.

        Returns:
            Callable[..., Callable[..., WerkzeugResponse]]: A decorator that enforces scope validation.
        """

        #########################[ start decorator ]#########################
        def decorator(
            view_func: Callable[..., WerkzeugResponse]
        ) -> Callable[..., WerkzeugResponse]:
            @wraps(view_func)
            def wrapper(*args: Any, **kwargs: Any) -> WerkzeugResponse:
                """
                Decorator to ensure that the request has the required scope.

                Args:
                    view_func (Callable[..., WerkzeugResponse]): The view function to protect.

                Returns:
                    Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
                """
                error_msg = "Forbidden"
                # Helper to determine if request is API or view
                if not hasattr(g, "jwt_scopes"):
                    if RecipezAuthZUtils._is_api_request():
                        return (
                            jsonify(
                                {
                                    "error": error_msg,
                                    "details": "JWT validation not performed",
                                }
                            ),
                            401,
                        )
                    else:
                        flash("You must be logged in to access this page.", "danger")
                        # Use next param for redirect if available
                        next_url = (
                            request.url
                            if request.method == "GET"
                            else url_for("index.index_view")
                        )
                        return redirect(url_for("auth.login_email_view", next=next_url))

                # Check if the required scope is in the list of scopes
                if required_scope not in g.jwt_scopes:
                    if RecipezAuthZUtils._is_api_request():
                        return (
                            jsonify(
                                {
                                    "error": error_msg,
                                    "details": f"Missing required scope: {required_scope}",
                                }
                            ),
                            403,
                        )
                    else:
                        flash(
                            "You do not have permission to perform this action.",
                            "danger",
                        )
                        return redirect(request.referrer or url_for("index.index_view"))

                # All validations passed, proceed with the view function
                return view_func(*args, **kwargs)

            return wrapper

        #########################[ end decorator ]#########################

        return decorator

    #########################[ end scope_required ]#########################

    #########################[ start category_create_required ]#################
    @staticmethod
    def category_create_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'category:create' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("category:create")(view_func)

    #########################[ end category_create_required ]###################

    #########################[ start category_read_required ]##################
    @staticmethod
    def category_read_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'category:read' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("category:read")(view_func)

    #########################[ end category_read_required ]####################

    #########################[ start category_update_required ]################
    @staticmethod
    def category_update_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'category:update' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("category:update")(view_func)

    #########################[ end category_update_required ]##################

    #########################[ start category_delete_required ]################
    @staticmethod
    def category_delete_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'category:delete' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("category:delete")(view_func)

    #########################[ end category_delete_required ]##################

    #########################[ start code_verify_required ]################
    @staticmethod
    def code_verify_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'code:verify' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("code:verify")(view_func)

    #########################[ end code_verify_required ]##################

    #########################[ start code_create_required ]#################
    @staticmethod
    def code_create_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'code:create' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("code:create")(view_func)

    #########################[ end code_create_required ]###################

    #########################[ start code_read_required ]##################
    @staticmethod
    def code_read_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'code:read' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("code:read")(view_func)

    #########################[ end code_read_required ]####################

    #########################[ start code_update_required ]################
    @staticmethod
    def code_update_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'code:update' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("code:update")(view_func)

    #########################[ end code_update_required ]##################

    #########################[ start code_delete_required ]################
    @staticmethod
    def code_delete_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'code:delete' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("code:delete")(view_func)

    #########################[ end code_delete_required ]##################

    #########################[ start image_create_required ]################
    @staticmethod
    def image_create_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'image:create' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("image:create")(view_func)

    #########################[ end image_create_required ]##################

    #########################[ start image_read_required ]################
    @staticmethod
    def image_read_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'image:create' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("image:read")(view_func)

    #########################[ end image_read_required ]##################

    #########################[ start image_update_required ]################
    @staticmethod
    def image_update_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'image:create' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("image:update")(view_func)

    #########################[ end image_update_required ]##################

    #########################[ start image_delete_required ]################
    @staticmethod
    def image_delete_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'image:create' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("image:delete")(view_func)

    #########################[ end image_delete_required ]##################

    #########################[ start email_code_create_required ]###############
    @staticmethod
    def email_code_create_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'email:code:create' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("email:code:create")(view_func)

    #########################[ end email_code_create_required ]#################

    #########################[ start ingredient_create_required ]#################
    @staticmethod
    def ingredient_create_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'recipe:create' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("ingredient:create")(view_func)

    #########################[ end ingredient_create_required ]###################

    #########################[ start ingredient_read_required ]#################
    @staticmethod
    def ingredient_read_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'ingredient:read' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("ingredient:read")(view_func)

    #########################[ end ingredient_read_required ]###################

    #########################[ start ingedient_update_required ]#################
    @staticmethod
    def ingedient_update_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'ingredient:update' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("ingredient:update")(view_func)

    #########################[ end ingedient_update_required ]###################

    #########################[ start ingredient_delete_required ]#################
    @staticmethod
    def ingredient_delete_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'ingredient:delete' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("ingredient:delete")(view_func)

    #########################[ end ingredient_delete_required ]###################

    #########################[ start recipe_create_required ]#################
    @staticmethod
    def recipe_create_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'recipe:create' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("recipe:create")(view_func)

    #########################[ end recipe_create_required ]###################

    #########################[ start recipe_read_required ]#################
    @staticmethod
    def recipe_read_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'recipe:read' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("recipe:read")(view_func)

    #########################[ end recipe_read_required ]###################

    #########################[ start recipe_update_required ]#################
    @staticmethod
    def recipe_update_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'recipe:update' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("recipe:update")(view_func)

    #########################[ end recipe_update_required ]###################

    #########################[ start recipe_delete_required ]#################
    @staticmethod
    def recipe_delete_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'recipe:delete' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("recipe:delete")(view_func)

    #########################[ end recipe_delete_required ]###################

    #########################[ start step_create_required ]#################
    @staticmethod
    def step_create_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'step:create' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("step:create")(view_func)

    #########################[ end step_create_required ]###################

    #########################[ start step_read_required ]#################
    @staticmethod
    def step_read_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'step:read' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("step:read")(view_func)

    #########################[ end step_read_required ]###################

    #########################[ start step_update_required ]#################
    @staticmethod
    def step_update_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'step:update' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("step:update")(view_func)

    #########################[ end step_update_required ]###################

    #########################[ start step_delete_required ]#################
    @staticmethod
    def step_delete_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator to ensure that the request has the 'step:delete' scope.

        Args:
            view_func (Callable[..., WerkzeugResponse]): The view function to protect.

        Returns:
            Callable[..., WerkzeugResponse]: A wrapped view function enforcing scope validation.
        """
        return RecipezAuthZUtils.scope_required("step:delete")(view_func)

    #########################[ end step_delete_required ]###################

    #########################[ start ai_create_recipe_required ]#################
    @staticmethod
    def ai_create_recipe_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """Decorator for 'ai:create-recipe' scope."""
        return RecipezAuthZUtils.scope_required("ai:create-recipe")(view_func)

    #########################[ end ai_create_recipe_required ]###################

    #########################[ start ai_modify_recipe_required ]#################
    @staticmethod
    def ai_modify_recipe_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """Decorator for 'ai:modify-recipe' scope."""
        return RecipezAuthZUtils.scope_required("ai:modify-recipe")(view_func)

    #########################[ end ai_modify_recipe_required ]###################

    #########################[ start ai_grocery_list_required ]#################
    @staticmethod
    def ai_grocery_list_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """Decorator for 'ai:grocery-list' scope."""
        return RecipezAuthZUtils.scope_required("ai:grocery-list")(view_func)

    #########################[ end ai_grocery_list_required ]###################

    #########################[ start owner_required ]#########################
    @staticmethod
    def owner_required(
        view_func: Callable[..., WerkzeugResponse]
    ) -> Callable[..., WerkzeugResponse]:
        """
        Decorator factory to ensure that the user is the owner of the resource they're trying to modify.
        Args:
            user_attr (str): The attribute of g.user to use as the user ID (default: 'user_id')
        Returns:
            Callable[..., Callable[..., WerkzeugResponse]]: A decorator that enforces ownership check.
        """
        MODEL_NAMES: Set[str] = {
            "recipe",
            "ingredient",
            "step",
            "image",
            "category",
        }

        #########################[ start _extract_model_type ]#########################
        def _extract_model_type(path_parts: list[str]) -> Union[str, None]:
            """Return the first segment that matches a known model name."""
            for part in path_parts:
                if part in MODEL_NAMES:
                    return part
            return None

        #########################[ end _extract_model_type ]#########################

        #########################[ start _extract_resource_id ]#########################
        def _extract_resource_id(
            path_parts: list[str],
            model_type: str,
            route_kwargs: dict[str, Any],
        ) -> Union[str, None]:
            """
            Function to extract the resource ID from the URL.

            Args:
                path_parts (list[str]): The list of path segments.
                model_type (str): The type of the model.
                route_kwargs (dict[str, Any]): The route arguments.

            Returns:
                Union[str, None]: The resource ID or None if not found.
            """
            # Look at Flask’s view-args first
            candidate = route_kwargs.get("pk") or route_kwargs.get(f"{model_type}_id")
            if candidate:
                return candidate

            # Fallback: take the last path segment
            return path_parts[-1] if path_parts else None

        #########################[ end _extract_resource_id ]#########################

        #########################[ start wrapper ]#########################
        @wraps(view_func)
        def wrapper(*args: Any, **kwargs: Any) -> WerkzeugResponse:
            error_msg = "You are not authorized to modify this resource."
            path_parts = request.path.strip("/").split("/")
            model_type = _extract_model_type(path_parts)
            if not model_type:
                current_app.logger.error(f"Invalid model type in path: {request.path}")
                if RecipezAuthZUtils._is_api_request():
                    return jsonify({"response": {"error": error_msg}}), 403
                else:
                    flash("Invalid resource for this operation.", "danger")
                    return redirect(request.referrer or url_for("index.index_view"))

            raw_id = _extract_resource_id(path_parts, model_type, kwargs)
            try:
                resource_id = str(UUID(raw_id))
            except Exception:
                current_app.logger.error(
                    f"Malformed or missing UUID in path: {request.path}"
                )
                if RecipezAuthZUtils._is_api_request():
                    return jsonify({"response": {"error": error_msg}}), 403
                else:
                    flash("Invalid resource identifier.", "danger")
                    return redirect(request.referrer or url_for("index.index_view"))

            user_id = getattr(g.user, "user_id", None) if g.user else None
            if not user_id:
                current_app.logger.error(
                    "User ID not found in g.user for ownership check."
                )
                if RecipezAuthZUtils._is_api_request():
                    return jsonify({"response": {"error": error_msg}}), 403
                else:
                    flash("You must be logged in to perform this action.", "danger")
                    return redirect(url_for("auth.login_email_view", next=request.url))

            query_map: Dict[str, Callable[[str, str], bool]] = {
                "recipe": RecipeRepository.is_recipe_author,
                "ingredient": IngredientRepository.is_ingredient_author,
                "step": StepRepository.is_step_author,
                "image": ImageRepository.is_image_author,
                "category": CategoryRepository.is_category_author,
            }

            is_owner = query_map[model_type](resource_id, user_id)
            if not is_owner:
                current_app.logger.warning(
                    f"User {user_id} is not owner of {model_type} {resource_id}"
                )
                if RecipezAuthZUtils._is_api_request():
                    return jsonify({"response": {"error": error_msg}}), 403
                else:
                    flash(
                        "You do not have permission to modify this resource.", "danger"
                    )
                    return redirect(request.referrer or url_for("index.index_view"))

            return view_func(*args, **kwargs)

        #########################[ end wrapper ]#########################

        return wrapper

    #########################[ end owner_required ]###########################


###################################[ end RecipezAuthZUtils ]####################################
