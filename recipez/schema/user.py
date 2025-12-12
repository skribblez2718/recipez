from pydantic import BaseModel, EmailStr


###################################[ start CreateUserSchema ]###################################
class CreateUserSchema(BaseModel):
    """ """

    email: EmailStr


###################################[ end CreateUserSchema ]#####################################


###################################[ start ReadUserByEmailSchema ]###################################
class ReadUserByEmailSchema(BaseModel):
    """ """

    email: EmailStr


###################################[ end ReadUserByEmailSchema ]#####################################
