from pydantic import AnyUrl, BaseModel, EmailStr
from typing import List, Literal, Optional

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


class UserLLMSettingsBase(BaseModel):
    provider: Literal["gemini", "openai", "local"] = "gemini"
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    openai_base_url: Optional[str] = None
    temperature: str = "0.2"
    max_tokens: str = "2048"


class UserLLMSettingsUpdate(UserLLMSettingsBase):
    pass


class UserLLMSettingsOut(UserLLMSettingsBase):
    id: str
    user_id: str

    class Config:
        from_attributes = True
