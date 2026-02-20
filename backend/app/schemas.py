from pydantic import AnyUrl, BaseModel, EmailStr
from typing import List, Literal

class Stage(BaseModel):
    target: int
    duration: str

class RunRequest(BaseModel):
    project_name: str
    url: AnyUrl
    stages: List[Stage]


class LoginPayload(BaseModel):
    identifier: str
    password: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Literal["admin", "user"] = "user"


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str


class UserOut(BaseModel):
    id: str
    username: str
    email: str
    role: Literal["admin", "user"]
