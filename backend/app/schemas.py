from pydantic import BaseModel, HttpUrl
from typing import List

class Stage(BaseModel):
    target: int
    duration: str

class RunRequest(BaseModel):
    project_name: str
    url: HttpUrl
    stages: List[Stage]
