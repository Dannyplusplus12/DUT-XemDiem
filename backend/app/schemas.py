from __future__ import annotations

# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class UploadContestMapping(BaseModel):
    contest_name: str = Field(..., description="Tên kỳ thi hiển thị trên hệ thống")
    description: str | None = Field(default=None, description="Mô tả ngắn (tuỳ chọn)")
    header_row: int = Field(default=8, ge=1, description="Dòng tiêu đề trong Excel (1-based)")
    id_col: str = Field(default="SBD")
    name_col: str = Field(default="Họ và tên")
    class_col: str = Field(default="Lớp")
    component_score_cols: List[str] = Field(default_factory=lambda: ["NGHE", "ĐỌC"])
    weights: dict[str, float] | None = Field(default=None, description="Trọng số cho từng cột điểm thành phần")


class ContestSummary(BaseModel):
    id: str
    name: str
    description: str | None
    benchmark_score: float
    participant_count: int
    created_at: datetime


class ContestListResponse(BaseModel):
    contests: list[ContestSummary]


class PersonalResultResponse(BaseModel):
    contest_id: str
    student_id: str
    full_name: str
    class_name: str
    component_scores: dict[str, float]
    total_score: float
    global_rank: int
    class_rank: int
    percentile: float
    benchmark_score: float
    gap_from_average: float


class LeaderboardRow(BaseModel):
    student_id: str
    full_name: str
    class_name: str
    total_score: float
    global_rank: int
    class_rank: int
    percentile: float
    component_scores: dict[str, float]


class LeaderboardResponse(BaseModel):
    contest_id: str
    page: int
    page_size: int
    total_items: int
    items: list[LeaderboardRow]


class MessageResponse(BaseModel):
    message: str
    detail: dict | None = None
