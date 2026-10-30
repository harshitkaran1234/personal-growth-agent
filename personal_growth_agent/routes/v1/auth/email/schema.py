from pydantic import BaseModel, EmailStr


class EmailOTPRequest(BaseModel):
    email: EmailStr


class EmailOTPResponse(BaseModel):
    email: str
    expires_at: int
    retry_after: int


class ValidateOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class ValidateOTPResponse(BaseModel):
    access_token: str
    is_new_user: bool
