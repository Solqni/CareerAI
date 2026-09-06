from app.schemas.common import ORMBase


class InterviewSessionOut(ORMBase):
    id: int
    user_id: int
    job_id: int | None = None
    status: str
