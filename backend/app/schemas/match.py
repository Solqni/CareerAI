from app.schemas.common import ORMBase


class MatchReportOut(ORMBase):
    id: int
    user_id: int
    job_id: int
    total_score: int
    summary: str | None = None
    detail_json: dict | None = None
