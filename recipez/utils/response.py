import secrets

from flask import (
    current_app,
    make_response,
    render_template,
    request,
)


###################################[ start RecipezResponseUtils ]###################################
class RecipezResponseUtils:
    """
    A utility class for processing and injecting response headers, generating cookies,
    and setting Content Security Policy (CSP) headers.
    """

    #########################[ start process_response ]#######################
    @staticmethod
    def process_response(
        request: "Request", template: str, script_nonce: str, link_nonce: str, **kwargs
    ) -> "Response":
        """
        Processes the response by rendering a template and injecting necessary headers.

        Parameters:
            request (Request): The Flask request object.
            template (str): The name of the template to render.
            script_nonce (str): A nonce value for script-src in CSP.
            link_nonce (str): A nonce value for style-src in CSP.
            **kwargs: Additional keyword arguments to pass to the template.

        Returns:
            Response: Flask response.
        """
        response = make_response(
            render_template(
                template,
                script_nonce=script_nonce,
                link_nonce=link_nonce,
                **kwargs,
            )
        )
        return RecipezResponseUtils.inject_response_headers(
            request=request,
            response=response,
            script_nonce=script_nonce,
            link_nonce=link_nonce,
        )

    #########################[ end process_response ]#########################

    #########################[ start inject_response_headers ]#################
    @staticmethod
    def inject_response_headers(
        request: request, response: make_response, script_nonce: str, link_nonce: str
    ) -> make_response:
        """
        Injects necessary headers into the response.

        Parameters:
            request (request): The Flask request object.
            response (make_response): The response object to modify.
            script_nonce (str): A nonce value for script-src in CSP.
            link_nonce (str): A nonce value for style-src in CSP.

        Returns:
            make_response: The modified response object with headers injected.
        """
        return RecipezResponseUtils.generate_csp(response, script_nonce, link_nonce)

    #########################[ end inject_response_headers ]##################

    #########################[ start generate_nonces ]#########################
    @staticmethod
    def generate_nonces() -> (str, str):
        """
        Generates nonce values for script-src and style-src in CSP.

        Returns:
            tuple: A tuple containing the script_nonce and link_nonce.
        """
        script_nonce = secrets.token_hex(16)
        link_nonce = secrets.token_hex(16)
        return script_nonce, link_nonce

    #########################[ end generate_nonces ]###########################

    #########################[ start generate_csp ]###########################
    @staticmethod
    def generate_csp(
        response: make_response, script_nonce: str, link_nonce: str
    ) -> make_response:
        """
        Generates and sets the Content Security Policy (CSP) header in the response.

        Parameters:
            response (make_response): The response object to modify.
            script_nonce (str): A nonce value for script-src in CSP.
            link_nonce (str): A nonce value for style-src in CSP.

        Returns:
            make_response: The modified response object with the CSP header set.
        """
        csp_header = (
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{script_nonce}'; "
            f"style-src 'self' https://fonts.googleapis.com 'nonce-{link_nonce}'; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "object-src 'none'; "
            "base-uri 'none'; "
            "frame-ancestors 'none'; "
        )

        response.headers["Content-Security-Policy"] = csp_header
        return response

    #########################[ end generate_csp ]#############################


###################################[ end RecipezResponseUtils ]####################################
