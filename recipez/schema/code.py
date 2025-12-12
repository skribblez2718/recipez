from pydantic import BaseModel, EmailStr, constr
from uuid import UUID
from typing import Optional


###################################[ start CreateCodeSchema ]###################################
class CreateCodeSchema(BaseModel):
    """
    Schema for validating email-based login initiation.

    Attributes:
        email (EmailStr): A valid email address for the user.
        session_id (UUID): A 32-character hexadecimal session identifier.
    """

    email: EmailStr
    session_id: UUID


###################################[ end CreateCodeSchema ]#####################################


###################################[ start ReadCodeSchema ]#####################################
class ReadCodeSchema(BaseModel):
    """
    Schema for validating email-based login initiation.

    Attributes:
        email (EmailStr): A valid email address for the user.
        session_id (UUID): A Flask session_id
    """

    email: EmailStr
    session_id: UUID


###################################[ end ReadCodeSchema ]#######################################


###################################[ start CodeDataSchema ]#####################################
class CodeDataSchema(BaseModel):
    """
    Schema for code data returned from the database.

    Attributes:
        code_id (str): UUID of the code.
        code_count (int): Count of code usage.
        code_value (str): Hashed code value.
        code_issued_at (Optional[str]): ISO formatted timestamp when the code was issued.
        code_expires_at (Optional[str]): ISO formatted timestamp when the code expires.
        code_attempts (int): Number of attempts made with this code.
        code_cooldown (Optional[str]): ISO formatted timestamp for cooldown period after failed attempts.
        code_email (str): Email associated with the code.
        code_session_id (str): Session UUID associated with the code.
    """

    code_id: str
    code_count: int
    code_value: str
    code_issued_at: Optional[str] = None
    code_expires_at: Optional[str] = None
    code_attempts: int
    code_cooldown: Optional[str] = None
    code_email: str
    code_session_id: str

    class Config:
        validate_assignment = True


###################################[ end CodeDataSchema ]#######################################


###################################[ start UpdateCodeSchema ]#####################################
class UpdateCodeSchema(BaseModel):
    """
    Schema for updating a verification code.

    Attributes:
        email (EmailStr): A valid email address for the user.
        code (CodeDataSchema): The code data object returned from read_code_api.
    """

    code: CodeDataSchema
    email: EmailStr


###################################[ end UpdateCodeSchema ]#######################################


###################################[ start VerifyCodeSchema ]#####################################
class VerifyCodeSchema(BaseModel):
    """
    Schema for validating a verification code.

    Attributes:
        code (CodeDataSchema): The code data object returned from read_code_api.
        received_code: The code entered by user. Only allows unambiguous characters
            (letters and digits excluding 0/O/o, 1/l/I/i, 5/S/s, 8/B/b, 2/Z/z).
    """

    code: CodeDataSchema
    # Pattern matches unambiguous charset: 346789ACDEFGHJKMNPQRTUVWXYacdefghjkmnpqrtuvwxy
    received_code: constr(pattern=r"^[346789ACDEFGHJKMNPQRTUVWXYacdefghjkmnpqrtuvwxy]{4}-[346789ACDEFGHJKMNPQRTUVWXYacdefghjkmnpqrtuvwxy]{4}$")


###################################[ end VerifyCodeSchema ]#######################################


###################################[ start CodeDeleteSchema ]#####################################
class DeleteCodeSchema(BaseModel):
    """
    Schema for validating a verification code.

    Attributes:
        code_id (UUID): The UUID of the code to delete.
    """

    code_id: UUID


###################################[ end CodeDeleteSchema ]#######################################
