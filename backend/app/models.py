import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .database import Base


class Contest(Base):
    __tablename__ = "contests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    benchmark_score = Column(Float, nullable=False, default=0)
    config = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    results = relationship("ContestResult", back_populates="contest", cascade="all, delete-orphan")
    feedbacks = relationship("ContestFeedback", back_populates="contest", cascade="all, delete-orphan")


class ContestResult(Base):
    __tablename__ = "contest_results"
    __table_args__ = (UniqueConstraint("contest_id", "student_id", name="uq_contest_student"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contest_id = Column(UUID(as_uuid=True), ForeignKey("contests.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(100), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    class_name = Column(String(100), nullable=False, index=True)
    component_scores = Column(JSONB, nullable=False, default=dict)
    total_score = Column(Float, nullable=False)
    global_rank = Column(Integer, nullable=False, index=True)
    class_rank = Column(Integer, nullable=False)
    percentile = Column(Float, nullable=False)

    contest = relationship("Contest", back_populates="results")


class ContestFeedback(Base):
    __tablename__ = "contest_feedbacks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contest_id = Column(UUID(as_uuid=True), ForeignKey("contests.id", ondelete="CASCADE"), nullable=False)
    author_name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    attachment_url = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    contest = relationship("Contest", back_populates="feedbacks")
