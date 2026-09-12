from typing import Literal

from pydantic import BaseModel


class AdminRoleUpdate(BaseModel):
    role: Literal["user", "admin"]
