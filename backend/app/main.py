from __future__ import annotations

import io
import json
import os
import uuid

import pandas as pd
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import asc, desc, distinct, func, select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Contest, ContestFeedback, ContestResult
from .schemas import (
    ClassSuggestionResponse,
    ContestItem,
    ContestListResponse,
    FeedbackCreateRequest,
    FeedbackItem,
    FeedbackListResponse,
    LeaderboardResponse,
    LeaderboardRow,
    MessageResponse,
    StudentResultResponse,
    UploadContestMapping,
)
from .services import transform_contest_dataframe

load_dotenv()

app = FastAPI(title="Multi-Contest Analytics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/upload-contest", response_model=MessageResponse)
async def upload_contest(
    file: UploadFile = File(...),
    mapping_json: str = Form(...),
    db: Session = Depends(get_db),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file Excel .xlsx hoặc .xls")

    try:
        mapping = UploadContestMapping.model_validate(json.loads(mapping_json))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"JSON mapping không hợp lệ: {exc}") from exc

    content = await file.read()
    header_row_index = mapping.header_row_number - 1 if mapping.header_row_number else 0
    try:
        df = pd.read_excel(io.BytesIO(content), header=header_row_index)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Không thể đọc file Excel: {exc}") from exc

    transformed = transform_contest_dataframe(df, mapping)
    if transformed.empty:
        raise HTTPException(status_code=400, detail="Không có dữ liệu hợp lệ sau khi xử lý")

    benchmark = float(transformed["total_score"].mean().round(4))

    contest = Contest(
        name=mapping.contest_name,
        benchmark_score=benchmark,
        config={
            "id_col": mapping.id_col,
            "name_col": mapping.name_col,
            "class_col": mapping.class_col,
            "component_score_cols": mapping.component_score_cols,
            "weights": mapping.weights or {},
            "header_row_number": mapping.header_row_number,
        },
    )
    db.add(contest)
    db.flush()

    rows = []
    for _, row in transformed.iterrows():
        rows.append(
            ContestResult(
                contest_id=contest.id,
                student_id=row["student_id"],
                full_name=row["full_name"],
                class_name=row["class_name"],
                component_scores=row["component_scores"],
                total_score=float(row["total_score"]),
                global_rank=int(row["global_rank"]),
                class_rank=int(row["class_rank"]),
                percentile=float(row["percentile"]),
            )
        )

    db.add_all(rows)
    db.commit()

    return MessageResponse(
        message="Upload dữ liệu kỳ thi thành công",
        data={
            "contest_id": str(contest.id),
            "participants": len(rows),
            "benchmark_score": benchmark,
        },
    )


@app.get("/contests", response_model=ContestListResponse)
def get_contests(db: Session = Depends(get_db)):
    participant_count_subquery = (
        select(ContestResult.contest_id, func.count(ContestResult.id).label("participant_count"))
        .group_by(ContestResult.contest_id)
        .subquery()
    )

    query = (
        select(
            Contest.id,
            Contest.name,
            Contest.benchmark_score,
            Contest.created_at,
            func.coalesce(participant_count_subquery.c.participant_count, 0),
        )
        .outerjoin(participant_count_subquery, Contest.id == participant_count_subquery.c.contest_id)
        .order_by(desc(Contest.created_at))
    )

    rows = db.execute(query).all()
    contests = [
        ContestItem(
            id=row[0],
            name=row[1],
            benchmark_score=row[2],
            created_at=row[3],
            participant_count=row[4],
        )
        for row in rows
    ]
    return ContestListResponse(contests=contests)


@app.get("/results/{contest_id}/{student_id}", response_model=StudentResultResponse)
def get_student_result(contest_id: uuid.UUID, student_id: str, db: Session = Depends(get_db)):
    contest = db.get(Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Không tìm thấy kỳ thi")

    result = (
        db.query(ContestResult)
        .filter(ContestResult.contest_id == contest_id, ContestResult.student_id == student_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy thí sinh trong kỳ thi")

    return StudentResultResponse(
        contest_id=contest_id,
        student_id=result.student_id,
        full_name=result.full_name,
        class_name=result.class_name,
        component_scores=result.component_scores,
        total_score=result.total_score,
        global_rank=result.global_rank,
        class_rank=result.class_rank,
        percentile=result.percentile,
        benchmark_score=contest.benchmark_score,
        score_difference_from_benchmark=round(result.total_score - contest.benchmark_score, 4),
    )


@app.get("/leaderboard/{contest_id}", response_model=LeaderboardResponse)
def get_leaderboard(
    contest_id: uuid.UUID,
    class_name: str | None = Query(default=None),
    sort_by: str = Query(default="global_rank"),
    order: str = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    contest = db.get(Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Không tìm thấy kỳ thi")

    query = db.query(ContestResult).filter(ContestResult.contest_id == contest_id)

    if class_name:
        query = query.filter(ContestResult.class_name == class_name)

    if sort_by in {"total_score", "global_rank", "class_rank", "percentile", "student_id", "full_name", "class_name"}:
        sort_column = getattr(ContestResult, sort_by)
    else:
        component_cols = contest.config.get("component_score_cols", []) if contest.config else []
        if sort_by in component_cols:
            sort_column = ContestResult.component_scores[sort_by].astext.cast(float)
        else:
            raise HTTPException(status_code=400, detail="sort_by không hợp lệ")

    order_fn = asc if order.lower() == "asc" else desc
    total_items = query.count()

    rows = (
        query.order_by(order_fn(sort_column), asc(ContestResult.student_id))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        LeaderboardRow(
            student_id=row.student_id,
            full_name=row.full_name,
            class_name=row.class_name,
            component_scores=row.component_scores,
            total_score=row.total_score,
            global_rank=row.global_rank,
            class_rank=row.class_rank,
            percentile=row.percentile,
        )
        for row in rows
    ]

    return LeaderboardResponse(
        contest_id=contest_id,
        total_items=total_items,
        page=page,
        page_size=page_size,
        items=items,
    )


@app.get("/suggest-classes/{contest_id}", response_model=ClassSuggestionResponse)
def suggest_classes(
    contest_id: uuid.UUID,
    q: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    contest = db.get(Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Không tìm thấy kỳ thi")

    query = select(distinct(ContestResult.class_name)).where(ContestResult.contest_id == contest_id)
    if q:
        query = query.where(ContestResult.class_name.ilike(f"%{q}%"))

    classes = [r[0] for r in db.execute(query.limit(limit)).all()]
    return ClassSuggestionResponse(classes=classes)


@app.post("/contests/{contest_id}/feedback", response_model=MessageResponse)
def create_feedback(contest_id: uuid.UUID, payload: FeedbackCreateRequest, db: Session = Depends(get_db)):
    contest = db.get(Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Không tìm thấy kỳ thi")

    feedback = ContestFeedback(
        contest_id=contest_id,
        author_name=payload.author_name,
        content=payload.content,
        attachment_url=payload.attachment_url,
        status="pending",
    )
    db.add(feedback)
    db.commit()

    return MessageResponse(message="Đã ghi nhận phản hồi, đang chờ duyệt")


@app.get("/contests/{contest_id}/feedback", response_model=FeedbackListResponse)
def get_feedback(contest_id: uuid.UUID, include_pending: bool = False, db: Session = Depends(get_db)):
    contest = db.get(Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Không tìm thấy kỳ thi")

    query = db.query(ContestFeedback).filter(ContestFeedback.contest_id == contest_id)
    if not include_pending:
        query = query.filter(ContestFeedback.status == "approved")

    rows = query.order_by(desc(ContestFeedback.created_at)).all()
    return FeedbackListResponse(
        items=[
            FeedbackItem(
                id=row.id,
                author_name=row.author_name,
                content=row.content,
                attachment_url=row.attachment_url,
                status=row.status,
                created_at=row.created_at,
            )
            for row in rows
        ]
    )


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
