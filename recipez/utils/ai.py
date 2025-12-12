from flask import current_app
from typing import Dict, Union, List, Any
import json
import re
import bleach
from recipez.utils.api import RecipezAPIUtils
from recipez.utils.error import RecipezErrorUtils
from recipez.schema import AICreateRecipeSchema, AIModifyRecipeSchema


class RecipezAIUtils:
    """Utility functions for AI operations."""

    # Security constants for input validation and sanitization
    MAX_INGREDIENTS = 50
    MAX_STEPS = 30
    MAX_RESPONSE_SIZE = 51200  # 50KB in bytes

    ALLOWED_MEASUREMENTS = {
        'cup', 'cups', 'tbsp', 'tablespoon', 'tablespoons',
        'tsp', 'teaspoon', 'teaspoons', 'oz', 'ounce', 'ounces',
        'lb', 'pound', 'pounds', 'g', 'gram', 'grams',
        'kg', 'kilogram', 'kilograms', 'ml', 'milliliter', 'milliliters',
        'l', 'liter', 'liters', 'pinch', 'dash', 'clove', 'cloves'
    }

    @staticmethod
    def _sanitize_text(text: str, max_length: int = 500) -> str:
        """
        Sanitize text from LLM to prevent XSS attacks.

        Removes all HTML tags and attributes, limits length to prevent
        session storage exhaustion and DoS attacks.

        Args:
            text: Text to sanitize (from untrusted LLM output)
            max_length: Maximum allowed length for sanitized text

        Returns:
            Sanitized text with HTML stripped and length limited

        Example:
            >>> RecipezAIUtils._sanitize_text("<script>alert('xss')</script>")
            "alert('xss')"
            >>> RecipezAIUtils._sanitize_text("a" * 600, max_length=500)
            # Returns 500 'a' characters
        """
        if not text or not isinstance(text, str):
            return ""

        # Strip all HTML tags and attributes using bleach
        clean = bleach.clean(text, tags=[], attributes={}, strip=True)

        # Truncate to max length
        return clean[:max_length].strip()

    @staticmethod
    def _sanitize_ingredient_dict(ing: Dict[str, Any]) -> Dict[str, str]:
        """
        Sanitize ingredient dictionary from LLM output.

        Validates and sanitizes all fields in an ingredient dictionary,
        including quantity, measurement, and name. Prevents XSS attacks
        through ingredient data.

        Args:
            ing: Ingredient dictionary with quantity, measurement, name keys

        Returns:
            Sanitized ingredient dictionary with all HTML stripped

        Example:
            >>> ing = {"quantity": "2", "measurement": "cups", "name": "<script>flour</script>"}
            >>> RecipezAIUtils._sanitize_ingredient_dict(ing)
            {"quantity": "2", "measurement": "cups", "name": "flour"}
        """
        return {
            "quantity": RecipezAIUtils._sanitize_text(str(ing.get("quantity", "")), max_length=20),
            "measurement": str(ing.get("measurement", "")).lower().strip()[:50],
            "name": RecipezAIUtils._sanitize_text(str(ing.get("name", "")), max_length=200)
        }

    @staticmethod
    def create_recipe(authorization: str, request: "Request", message: str) -> Dict:
        name = "ai.create_recipe"
        response_msg = "Failed to generate recipe"
        try:
            data = AICreateRecipeSchema(message=message)
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)
        try:
            response = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/ai/create",
                json={"message": data.message},
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            response = RecipezErrorUtils.handle_util_error(name, request, e, response_msg)
        if not response or "error" in response:
            err = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(name, request, err, response_msg)
        return response

    @staticmethod
    def modify_recipe(
        authorization: str, request: "Request", recipe_id: str, message: str
    ) -> Dict:
        name = "ai.modify_recipe"
        response_msg = "Failed to modify recipe"
        try:
            data = AIModifyRecipeSchema(recipe_id=recipe_id, message=message)
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)
        try:
            response = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/ai/modify",
                json={"recipe_id": str(data.recipe_id), "message": data.message},
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            response = RecipezErrorUtils.handle_util_error(name, request, e, response_msg)
        if not response or "error" in response:
            err = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(name, request, err, response_msg)
        return response

    @staticmethod
    def parse_recipe_response(response_text: str) -> Dict[str, Any]:
        """
        Parse AI recipe response from either JSON or markdown format.

        Extracts recipe name, ingredients, steps, and description from LLM responses.
        Handles multiple formats: JSON, markdown with headers, or plain text.
        Sanitizes all output to prevent XSS attacks and enforces size limits.

        Args:
            response_text: Raw response text from LLM

        Returns:
            Dict with keys:
                - name (str): Recipe name (sanitized)
                - ingredients (List[Dict]): List of ingredient dicts (sanitized, limited to MAX_INGREDIENTS)
                - steps (List[str]): List of step descriptions (sanitized, limited to MAX_STEPS)
                - description (str): Recipe description (sanitized)
                - parsing_errors (List[str]): List of parsing errors encountered

        Example:
            >>> response = "# Chocolate Chip Cookies\\n\\n..."
            >>> parsed = RecipezAIUtils.parse_recipe_response(response)
            >>> parsed['name']
            'Chocolate Chip Cookies'
        """
        result = {
            "name": "Untitled Recipe",
            "description": "",
            "ingredients": [],
            "steps": [],
            "parsing_errors": []
        }

        if not response_text or not isinstance(response_text, str):
            current_app.logger.warning("Empty or invalid response text provided to parse_recipe_response")
            return result

        # Validate response size to prevent DoS
        if len(response_text) > RecipezAIUtils.MAX_RESPONSE_SIZE:
            current_app.logger.warning(
                f"AI response too large: {len(response_text)} bytes, truncating to {RecipezAIUtils.MAX_RESPONSE_SIZE}"
            )
            response_text = response_text[:RecipezAIUtils.MAX_RESPONSE_SIZE]
            result["parsing_errors"].append("Response truncated due to size limit")

        # Clean up response text
        response_text = response_text.strip()

        # Try parsing as JSON first
        try:
            json_data = json.loads(response_text)
            if isinstance(json_data, dict):
                # Validate and sanitize name
                name = json_data.get("name", result["name"])
                if isinstance(name, str):
                    result["name"] = RecipezAIUtils._sanitize_text(name, max_length=100)
                else:
                    current_app.logger.warning(f"Invalid name type in JSON: {type(name)}, using default")
                    result["parsing_errors"].append(f"Invalid name type: {type(name).__name__}")

                # Validate and sanitize description
                desc = json_data.get("description", "")
                if isinstance(desc, str):
                    result["description"] = RecipezAIUtils._sanitize_text(desc, max_length=500)
                elif desc:
                    result["description"] = RecipezAIUtils._sanitize_text(str(desc), max_length=500)
                    result["parsing_errors"].append("Description was not a string, converted")

                # Validate and sanitize ingredients array
                ings = json_data.get("ingredients", [])
                if isinstance(ings, list):
                    result["ingredients"] = [
                        RecipezAIUtils._sanitize_ingredient_dict(ing)
                        for ing in ings[:RecipezAIUtils.MAX_INGREDIENTS]
                        if isinstance(ing, dict)
                    ]
                    if len(ings) > RecipezAIUtils.MAX_INGREDIENTS:
                        current_app.logger.warning(
                            f"Truncating ingredients from {len(ings)} to {RecipezAIUtils.MAX_INGREDIENTS}"
                        )
                        result["parsing_errors"].append(f"Ingredients truncated to {RecipezAIUtils.MAX_INGREDIENTS}")
                else:
                    current_app.logger.warning(f"Invalid ingredients type in JSON: {type(ings)}")
                    result["parsing_errors"].append(f"Invalid ingredients type: {type(ings).__name__}")

                # Validate and sanitize steps array
                steps = json_data.get("steps", [])
                if isinstance(steps, list):
                    result["steps"] = [
                        RecipezAIUtils._sanitize_text(str(step), max_length=500)
                        for step in steps[:RecipezAIUtils.MAX_STEPS]
                        if step
                    ]
                    if len(steps) > RecipezAIUtils.MAX_STEPS:
                        current_app.logger.warning(
                            f"Truncating steps from {len(steps)} to {RecipezAIUtils.MAX_STEPS}"
                        )
                        result["parsing_errors"].append(f"Steps truncated to {RecipezAIUtils.MAX_STEPS}")
                else:
                    current_app.logger.warning(f"Invalid steps type in JSON: {type(steps)}")
                    result["parsing_errors"].append(f"Invalid steps type: {type(steps).__name__}")

                return result
        except (json.JSONDecodeError, ValueError):
            # Not valid JSON, continue with markdown/text parsing
            pass

        # Parse markdown format
        try:
            # Extract recipe name (first heading) and sanitize
            name_match = re.search(r'^#\s+(.+?)$', response_text, re.MULTILINE)
            if name_match:
                result["name"] = RecipezAIUtils._sanitize_text(name_match.group(1), max_length=100)

            # Extract description (text between title and first section) and sanitize
            desc_match = re.search(r'^#\s+.+?\n\n(.+?)(?=\n##|\n###|$)', response_text, re.MULTILINE | re.DOTALL)
            if desc_match:
                result["description"] = RecipezAIUtils._sanitize_text(desc_match.group(1), max_length=500)

            # Extract ingredients section
            ingredients_match = re.search(
                r'##?\s+Ingredients:?\s*\n((?:[-*•]\s+.+?\n?)+)',
                response_text,
                re.MULTILINE | re.IGNORECASE
            )
            if ingredients_match:
                ingredient_lines = re.findall(r'[-*•]\s+(.+)', ingredients_match.group(1))
                for line in ingredient_lines[:RecipezAIUtils.MAX_INGREDIENTS]:
                    # Try to parse quantity, measurement, and name
                    parsed_ing = RecipezAIUtils._parse_ingredient_line(line.strip())
                    result["ingredients"].append(parsed_ing)
                if len(ingredient_lines) > RecipezAIUtils.MAX_INGREDIENTS:
                    current_app.logger.warning(
                        f"Truncating ingredients from {len(ingredient_lines)} to {RecipezAIUtils.MAX_INGREDIENTS}"
                    )

            # Extract steps section and sanitize
            steps_match = re.search(
                r'##?\s+(?:Instructions?|Steps?|Directions?):?\s*\n((?:(?:\d+\.|-)\s+.+?\n?)+)',
                response_text,
                re.MULTILINE | re.IGNORECASE
            )
            if steps_match:
                step_lines = re.findall(r'(?:\d+\.|-)\s+(.+)', steps_match.group(1))
                result["steps"] = [
                    RecipezAIUtils._sanitize_text(step, max_length=500)
                    for step in step_lines
                    if step.strip()
                ][:RecipezAIUtils.MAX_STEPS]

            # Fallback: if no structured format found, try extracting from plain text
            if not result["ingredients"] and not result["steps"]:
                current_app.logger.warning("Could not parse structured recipe format, attempting fallback")
                # Look for lines that look like ingredients (contain numbers/measurements)
                potential_ingredients = re.findall(
                    r'(?:^|\n)(?:[-*•]?\s*)?(\d+(?:/\d+)?\s+(?:cup|tbsp|tsp|oz|lb|g|kg|ml|l)\s+.+?)(?:\n|$)',
                    response_text,
                    re.IGNORECASE
                )
                for ing in potential_ingredients[:10]:  # Limit to first 10
                    parsed_ing = RecipezAIUtils._parse_ingredient_line(ing.strip())
                    result["ingredients"].append(parsed_ing)

        except (AttributeError, IndexError, TypeError) as e:
            current_app.logger.error(f"Error parsing recipe response: {str(e)}")
            result["parsing_errors"].append(f"Parsing error: {type(e).__name__}")
        except Exception as e:
            current_app.logger.error(f"Unexpected error parsing recipe: {str(e)}")
            result["parsing_errors"].append("Unexpected parsing error")

        # Log parsing errors if any occurred
        if result["parsing_errors"]:
            current_app.logger.warning(
                f"Recipe parsed with {len(result['parsing_errors'])} errors: {result['parsing_errors']}"
            )

        return result

    @staticmethod
    def _parse_ingredient_line(line: str) -> Dict[str, str]:
        """
        Parse a single ingredient line into quantity, measurement, and name.

        Sanitizes all fields to prevent XSS attacks and validates measurements
        against a whitelist of allowed values.

        Args:
            line: Ingredient line (e.g., "2 cups flour" or "1/2 tsp salt")

        Returns:
            Dict with keys: quantity, measurement, name (all sanitized)

        Example:
            >>> RecipezAIUtils._parse_ingredient_line("2 cups <script>alert('xss')</script>")
            {"quantity": "2", "measurement": "cups", "name": "alert('xss')"}
        """
        # Pattern: optional number/fraction + optional measurement + name
        pattern = r'^\s*(?:(\d+(?:[/-]\d+)?(?:\.\d+)?)\s+)?(?:(cup|cups|tbsp|tablespoon|tablespoons|tsp|teaspoon|teaspoons|oz|ounce|ounces|lb|pound|pounds|g|gram|grams|kg|kilogram|kilograms|ml|milliliter|milliliters|l|liter|liters|pinch|dash|clove|cloves)\s+)?(.+)$'

        match = re.match(pattern, line, re.IGNORECASE)

        if match:
            quantity = match.group(1) or ""
            measurement = match.group(2) or ""
            name = match.group(3) or line

            # Sanitize all fields
            quantity_clean = RecipezAIUtils._sanitize_text(quantity, max_length=20)
            measurement_clean = measurement.strip().lower()

            # Validate measurement against whitelist
            if measurement_clean and measurement_clean not in RecipezAIUtils.ALLOWED_MEASUREMENTS:
                current_app.logger.warning(f"Invalid measurement detected: {measurement_clean}")
                measurement_clean = ""

            name_clean = RecipezAIUtils._sanitize_text(name, max_length=200)

            return {
                "quantity": quantity_clean,
                "measurement": measurement_clean,
                "name": name_clean
            }
        else:
            # Fallback: entire line is the ingredient name (sanitized)
            return {
                "quantity": "",
                "measurement": "",
                "name": RecipezAIUtils._sanitize_text(line, max_length=200)
            }
