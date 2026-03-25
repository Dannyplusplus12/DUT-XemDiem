import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class UploadContestMapping(BaseModel):
    contest_name: str = Field(..., min_length=1)
    id_col: str
    name_col: str
    class_col: str
    component_score_cols: list[str]
    weights: dict[str, float] | None = None


class ContestItem(BaseModel):
    id: uuid.UUID
    name: str
    benchmark_score: float
    participant_count: int
    created_at: datetime


class ContestListResponse(BaseModel):
    contests: list[ContestItem]


class StudentResultResponse(BaseModel):
    contest_id: uuid.UUID
    student_id: str
    full_name: str
    class_name: str
    component_scores: dict[str, float]
    total_score: float
    global_rank: int
    class_rank: int
    percentile: float
    benchmark_score: float
    score_difference_from_benchmark: float


class LeaderboardRow(BaseModel):
    student_id: str
    full_name: str
    class_name: str
    component_scores: dict[str, float]
    total_score: float
    global_rank: int
    class_rank: int
    percentile: float


class LeaderboardResponse(BaseModel):
    contest_id: uuid.UUID
    total_items: int
    page: int
    page_size: int
    items: list[LeaderboardRow]


class ClassSuggestionResponse(BaseModel):
    classes: list[str]


class FeedbackCreateRequest(BaseModel):
    author_name: str
    content: str
    attachment_url: str | None = None


class FeedbackItem(BaseModel):
    id: uuid.UUID
    author_name: str
    content: str
    attachment_url: str | None
    status: str
    created_at: datetime


class FeedbackListResponse(BaseModel):
    items: list[FeedbackItem]


class MessageResponse(BaseModel):
    message: str
    data: dict[str, Any] | None = None
