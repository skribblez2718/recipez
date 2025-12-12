from pydantic import BaseModel, EmailStr, constr
from uuid import UUID


###################################[ start LoginEmailSchema ]###################################
class LoginEmailSchema(BaseModel):
    """
    Schema for validating email-based login initiation.

    Attributes:
        email (EmailStr): A valid email address for the user.
        session_id (UUID): A Flask session_id
    """

    email: EmailStr
    session_id: UUID


###################################[ end LoginEmailSchema ]#####################################


###################################[ start LoginVerifySchema ]###################################
class LoginVerifySchema(BaseModel):
    """
    Schema for verifying an OTP code against the session and user email.

    Attributes:
        email (EmailStr): A valid email address for the user.
        code (str): The verification code in the format XXX-XXX (alphanumeric).
        session_id (UUID): A Flask session_id
    """

    email: EmailStr
    code: constr(pattern=r"^[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}$")
    session_id: UUID


###################################[ end LoginVerifySchema ]#####################################


###################################[ start CeateUserSchema ]###################################
class CeateUserSchema(BaseModel):
    """
    Schema for creating a new user.

    Attributes:
        email (EmailStr): A valid email address for the user.
    """

    email: EmailStr


###################################[ end CeateUserSchema ]#####################################
