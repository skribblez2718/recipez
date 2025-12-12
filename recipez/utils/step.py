import re
import json
from flask import current_app, flash, jsonify
from uuid import UUID
from typing import List, Dict, Union
from wtforms import ValidationError

from recipez.utils.api import RecipezAPIUtils
from recipez.utils.error import RecipezErrorUtils
from recipez.schema import UpdateStepsSchema, DeleteStepSchema


###################################[ start RecipezStepUtils ]###################################
class RecipezStepUtils:
    """ """

    #########################[ start create_ingredient ]#############################
    @staticmethod
    def create_steps(
        authorization: str,
        request: "Request",
        steps: List[Dict[str, str]],
        author_id: str,
        recipe_id: str,
    ) -> List[Dict[str, str]]:
        """
        Sends request to create steps API

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            steps (List[Dict[str, str]]): The steps to create.
            author_id (str): The ID of the author.
            recipe_id (str): The ID of the recipe.

        Returns:
            List[Dict[str, str]]: A list of steps.
        """
        name = f"step.create_steps"
        response_msg = "An error occurred while creating the steps"

        request_json = {
            "steps": steps,
            "author_id": author_id,
            "recipe_id": recipe_id,
        }
        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/step/create",
                json=request_json,
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            response = RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if not response or "error" in response:
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        return response

    #########################[ end create_ingredient ]###############################

    #########################[ start read_step_by_id ]#############################
    @staticmethod
    def read_step_by_id(
        authorization: str, request: "Request", step_id: str
    ) -> List[Dict[str, str]]:
        """
        Fetches a step by id from the API.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            step_id (UUID): The ID of the step to fetch.

        Returns:
            List[Dict[str, str]]: A list of steps.
        """
        name = f"step.read_step_by_id"
        response_msg = "An error occurred while fetching steps"

        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").get,
                path=f"/api/step/{step_id}",
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            response = RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if not response or "error" in response:
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        return response

    #########################[ end read_step_by_id ]###############################

    #########################[ start read_all_steps ]#############################
    @staticmethod
    def read_all_steps(authorization: str, request: "Request") -> List[Dict[str, str]]:
        """
        Fetches all steps from the API.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.

        Returns:
            List[Dict[str, str]]: A list of steps.
        """
        name = f"step.read_all_steps"
        response_msg = "An error occurred while fetching steps"

        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").get,
                path="/api/step/all",
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            response = RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if not response or "error" in response:
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        return response

    #########################[ end read_all_steps ]###############################

    #########################[ start update_step ]#############################
    @staticmethod
    def update_step(
        authorization: str, request: "Request", step_id: str, step_name: str
    ) -> List[Dict[str, str]]:
        """
        Updates an existing step.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            step_id (str): The ID of the step to update.
            step_name (str): The name of the step to update.

        Returns:
            List[Dict[str, str]]: A list of steps.
        """
        name = f"step.update_step"
        response_msg = "An error occurred while updating the step"

        try:
            data: UpdateStepsSchema = UpdateStepsSchema(
                **{"step_name": step_name, "step_id": UUID(step_id)}
            )
        except Exception as e:
            step_error = "Invalid step name or id"
            return RecipezErrorUtils.handle_util_error(
                name, request, e, step_error
            )

        step_name = data.step_name
        step_id = data.step_id
        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").put,
                path=f"/api/step/update/{str(step_id)}",
                json={
                    "step_name": step_name,
                },
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if not response or "error" in response:
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        return response

    #########################[ end update_step ]###############################

    #########################[ start delete_step ]#############################
    @staticmethod
    def delete_step(
        authorization: str, request: "Request", step_id: str
    ) -> List[Dict[str, str]]:
        """
        Deletes an existing category.

        Args:
            authorization (str): The authorization token.
            request (Request): The request object.
            step_id (str): The ID of the step to delete.

        Returns:
            List[Dict[str, str]]: A list of steps.
        """
        name = f"step.delete_step"
        response_msg = "An error occurred while deleting the step"

        try:
            data: DeleteStepSchema = DeleteStepSchema(**{"step_id": UUID(step_id)})
        except Exception as e:
            step_error = "Invalid step id."
            return RecipezErrorUtils.handle_util_error(
                name, request, e, step_error
            )

        step_id = data.step_id
        try:
            response: Union[Dict[str, str], None] = RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").delete,
                path=f"/api/step/delete/{str(step_id)}",
                authorization=authorization,
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

        if not response or "error" in response:
            error_msg = response.get("error", response_msg)
            return RecipezErrorUtils.handle_util_error(
                name, request, error_msg, response_msg
            )

        return response

    #########################[ end delete_step ]###############################


###################################[ end RecipezStepUtils ]####################################
