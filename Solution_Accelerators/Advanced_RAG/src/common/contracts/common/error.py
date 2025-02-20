from typing import Optional

from pydantic import BaseModel


class Error(BaseModel):
    error_str: Optional[str] = None
    retry: Optional[bool] = None
    status_code: Optional[int] = 500
