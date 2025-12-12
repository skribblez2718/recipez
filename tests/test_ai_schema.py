import pytest
from uuid import uuid4
import importlib.util
import pathlib

# Load schema module directly to avoid importing full package
schema_path = pathlib.Path(__file__).resolve().parents[1] / "recipez" / "schema" / "ai.py"
spec = importlib.util.spec_from_file_location("ai_schema", schema_path)
ai_schema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ai_schema)
AICreateRecipeSchema = ai_schema.AICreateRecipeSchema
AIModifyRecipeSchema = ai_schema.AIModifyRecipeSchema


def test_ai_create_schema_requires_message():
    with pytest.raises(Exception):
        AICreateRecipeSchema(message="")


def test_ai_modify_schema_requires_uuid():
    with pytest.raises(Exception):
        AIModifyRecipeSchema(recipe_id="bad", message="hello")


def test_ai_modify_schema_valid():
    obj = AIModifyRecipeSchema(recipe_id=uuid4(), message="Change it")
    assert obj.message == "change it"
