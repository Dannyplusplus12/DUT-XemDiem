from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Contest, ContestResult
from .schemas import (
    ContestListResponse,
    ContestSummary,
    LeaderboardResponse,
    LeaderboardRow,
    MessageResponse,
    PersonalResultResponse,
    UploadContestMapping,
)
from .services import import_excel_file

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cổng tra cứu kết quả thi", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/contests/upload", response_model=MessageResponse)
async def upload_contest(
    file: UploadFile = File(...),
    mapping_json: str = Form(...),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp file Excel (.xlsx hoặc .xls)")

    try:
        mapping = UploadContestMapping.model_validate(json.loads(mapping_json))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"mapping_json không hợp lệ: {exc}") from exc

    content = await file.read()
    contest = import_excel_file(db, content, mapping)
    return MessageResponse(message="Đã lưu kỳ thi", detail={"contest_id": contest.id})


@app.get("/contests", response_model=ContestListResponse)
def list_contests(db: Session = Depends(get_db)):
    rows = (
        db.query(
            Contest.id,
            Contest.name,
            Contest.description,
            Contest.benchmark_score,
            Contest.created_at,
            func.count(ContestResult.id),
        )
        .outerjoin(ContestResult, Contest.id == ContestResult.contest_id)
        .group_by(Contest.id)
        .order_by(Contest.created_at.desc())
        .all()
    )

    contests = [
        ContestSummary(
            id=row[0],
            name=row[1],
            description=row[2],
            benchmark_score=row[3],
            created_at=row[4],
            participant_count=row[5],
        )
        for row in rows
    ]
    return ContestListResponse(contests=contests)


@app.get("/contests/{contest_id}/results/{student_id}", response_model=PersonalResultResponse)
def get_personal_result(contest_id: str, student_id: str, db: Session = Depends(get_db)):
    contest = db.get(Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Không tìm thấy kỳ thi")

    result = (
        db.query(ContestResult)
        .filter(ContestResult.contest_id == contest_id, ContestResult.student_id == student_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy thí sinh")

    component_scores = json.loads(result.component_scores)
    return PersonalResultResponse(
        contest_id=contest_id,
        student_id=result.student_id,
        full_name=result.full_name,
        class_name=result.class_name,
        component_scores=component_scores,
        total_score=result.total_score,
        global_rank=result.global_rank,
        class_rank=result.class_rank,
        percentile=result.percentile,
        benchmark_score=contest.benchmark_score,
        gap_from_average=round(result.total_score - contest.benchmark_score, 2),
    )


@app.get("/contests/{contest_id}/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    contest_id: str,
    class_name: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    contest = db.get(Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Không tìm thấy kỳ thi")

    query = db.query(ContestResult).filter(ContestResult.contest_id == contest_id)
    if class_name:
        query = query.filter(ContestResult.class_name == class_name)

    total_items = query.count()
    rows = (
        query.order_by(ContestResult.global_rank)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        LeaderboardRow(
            student_id=row.student_id,
            full_name=row.full_name,
            class_name=row.class_name,
            total_score=row.total_score,
            global_rank=row.global_rank,
            class_rank=row.class_rank,
            percentile=row.percentile,
            component_scores=json.loads(row.component_scores),
        )
        for row in rows
    ]

    return LeaderboardResponse(
        contest_id=contest_id,
        page=page,
        page_size=page_size,
        total_items=total_items,
        items=items,
    )


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
