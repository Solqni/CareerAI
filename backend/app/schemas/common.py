from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    """支持从 SQLAlchemy ORM 对象读取的基类。"""

    model_config = ConfigDict(from_attributes=True)
