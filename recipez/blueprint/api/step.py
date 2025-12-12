from typing import Dict, List
from flask import Blueprint, jsonify, request

from recipez.utils import RecipezAuthNUtils, RecipezAuthZUtils, RecipezErrorUtils
from recipez.repository import StepRepository
from recipez.schema import (
    CreateStepsSchema,
    ReadStepsSchema,
    UpdateStepsSchema,
    DeleteStepSchema,
)
from recipez.extensions import csrf

bp = Blueprint("api/step", __name__, url_prefix="/api/step")


#########################[ start create_steps_api ]###############################
@bp.route("/create", methods=["POST"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.step_create_required
def create_steps_api() -> Dict:
    """Create steps for a recipe."""
    name = f"step.{create_steps_api.__name__}"
    response_msg = "Failed to create step"
    try:
        data = CreateStepsSchema(**request.json)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    created_steps: List[Dict] = []
    try:
        for step in data.steps:
            created_step = StepRepository.create_step(
                step.step_description,
                str(data.recipe_id),
                str(data.author_id),
            )
            created_steps.append(created_step.as_dict())
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    return jsonify({"response": {"steps": created_steps}})


#########################[ end create_steps_api ]################################


#########################[ start read_steps_api ]################################
@bp.route("/<pk>", methods=["GET"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.step_read_required
def read_steps_api(pk: str) -> Dict:
    """Read all steps for a recipe."""
    name = f"step.{read_steps_api.__name__}"
    response_msg = "Step not found"

    try:
        data = ReadStepsSchema(recipe_id=pk)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    try:
        steps = StepRepository.read_steps_by_recipe_id(str(data.recipe_id))
        if not steps:
            return jsonify(
                {
                    "response": {
                        "steps": [
                            {
                                "step_id": "",
                                "step_text": "",
                                "step_author_id": "",
                                "step_recipe_id": "",
                                "created_at": "",
                            }
                        ]
                    }
                }
            )
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    return jsonify({"response": {"steps": steps}})


#########################[ end read_steps_api ]##################################


#########################[ start update_steps_api ]###############################
@bp.route("/update/<pk>", methods=["PUT"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.step_update_required
def update_steps_api(pk: str) -> Dict:
    """Update a step."""
    name = f"step.{update_steps_api.__name__}"
    response_msg = "Failed to update step"

    json_data = request.json or {}
    json_data["step_id"] = pk
    try:
        data = UpdateStepsSchema(**json_data)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    try:
        updated = StepRepository.update_step(str(data.step_id), data.step_description)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)
    if not updated:
        return jsonify({"response": {"error": response_msg}})
    return jsonify({"response": {"success": True}})


#########################[ end update_steps_api ]################################


#########################[ start delete_steps_api ]###############################
@bp.route("/delete/<pk>", methods=["DELETE"])
@csrf.exempt  # Exempt from CSRF protection - protected by JWT authentication
@RecipezAuthNUtils.jwt_required
@RecipezAuthZUtils.step_delete_required
def delete_steps_api(pk: str) -> Dict:
    """Delete a step."""
    name = f"step.{delete_steps_api.__name__}"
    response_msg = "Failed to delete step"
    try:
        data = DeleteStepSchema(step_id=pk)
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)

    try:
        deleted = StepRepository.delete_step(str(data.step_id))
    except Exception as e:
        return RecipezErrorUtils.handle_api_error(name, request, e, response_msg)
    if not deleted:
        return jsonify({"response": {"error": response_msg}})
    return jsonify({"response": {"success": True}})


#########################[ end delete_steps_api ]################################
