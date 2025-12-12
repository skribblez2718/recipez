from flask import (
    current_app,
    jsonify,
)

from typing import Dict, Any, List
import smtplib
from email.utils import parseaddr
from email.message import EmailMessage

from recipez.utils.api import RecipezAPIUtils
from recipez.utils.error import RecipezErrorUtils
from recipez.dataclass import EmailInvite, EmailRecipeShare, EmailRecipeShareFull

CODE_VERIFICATION_EMAIL_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
   <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Login Verification Code</title>
      <style>
         body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #0f172a;
            margin: 0;
            padding: 0;
            line-height: 1.6;
         }}
         .container {{
            max-width: 600px;
            margin: 20px auto;
            padding: 0;
            background-color: #1e293b;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            overflow: hidden;
         }}
         .header {{
            text-align: center;
            background-color: #0f172a;
            color: white;
            padding: 20px 15px;
            border-bottom: 3px solid #ff6b6b;
         }}
         .header h2 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
         }}
         .content {{
            padding: 24px;
            color: #e2e8f0;
         }}
         .content p {{
            margin: 12px 0;
         }}
         .code-container {{
            background-color: #0f172a;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
            border-radius: 8px;
            border: 1px solid #334155;
         }}
         .verification-code {{
            font-family: 'SF Mono', 'Cascadia Code', 'Fira Code', 'JetBrains Mono', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 32px;
            font-weight: 600;
            letter-spacing: 6px;
            color: #ff6b6b;
            background-color: #1e293b;
            padding: 15px 30px;
            border: 2px dashed #ff6b6b;
            border-radius: 8px;
            display: inline-block;
            margin: 10px 0;
            cursor: pointer;
            user-select: all;
            -webkit-user-select: all;
            -moz-user-select: all;
            -ms-user-select: all;
         }}
         .copy-instruction {{
            font-size: 13px;
            color: #94a3b8;
            margin: 10px 0 0;
         }}
         a {{
            text-decoration: none;
            color: #ff6b6b;
         }}
         .footer {{
            text-align: center;
            padding: 16px;
            color: #94a3b8;
            font-size: 12px;
            background-color: #0f172a;
            border-top: 1px solid #334155;
         }}
         .footer a {{
            color: #ff6b6b;
         }}
      </style>
   </head>
   <body>
      <div class="container">
         <div class="header">
            <h2>Login Verification Code</h2>
         </div>
         <div class="content">
            <p>Dear Chef,</p>
            <p>We are sending you this email because you have requested to log in to your account. To complete the login process, please enter the verification code below:</p>
            <div class="code-container">
               <div class="verification-code" onclick="this.focus();this.select()">{verification_code}</div>
            </div>
            <p>Please enter this code on our website within the next {timeframe} to access your account.</p>
            <p>Best regards,</p>
            <p><strong>Recipez</strong></p>
         </div>
         <div class="footer">
            <p>This is an automated message from <a href="#">Recipez</a></p>
         </div>
      </div>
   </body>
</html>
"""

RECIPE_SHARE_EMAIL_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
   <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>{recipe_name} - Shared Recipe</title>
      <style>
         body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #0f172a;
            margin: 0;
            padding: 0;
            line-height: 1.6;
         }}
         .container {{
            max-width: 600px;
            margin: 20px auto;
            padding: 0;
            background-color: #1e293b;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            overflow: hidden;
         }}
         .header {{
            text-align: center;
            background-color: #0f172a;
            color: white;
            padding: 20px 15px;
            border-bottom: 3px solid #ff6b6b;
         }}
         .header h2 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
         }}
         .content {{
            padding: 24px;
            color: #e2e8f0;
         }}
         .content p {{
            margin: 12px 0;
         }}
         .recipe-section {{
            background-color: #0f172a;
            padding: 16px;
            margin: 16px 0;
            border-radius: 8px;
            border: 1px solid #334155;
         }}
         .recipe-section h3 {{
            color: #ff6b6b;
            margin: 0 0 12px 0;
            font-size: 18px;
         }}
         .ingredient-list {{
            list-style: none;
            padding: 0;
            margin: 0;
         }}
         .ingredient-list li {{
            padding: 8px 0;
            border-bottom: 1px solid #334155;
         }}
         .ingredient-list li:last-child {{
            border-bottom: none;
         }}
         .step-list {{
            padding-left: 0;
            margin: 0;
            list-style: none;
         }}
         .step-list li {{
            padding: 12px 0;
            border-bottom: 1px solid #334155;
         }}
         .step-list li:last-child {{
            border-bottom: none;
         }}
         .description {{
            font-style: italic;
            color: #94a3b8;
         }}
         a {{
            text-decoration: none;
            color: #ff6b6b;
         }}
         .footer {{
            text-align: center;
            padding: 16px;
            color: #94a3b8;
            font-size: 12px;
            background-color: #0f172a;
            border-top: 1px solid #334155;
         }}
         .footer a {{
            color: #ff6b6b;
         }}
      </style>
   </head>
   <body>
      <div class="container">
         <div class="header">
            <h2>{recipe_name}</h2>
         </div>
         <div class="content">
            <p>Dear Chef,</p>
            <p><strong>{sender_name}</strong> shared this recipe with you!</p>
            {description_html}
            <div class="recipe-section">
               <h3>Ingredients</h3>
               <ul class="ingredient-list">
                  {ingredients_html}
               </ul>
            </div>
            <div class="recipe-section">
               <h3>Steps</h3>
               <ol class="step-list">
                  {steps_html}
               </ol>
            </div>
            <p>Enjoy cooking!</p>
            <p>Best regards,</p>
            <p><strong>Recipez</strong></p>
         </div>
         <div class="footer">
            <p>This recipe was shared via <a href="#">Recipez</a></p>
         </div>
      </div>
   </body>
</html>
"""


###################################[ start RecipezEmailUtils ]###################################
class RecipezEmailUtils:
    """
    A class to generate and send customizable email templates for Recipez.

    This class contains static methods for generating email templates and sending emails
    of different types (verification codes, invites, recipes, etc.) with a consistent interface.
    """

    #########################[ start email_code ]##########################
    @staticmethod
    def email_code(
        authorization: str,
        email: str,
        code: str,
        request: "Request",
    ) -> Dict[str, Dict[str, str]]:
        """
        Sends an email with a verification code to the specified recipient.

        Args:
           recipient_email (str): The recipient's email address.
           code (str): The verification code to be sent.

        Returns:
           Dict[str, Dict[str, str]]: A response dictionary indicating success or failure.
        """

        name = f"code.email_code"
        response_msg = "An error occurred while creating the code"
        try:
            return RecipezAPIUtils.make_request(
                method=current_app.config.get("RECIPEZ_HTTP_SESSION").post,
                path="/api/email/code",
                authorization=authorization,
                json={
                    "email": email,
                    "code": code,
                },
                request=request,
            )
        except Exception as e:
            return RecipezErrorUtils.handle_util_error(name, request, e, response_msg)

    #########################[ end email_code ]############################

    #########################[ start send_email ]##########################
    @staticmethod
    def send_email(
        recipient_email: str, subject: str, html_content: str, request: "Request"
    ) -> Dict[str, Any]:
        """
        Sends an email with the specified content to the recipient.

        This is the core email sending function used by all email types.

        Args:
           request (Request): The Flask request object.
           recipient_email (str): The recipient's email address.
           subject (str): The email subject line.
           html_content (str): The HTML content of the email.

        Returns:
           Dict[str, Any]: A response dictionary indicating success or failure.
        """
        name = f"email.{RecipezEmailUtils.send_email.__name__}"
        response_msg = ""
        log_msg = ""

        # Validate email format
        _, parsed_email = parseaddr(recipient_email)
        if not parsed_email or "\n" in parsed_email or "\r" in parsed_email:
            log_msg = f"Invalid email address format: {recipient_email}"
            response_msg = "Invalid email address format."
            return RecipezErrorUtils.handle_util_error(name, request, log_msg, response_msg)

        # Create email message
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = current_app.config.get("RECIPEZ_SENDER_EMAIL")
        msg["To"] = parsed_email
        msg.set_content("Please view this email with an HTML-compatible email client.")
        msg.add_alternative(html_content, subtype="html")

        # Get SMTP configuration
        smtp_hostname = current_app.config["RECIPEZ_SMTP_HOSTNAME"]
        smtp_port = current_app.config["RECIPEZ_SMTP_PORT"]
        sender_email = current_app.config.get("RECIPEZ_SENDER_EMAIL")
        sender_password = current_app.config.get("RECIPEZ_SENDER_PASSWORD")

        # Debug logging for SMTP config
        current_app.logger.info(
            f"[{name}] SMTP Config - hostname: {smtp_hostname}, port: {smtp_port}, "
            f"sender: {sender_email}, password_set: {bool(sender_password)}, "
            f"password_len: {len(sender_password) if sender_password else 0}"
        )

        try:
            with smtplib.SMTP(smtp_hostname, smtp_port) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(sender_email, sender_password)
                smtp.send_message(msg)

                return {
                    "response": {
                        "message": f"Email successfully sent to {recipient_email}"
                    }
                }
        except smtplib.SMTPAuthenticationError as e:
            current_app.logger.error(f"[{name}] SMTP Auth Error: {str(e)}")
            return {"error": f"SMTP authentication failed: {str(e)}"}
        except smtplib.SMTPException as e:
            current_app.logger.error(f"[{name}] SMTP Error: {str(e)}")
            return {"error": f"SMTP error: {str(e)}"}
        except Exception as e:
            current_app.logger.error(f"[{name}] Failed to send email: {type(e).__name__}: {str(e)}")
            return {"error": f"Email error: {type(e).__name__}: {str(e)}"}

    #########################[ end send_email ]############################

    ###########################[ start get_verification_code_email ]#####################
    @staticmethod
    def get_verification_code_email(
        verification_code: str,
        timeframe: str = "5 minutes",
    ) -> str:
        """
        Generates an HTML email template for a login verification code.

        Parameters:
            verification_code (str): The verification code to be included in the email.
              timeframe (str): The time within which the verification code is valid. Defaults to "10 minutes".
              support_email (str): The email address of the support team.

        Returns:
            str: An HTML string representing the verification code email.
        """
        return CODE_VERIFICATION_EMAIL_TEMPLATE.format(
            verification_code=verification_code, timeframe=timeframe
        )

    ###########################[ end get_verification_code_email ]############

    ###########################[ start email_invite ]#########################
    @staticmethod
    def email_invite(request: "Request", payload: EmailInvite) -> Dict[str, Any]:
        """Send an invitation email using provided payload."""

        subject = f"{payload.sender_name} invited you to Recipez"
        html_content = (
            f"<p>{payload.sender_name} has invited you to join Recipez.</p>"
            f"<p><a href='{payload.invite_link}'>Join Recipez</a></p>"
        )
        try:
            return RecipezEmailUtils.send_email(
                payload.email, subject, html_content, request
            )
        except Exception as e:
            response_msg = "Failed to send invitation email"
            return RecipezErrorUtils.handle_util_error(
                "email.email_invite", request, e, response_msg
            )

    ###########################[ end email_invite ]###########################

    ###########################[ start email_recipe_share ]###################
    @staticmethod
    def email_recipe_share(
        request: "Request", payload: EmailRecipeShare
    ) -> Dict[str, Any]:
        """Send a recipe sharing email using provided payload."""

        subject = f"{payload.sender_name} shared a recipe with you"
        html_content = (
            f"<p>{payload.sender_name} shared the recipe "
            f"<strong>{payload.recipe_name}</strong>.</p>"
            f"<p>View it here: <a href='{payload.recipe_link}'>{payload.recipe_link}</a></p>"
        )
        try:
            return RecipezEmailUtils.send_email(
                payload.email, subject, html_content, request
            )
        except Exception as e:
            response_msg = "Failed to send recipe sharing email"
            return RecipezErrorUtils.handle_util_error(
                "email.email_recipe_share", request, e, response_msg
            )

    ###########################[ end email_recipe_share ]#####################

    ###########################[ start get_recipe_share_email ]###################
    @staticmethod
    def get_recipe_share_email(
        recipe_name: str,
        recipe_description: str,
        recipe_ingredients: List[Dict[str, str]],
        recipe_steps: List[str],
        sender_name: str,
    ) -> str:
        """
        Generates an HTML email template for sharing a full recipe.

        Parameters:
            recipe_name (str): The name of the recipe being shared.
            recipe_description (str): The description of the recipe.
            recipe_ingredients (List[Dict[str, str]]): List of ingredients with quantity, measurement, name.
            recipe_steps (List[str]): List of recipe steps.
            sender_name (str): The name of the person sharing the recipe.

        Returns:
            str: An HTML string representing the recipe share email.
        """
        import html

        # Build description HTML
        description_html = ""
        if recipe_description:
            description_html = f'<p class="description">{html.escape(recipe_description)}</p>'

        # Build ingredients HTML with inline bullet character
        ingredients_html = ""
        for ing in recipe_ingredients:
            quantity = html.escape(str(ing.get("quantity", "")))
            measurement = html.escape(str(ing.get("measurement", "")))
            name = html.escape(str(ing.get("name", "")))
            # Use inline bullet character since CSS ::before doesn't work in email clients
            ingredients_html += f'<li><span style="color: #ff6b6b; margin-right: 8px;">&#8226;</span>{quantity} {measurement} {name}</li>\n'

        # Build steps HTML with inline step numbers
        steps_html = ""
        for i, step in enumerate(recipe_steps, start=1):
            step_text = html.escape(str(step).strip())
            # Use inline number since CSS counters don't work in email clients
            steps_html += f'<li><span style="display: inline-block; width: 24px; height: 24px; background-color: #ff6b6b; color: white; border-radius: 50%; text-align: center; line-height: 24px; font-weight: bold; font-size: 12px; margin-right: 10px;">{i}</span>{step_text}</li>\n'

        return RECIPE_SHARE_EMAIL_TEMPLATE.format(
            recipe_name=html.escape(recipe_name),
            sender_name=html.escape(sender_name),
            description_html=description_html,
            ingredients_html=ingredients_html,
            steps_html=steps_html,
        )

    ###########################[ end get_recipe_share_email ]#####################

    ###########################[ start email_recipe_share_full ]###################
    @staticmethod
    def email_recipe_share_full(
        request: "Request", payload: EmailRecipeShareFull
    ) -> Dict[str, Any]:
        """Send a full recipe sharing email with complete recipe content."""

        subject = f"{payload.sender_name} shared a recipe with you: {payload.recipe_name}"
        html_content = RecipezEmailUtils.get_recipe_share_email(
            recipe_name=payload.recipe_name,
            recipe_description=payload.recipe_description,
            recipe_ingredients=payload.recipe_ingredients,
            recipe_steps=payload.recipe_steps,
            sender_name=payload.sender_name,
        )
        try:
            return RecipezEmailUtils.send_email(
                payload.email, subject, html_content, request
            )
        except Exception as e:
            response_msg = "Failed to send recipe sharing email"
            return RecipezErrorUtils.handle_util_error(
                "email.email_recipe_share_full", request, e, response_msg
            )

    ###########################[ end email_recipe_share_full ]#####################


###################################[ end RecipezEmailUtils ]###################################
