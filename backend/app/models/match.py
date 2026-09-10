from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime, Float
from app.models.base import Base
from sqlalchemy.orm import relationship
from datetime import datetime


class MatchReport(Base):
    __tablename__ = "match_report"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), index=True)
    job_id = Column(Integer, ForeignKey("job_analysis.id"), index=True)
    position_title = Column(String(255), nullable=True)
    skill_match = Column(Float, nullable=True)
    experience_match = Column(Float, nullable=True)
    education_match = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    gaps_json = Column(JSON, nullable=True)  # 存储 GapItem 列表的 JSON
    recommendations_json = Column(JSON, nullable=True)  # 存储 Recommendation 列表的 JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    gaps = relationship("GapItem", back_populates="report", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="report", cascade="all, delete-orphan")
    learning_plan = relationship("LearningPlan", back_populates="report", cascade="all, delete-orphan")


class GapItem(Base):
    __tablename__ = "gap_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(100), ForeignKey("match_report.id"), index=True)
    type = Column(String(32), nullable=True)
    skill_name = Column(String(128), nullable=True)
    current_level = Column(Integer, nullable=True)
    target_level = Column(Integer, nullable=True)
    current_years = Column(Float, nullable=True)
    target_years = Column(Integer, nullable=True)
    current_education = Column(String(128), nullable=True)
    target_education = Column(String(128), nullable=True)
    experience_type = Column(String(128), nullable=True)
    severity = Column(String(16), nullable=True)
    description = Column(Text, nullable=True)

    report = relationship("MatchReport", back_populates="gaps")


class Recommendation(Base):
    __tablename__ = "recommendation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(100), ForeignKey("match_report.id"), index=True)
    type = Column(String(64), nullable=True)
    description = Column(Text, nullable=True)
    priority = Column(String(16), nullable=True)
    estimated_time = Column(String(64), nullable=True)

    report = relationship("MatchReport", back_populates="recommendations")


class LearningPlan(Base):
    __tablename__ = "learning_plan"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), index=True)
    report_id = Column(String(100), ForeignKey("match_report.id"), index=True)
    content_json = Column(JSON, nullable=True)
    status = Column(String(32), default="pending")

    report = relationship("MatchReport", back_populates="learning_plan")
    tasks = relationship("LearningTask", back_populates="plan", cascade="all, delete-orphan")


class LearningTask(Base):
    __tablename__ = "learning_task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("learning_plan.id"), index=True)
    task_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    resource_url = Column(String(512), nullable=True)
    status = Column(String(32), default="todo")
    due_date = Column(String(32), nullable=True)

    plan = relationship("LearningPlan", back_populates="tasks")