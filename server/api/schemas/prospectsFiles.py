from datetime import datetime
from typing import List
from fastapi.datastructures import UploadFile

from pydantic import BaseModel

class ProspectFile(BaseModel):
    id: int
    file: str
    total_rows: int
    prospects_before_upload: int
    preview: List[List[str]]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ProspectFileAddToDatabase(BaseModel):
    email_index: int
    first_name_index: int
    last_name_index: int
    force: bool
    has_header: bool


class ProspectFileUploadResponse(BaseModel):
    #upload response
    id: int
    preview: List[List[str]]

class ProspectFileAddCSVResponse(BaseModel):
    id: int
    total_rows: int
    done: int

class ProspectFileProgressResponse(BaseModel):
    total: int
    done: int