from pydantic import BaseModel
from typing import List

class Stage(BaseModel):
    target: int
    duration: str

class RunRequest(BaseModel):
    project_name: str
    url: str
    stages: List[Stage]
