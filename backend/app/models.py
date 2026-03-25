from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Contest(Base):
    __tablename__ = "contests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    benchmark_score = Column(Float, default=0, nullable=False)

    results = relationship("ContestResult", back_populates="contest", cascade="all, delete-orphan")


class ContestResult(Base):
    __tablename__ = "contest_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contest_id = Column(String(36), ForeignKey("contests.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(100), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    class_name = Column(String(100), nullable=False)
    component_scores = Column(Text, nullable=False)
    total_score = Column(Float, nullable=False, index=True)
    global_rank = Column(Integer, nullable=False)
    class_rank = Column(Integer, nullable=False)
    percentile = Column(Float, nullable=False)

    contest = relationship("Contest", back_populates="results")
