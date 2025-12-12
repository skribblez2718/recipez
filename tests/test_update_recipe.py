"""
Test module for update recipe functionality.

This module tests the update recipe view and ensures it mirrors
the create recipe functionality properly.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, session, request
from recipez.blueprint.view.recipe import update_recipe_view
from recipez.utils import RecipezRecipeUtils


class TestUpdateRecipeView:
    """Test class for update recipe view functionality."""

    @pytest.fixture
    def app(self):
        """Create a Flask app for testing."""
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()

    @pytest.fixture
    def mock_session_data(self):
        """Mock session data for authenticated user."""
        return {
            'user_id': 'test-user-123',
            'user_jwt': 'mock-jwt-token'
        }

    @pytest.fixture
    def mock_existing_recipe(self):
        """Mock existing recipe data."""
        return {
            'recipe_id': '4ee3e240-9eaf-4dd2-b69e-a08008cf6d39',
            'recipe_name': 'Test Recipe',
            'recipe_description': 'Test Description',
            'recipe_category_id': 'category-123',
            'recipe_image_id': 'image-123',
            'recipe_author_id': 'test-user-123',
            'recipe_ingredients': [
                {
                    'ingredient_id': 'ing-1',
                    'ingredient_quantity': '2',
                    'ingredient_measurement': 'cups',
                    'ingredient_name': 'flour'
                }
            ],
            'recipe_steps': [
                {
                    'step_id': 'step-1',
                    'step_text': 'Mix ingredients'
                }
            ]
        }

    @pytest.fixture
    def mock_categories(self):
        """Mock categories data."""
        return [
            {'category_id': 'cat-1', 'category_name': 'Desserts'},
            {'category_id': 'cat-2', 'category_name': 'Main Dishes'}
        ]

    def test_update_recipe_category_method_signature(self):
        """Test that update_recipe_category method has correct signature."""
        import inspect
        
        # Get the method signature
        sig = inspect.signature(RecipezRecipeUtils.update_recipe_category)
        params = list(sig.parameters.keys())
        
        # Verify expected parameters
        expected_params = [
            'authorization',
            'request', 
            'recipe_id',
            'current_category_id',
            'category_name',
            'create_category_form'
        ]
        
        assert params == expected_params, f"Expected {expected_params}, got {params}"
        
        # Verify no 'category_id' parameter exists
        assert 'category_id' not in params, "Method should not have 'category_id' parameter"

    @patch('recipez.blueprint.view.recipe.RecipezRecipeUtils.read_recipe')
    @patch('recipez.blueprint.view.recipe.RecipezCategoryUtils.read_all_categories')
    @patch('recipez.blueprint.view.recipe.session')
    @patch('recipez.blueprint.view.recipe.request')
    def test_update_recipe_get_request(self, mock_request, mock_session, 
                                     mock_read_categories, mock_read_recipe,
                                     app, mock_session_data, mock_existing_recipe, 
                                     mock_categories):
        """Test GET request to update recipe view."""
        # Setup mocks
        mock_session.get.side_effect = lambda key, default=None: mock_session_data.get(key, default)
        mock_session.__getitem__ = lambda key: mock_session_data[key]
        mock_request.method = 'GET'
        mock_read_recipe.return_value = mock_existing_recipe
        mock_read_categories.return_value = mock_categories
        
        with app.test_request_context():
            with patch('recipez.blueprint.view.recipe.RecipezResponseUtils.generate_nonces') as mock_nonces:
                mock_nonces.return_value = ('script-nonce', 'link-nonce')
                
                with patch('recipez.blueprint.view.recipe.RecipezResponseUtils.process_response') as mock_process:
                    mock_process.return_value = 'rendered-template'
                    
                    result = update_recipe_view('4ee3e240-9eaf-4dd2-b69e-a08008cf6d39')
                    
                    # Verify the recipe was read
                    mock_read_recipe.assert_called_once()
                    
                    # Verify categories were read
                    mock_read_categories.assert_called_once()
                    
                    # Verify response was processed
                    mock_process.assert_called_once()

    @patch('recipez.blueprint.view.recipe.RecipezRecipeUtils.update_recipe_category')
    @patch('recipez.blueprint.view.recipe.RecipezRecipeUtils.update_recipe_image')
    @patch('recipez.blueprint.view.recipe.RecipezRecipeUtils.update_recipe')
    @patch('recipez.blueprint.view.recipe.RecipezRecipeUtils.update_recipe_ingredients')
    @patch('recipez.blueprint.view.recipe.RecipezRecipeUtils.update_recipe_steps')
    @patch('recipez.blueprint.view.recipe.RecipezRecipeUtils.read_recipe')
    @patch('recipez.blueprint.view.recipe.RecipezCategoryUtils.read_all_categories')
    @patch('recipez.blueprint.view.recipe.session')
    @patch('recipez.blueprint.view.recipe.request')
    def test_update_recipe_post_request_success(self, mock_request, mock_session,
                                               mock_read_categories, mock_read_recipe,
                                               mock_update_steps, mock_update_ingredients,
                                               mock_update_recipe, mock_update_image,
                                               mock_update_category, app,
                                               mock_session_data, mock_existing_recipe,
                                               mock_categories):
        """Test successful POST request to update recipe."""
        # Setup mocks
        mock_session.get.side_effect = lambda key, default=None: mock_session_data.get(key, default)
        mock_session.__getitem__ = lambda key: mock_session_data[key]
        mock_request.method = 'POST'
        mock_read_recipe.return_value = mock_existing_recipe
        mock_read_categories.return_value = mock_categories
        
        # Mock successful responses for all update operations
        mock_update_category.return_value = {
            'new_category_created': False,
            'category': {'category_id': 'cat-1', 'category_name': 'Desserts'}
        }
        mock_update_image.return_value = {'image_updated': True}
        mock_update_recipe.return_value = {'recipe_updated': True}
        mock_update_ingredients.return_value = {'ingredients_updated': True}
        mock_update_steps.return_value = {'steps_updated': True}
        
        with app.test_request_context():
            with patch('recipez.blueprint.view.recipe.UpdateRecipeForm') as mock_form_class:
                # Mock form validation
                mock_form = Mock()
                mock_form.validate.return_value = True
                mock_form.name.data = 'Updated Recipe Name'
                mock_form.description.data = 'Updated Description'
                mock_form.category_selector.data = 'cat-1'
                mock_form.image.data = None
                mock_form.ingredients.entries = []
                mock_form.steps.entries = []
                mock_form_class.return_value = mock_form
                
                with patch('recipez.blueprint.view.recipe.CreateCategoryForm') as mock_cat_form_class:
                    mock_cat_form = Mock()
                    mock_cat_form.name.data = None
                    mock_cat_form_class.return_value = mock_cat_form
                    
                    with patch('recipez.blueprint.view.recipe.flash') as mock_flash:
                        with patch('recipez.blueprint.view.recipe.redirect') as mock_redirect:
                            mock_redirect.return_value = 'redirect-response'
                            
                            result = update_recipe_view('4ee3e240-9eaf-4dd2-b69e-a08008cf6d39')
                            
                            # Verify all update methods were called
                            mock_update_category.assert_called_once()
                            mock_update_image.assert_called_once()
                            mock_update_recipe.assert_called_once()
                            mock_update_ingredients.assert_called_once()
                            mock_update_steps.assert_called_once()
                            
                            # Verify success flash message
                            mock_flash.assert_called_once()
                            flash_args = mock_flash.call_args[0]
                            assert 'updated successfully' in flash_args[0]
                            
                            # Verify redirect
                            mock_redirect.assert_called_once()

    @patch('recipez.blueprint.view.recipe.RecipezRecipeUtils.update_recipe_category')
    @patch('recipez.blueprint.view.recipe.RecipezRecipeUtils.cleanup_recipe_category')
    @patch('recipez.blueprint.view.recipe.RecipezRecipeUtils.read_recipe')
    @patch('recipez.blueprint.view.recipe.RecipezCategoryUtils.read_all_categories')
    @patch('recipez.blueprint.view.recipe.session')
    @patch('recipez.blueprint.view.recipe.request')
    def test_update_recipe_category_error_handling(self, mock_request, mock_session,
                                                  mock_read_categories, mock_read_recipe,
                                                  mock_cleanup_category, mock_update_category,
                                                  app, mock_session_data, mock_existing_recipe,
                                                  mock_categories):
        """Test error handling and cleanup when category update fails."""
        # Setup mocks
        mock_session.get.side_effect = lambda key, default=None: mock_session_data.get(key, default)
        mock_session.__getitem__ = lambda key: mock_session_data[key]
        mock_request.method = 'POST'
        mock_read_recipe.return_value = mock_existing_recipe
        mock_read_categories.return_value = mock_categories
        
        # Mock category update error
        mock_update_category.return_value = {
            'error': 'Category update failed'
        }
        
        with app.test_request_context():
            with patch('recipez.blueprint.view.recipe.UpdateRecipeForm') as mock_form_class:
                mock_form = Mock()
                mock_form.validate.return_value = True
                mock_form.category_selector.data = 'cat-1'
                mock_form_class.return_value = mock_form
                
                with patch('recipez.blueprint.view.recipe.CreateCategoryForm') as mock_cat_form_class:
                    mock_cat_form = Mock()
                    mock_cat_form.name.data = None
                    mock_cat_form_class.return_value = mock_cat_form
                    
                    with patch('recipez.blueprint.view.recipe.RecipezErrorUtils.handle_view_error') as mock_error:
                        mock_error.return_value = 'error-response'
                        
                        result = update_recipe_view('4ee3e240-9eaf-4dd2-b69e-a08008cf6d39')
                        
                        # Verify category update was called
                        mock_update_category.assert_called_once()
                        
                        # Verify error handling was called
                        mock_error.assert_called_once()
                        
                        # Verify cleanup was not called (no new category was created)
                        mock_cleanup_category.assert_not_called()

    def test_update_recipe_mirrors_create_recipe_structure(self):
        """Test that update recipe follows the same 5-step structure as create recipe."""
        import inspect
        import re
        
        # Read the recipe view file
        with open('/home/user/projects/recipez/recipez/blueprint/view/recipe.py', 'r') as f:
            content = f.read()
        
        # Extract create recipe steps
        create_pattern = r'# Step (\d+): ([^\n]+)'
        create_matches = re.findall(create_pattern, content[:content.find('def update_recipe_view')])
        
        # Extract update recipe steps  
        update_content = content[content.find('def update_recipe_view'):]
        update_matches = re.findall(create_pattern, update_content)
        
        # Verify both have 5 steps
        assert len(create_matches) == 5, f"Create recipe should have 5 steps, found {len(create_matches)}"
        assert len(update_matches) == 5, f"Update recipe should have 5 steps, found {len(update_matches)}"
        
        # Verify step correspondence
        expected_correspondences = [
            ('Create or get the recipe category', 'Update the recipe category'),
            ('Create the recipe image', 'Update the recipe image'),
            ('Create the recipe', 'Update the recipe details'),
            ('Create recipe ingredients', 'Update recipe ingredients'),
            ('Create recipe steps', 'Update recipe steps')
        ]
        
        for i, (create_desc, update_desc) in enumerate(expected_correspondences):
            create_step = create_matches[i][1]
            update_step = update_matches[i][1]
            
            assert create_desc in create_step, f"Create step {i+1} should contain '{create_desc}'"
            assert update_desc in update_step, f"Update step {i+1} should contain '{update_desc}'"


if __name__ == '__main__':
    pytest.main([__file__])
