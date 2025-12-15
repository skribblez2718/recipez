#!/usr/bin/env python
"""Helper script to generate test user and JWT tokens for API testing."""

import sys
import os
sys.path.insert(0, '/home/user/projects/recipez')

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv('/home/user/projects/recipez/.env')

from recipez import create_app
from recipez.repository import UserRepository, CategoryRepository, ImageRepository
from recipez.utils import RecipezSecretsUtils

app = create_app()

def get_or_create_test_user():
    """Get or create a test user and return user + tokens."""
    with app.app_context():
        # Check for existing test user by email
        email = "apitest@example.com"
        hmac_hash = RecipezSecretsUtils.generate_hmac(email)
        user = UserRepository.get_user_by_email_hmac(hmac_hash)

        if not user:
            # Create new test user
            enc = RecipezSecretsUtils.encrypt(email)
            user = UserRepository.create_user(enc, hmac_hash, "apitest", "/static/img/default_user.png")
            print(f"Created test user: {user.user_id}")
        else:
            print(f"Found existing test user: {user.user_id}")

        # Get all regular user scopes from config
        scopes = app.config.get("RECIPEZ_USER_JWT_SCOPES", [])
        token = RecipezSecretsUtils.generate_jwt(str(user.user_sub), scopes)

        # Also get system user token
        system_jwt = RecipezSecretsUtils.get_valid_system_jwt()

        print(f"\nUser ID: {user.user_id}")
        print(f"User Sub: {user.user_sub}")
        print(f"\n=== USER JWT TOKEN (all scopes) ===")
        print(token)
        print(f"\n=== SYSTEM USER JWT TOKEN ===")
        print(system_jwt if system_jwt else "NOT AVAILABLE")

        return user, token, system_jwt

def get_test_resources():
    """Get or create test resources (category, image)."""
    with app.app_context():
        email = "apitest@example.com"
        hmac_hash = RecipezSecretsUtils.generate_hmac(email)
        user = UserRepository.get_user_by_email_hmac(hmac_hash)

        if not user:
            print("ERROR: Test user not found. Run get_or_create_test_user first.")
            return None

        # Find or create a test category
        categories = CategoryRepository.get_all_categories()
        test_cat = None
        for cat in categories:
            if cat.category_name == "API Test Category":
                test_cat = cat
                break

        if not test_cat:
            test_cat = CategoryRepository.create_category("API Test Category", user.user_id)
            print(f"Created test category: {test_cat.category_id}")
        else:
            print(f"Found existing test category: {test_cat.category_id}")

        # Find or create a test image
        images = ImageRepository.get_all_images()
        test_img = None
        for img in images:
            if img.image_url == "/static/img/default_recipe.png":
                test_img = img
                break

        if not test_img and images:
            test_img = images[0]
            print(f"Using existing image: {test_img.image_id}")
        else:
            test_img = ImageRepository.create_image("/static/img/default_recipe.png", user.user_id)
            print(f"Created test image: {test_img.image_id}")

        print(f"\nCategory ID: {test_cat.category_id}")
        print(f"Image ID: {test_img.image_id}")

        return test_cat, test_img

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "resources":
            get_test_resources()
        else:
            print("Usage: python test_helper.py [resources]")
    else:
        get_or_create_test_user()
