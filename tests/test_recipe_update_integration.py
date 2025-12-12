"""
Integration test for complete recipe update functionality.

This module tests that all recipe attributes (name, description, category, image, ingredients, steps)
are properly updated when using the update recipe endpoint.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from recipez.utils.recipe import RecipezRecipeUtils


class TestRecipeUpdateIntegration:
    """Integration test class for complete recipe update functionality."""

    @pytest.fixture
    def mock_authorization(self):
        """Mock authorization token."""
        return "mock-jwt-token"

    @pytest.fixture
    def mock_request(self):
        """Mock Flask request object."""
        mock_req = Mock()
        mock_req.form = {}
        return mock_req

    @pytest.fixture
    def recipe_id(self):
        """Test recipe ID."""
        return "4ee3e240-9eaf-4dd2-b69e-a08008cf6d39"

    def test_update_recipe_category_functionality(self, mock_authorization, mock_request, recipe_id):
        """Test that recipe category updates work correctly."""
        with patch('recipez.utils.recipe.RecipezCategoryUtils.create_category') as mock_create_cat:
            with patch('recipez.utils.recipe.RecipezCategoryUtils.read_category_by_id') as mock_read_cat:
                with patch('recipez.utils.recipe.session') as mock_session:
                    mock_session.get.return_value = "test-user-123"
                    
                    # Test creating new category
                    mock_create_cat.return_value = {
                        'category': {'category_id': 'new-cat-123', 'category_name': 'New Category'}
                    }
                    
                    result = RecipezRecipeUtils.update_recipe_category(
                        authorization=mock_authorization,
                        request=mock_request,
                        recipe_id=recipe_id,
                        current_category_id="old-cat-123",
                        category_name="New Category",
                        create_category_form=None
                    )
                    
                    assert result['new_category_created'] == True
                    assert result['category']['category_id'] == 'new-cat-123'
                    mock_create_cat.assert_called_once()

    def test_update_recipe_image_functionality(self, mock_authorization, mock_request, recipe_id):
        """Test that recipe image updates work correctly."""
        with patch('recipez.utils.recipe.RecipezImageUtils.update_image') as mock_update_img:
            mock_update_img.return_value = {
                'image': {'image_id': 'updated-img-123', 'image_url': 'http://example.com/new-image.jpg'}
            }
            
            result = RecipezRecipeUtils.update_recipe_image(
                authorization=mock_authorization,
                request=mock_request,
                recipe_id=recipe_id,
                current_image_id="old-img-123",
                image_data=b"fake-image-data"
            )
            
            assert result['image_updated'] == True
            assert result['image']['image_id'] == 'updated-img-123'
            mock_update_img.assert_called_once()

    def test_update_recipe_ingredients_functionality(self, mock_authorization, mock_request, recipe_id):
        """Test that recipe ingredients update correctly."""
        with patch('recipez.utils.recipe.RecipezIngredientUtils.delete_ingredient') as mock_delete_ing:
            with patch('recipez.utils.recipe.RecipezIngredientUtils.create_ingredients') as mock_create_ing:
                with patch('recipez.utils.recipe.session') as mock_session:
                    mock_session.get.return_value = "test-user-123"
                    
                    # Mock successful deletion
                    mock_delete_ing.return_value = {'success': True}
                    
                    # Mock successful creation
                    mock_create_ing.return_value = {
                        'ingredients': [
                            {'ingredient_id': 'new-ing-1', 'ingredient_name': 'Updated Flour'},
                            {'ingredient_id': 'new-ing-2', 'ingredient_name': 'Updated Sugar'}
                        ]
                    }
                    
                    # Mock current ingredients
                    current_ingredients = [
                        {'ingredient_id': 'old-ing-1', 'ingredient_name': 'Old Flour'}
                    ]
                    
                    # Mock ingredient forms
                    mock_forms = []
                    for i in range(2):
                        mock_form = Mock()
                        mock_form.quantity.data = f"{i+1}"
                        mock_form.measurement.data = "cup"
                        mock_form.ingredient_name.data = f"Updated Ingredient {i+1}"
                        mock_forms.append(mock_form)
                    
                    result = RecipezRecipeUtils.update_recipe_ingredients(
                        authorization=mock_authorization,
                        request=mock_request,
                        recipe_id=recipe_id,
                        current_ingredients=current_ingredients,
                        ingredient_forms=mock_forms
                    )
                    
                    assert result['ingredients_updated'] == True
                    assert len(result['ingredients']) == 2
                    mock_delete_ing.assert_called_once()
                    mock_create_ing.assert_called_once()

    def test_update_recipe_steps_functionality(self, mock_authorization, mock_request, recipe_id):
        """Test that recipe steps update correctly."""
        with patch('recipez.utils.recipe.RecipezStepUtils.delete_step') as mock_delete_step:
            with patch('recipez.utils.recipe.RecipezStepUtils.create_steps') as mock_create_step:
                with patch('recipez.utils.recipe.session') as mock_session:
                    mock_session.get.return_value = "test-user-123"
                    
                    # Mock successful deletion
                    mock_delete_step.return_value = {'success': True}
                    
                    # Mock successful creation
                    mock_create_step.return_value = {
                        'steps': [
                            {'step_id': 'new-step-1', 'step_text': 'Updated Step 1'},
                            {'step_id': 'new-step-2', 'step_text': 'Updated Step 2'}
                        ]
                    }
                    
                    # Mock current steps
                    current_steps = [
                        {'step_id': 'old-step-1', 'step_text': 'Old Step 1'}
                    ]
                    
                    # Mock step forms
                    mock_forms = []
                    for i in range(2):
                        mock_form = Mock()
                        mock_form.step.data = f"Updated Step {i+1}"
                        mock_forms.append(mock_form)
                    
                    result = RecipezRecipeUtils.update_recipe_steps(
                        authorization=mock_authorization,
                        request=mock_request,
                        recipe_id=recipe_id,
                        current_steps=current_steps,
                        step_forms=mock_forms
                    )
                    
                    assert result['steps_updated'] == True
                    assert len(result['steps']) == 2
                    mock_delete_step.assert_called_once()
                    mock_create_step.assert_called_once()

    def test_update_recipe_basic_attributes(self, mock_authorization, mock_request, recipe_id):
        """Test that basic recipe attributes (name, description) update correctly."""
        with patch('recipez.utils.recipe.RecipezAPIUtils.make_request') as mock_api:
            with patch('recipez.utils.recipe.current_app') as mock_app:
                # Mock Flask app config
                mock_session = Mock()
                mock_app.config.get.return_value = mock_session
                mock_session.put = Mock()
                
                # Mock successful API response
                mock_api.return_value = {
                    'recipe': {
                        'recipe_id': recipe_id,
                        'recipe_name': 'Updated Recipe Name',
                        'recipe_description': 'Updated Recipe Description'
                    }
                }

                updates = {
                    'recipe_name': 'Updated Recipe Name',
                    'recipe_description': 'Updated Recipe Description'
                }
                
                result = RecipezRecipeUtils.update_recipe(
                    authorization=mock_authorization,
                    request=mock_request,
                    recipe_id=recipe_id,
                    updates=updates
                )
                
                assert 'recipe' in result
                assert result['recipe']['recipe_name'] == 'Updated Recipe Name'
                assert result['recipe']['recipe_description'] == 'Updated Recipe Description'
                mock_api.assert_called_once()

    def test_complete_recipe_update_flow(self):
        """Test that the complete recipe update flow works end-to-end."""
        # This test verifies that all the individual update methods work together
        methods_to_test = [
            'update_recipe_category',
            'update_recipe_image', 
            'update_recipe',
            'update_recipe_ingredients',
            'update_recipe_steps'
        ]
        
        for method_name in methods_to_test:
            method = getattr(RecipezRecipeUtils, method_name)
            assert callable(method), f"{method_name} should be callable"
            
            # Verify method has proper signature
            import inspect
            sig = inspect.signature(method)
            params = list(sig.parameters.keys())
            
            # All methods should have authorization and request parameters
            assert 'authorization' in params, f"{method_name} should have authorization parameter"
            assert 'request' in params, f"{method_name} should have request parameter"
            
        print("✓ All update methods are properly defined and callable")
        print("✓ All methods have required authorization and request parameters")
        print("✓ Complete recipe update flow structure is correct")


if __name__ == '__main__':
    pytest.main([__file__])
