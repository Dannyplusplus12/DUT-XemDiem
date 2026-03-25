from __future__ import annotations

# -*- coding: utf-8 -*-
import io
import json
from typing import Iterable

import pandas as pd
from sqlalchemy.orm import Session

from .models import Contest, ContestResult
from .schemas import UploadContestMapping


class ValidationError(Exception):
    """Custom validation error for Excel processing."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def _normalize_component_scores(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    component_df = df[list(columns)].apply(pd.to_numeric, errors="coerce").fillna(0)
    return component_df


def _calculate_total_scores(component_df: pd.DataFrame, weights: dict[str, float] | None) -> pd.Series:
    if not weights:
        return component_df.sum(axis=1)

    weight_series = pd.Series(weights, dtype=float)
    missing = sorted(set(weight_series.index) - set(component_df.columns))
    if missing:
        raise ValidationError(f"Cột trọng số không hợp lệ: {', '.join(missing)}")

    normalized_weights = weight_series.reindex(component_df.columns).fillna(0.0)
    weight_sum = normalized_weights.sum()
    if weight_sum <= 0:
        raise ValidationError("Tổng trọng số phải lớn hơn 0")

    normalized_weights /= weight_sum
    return component_df.mul(normalized_weights, axis=1).sum(axis=1)


def transform_excel(content: bytes, mapping: UploadContestMapping) -> pd.DataFrame:
    header_index = mapping.header_row - 1
    df = pd.read_excel(io.BytesIO(content), header=header_index)

    required_cols = [mapping.id_col, mapping.name_col, mapping.class_col, *mapping.component_score_cols]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValidationError(f"Thiếu cột trong Excel: {', '.join(missing)}")

    dataset = pd.DataFrame()
    dataset["student_id"] = df[mapping.id_col].fillna("").astype(str).str.strip()
    dataset["full_name"] = df[mapping.name_col].fillna("").astype(str).str.strip()
    dataset["class_name"] = df[mapping.class_col].fillna("").astype(str).str.strip()

    component_df = _normalize_component_scores(df, mapping.component_score_cols)
    dataset["component_scores"] = component_df.to_dict(orient="records")
    dataset["total_score"] = _calculate_total_scores(component_df, mapping.weights).round(2)

    # Filter out empty rows and NaN values
    dataset = dataset[
        (dataset["student_id"] != "") &
        (dataset["student_id"] != "nan") &
        (dataset["full_name"] != "") &
        (dataset["class_name"] != "") &
        (dataset["total_score"].notna())
    ].copy()

    if dataset.empty:
        raise ValidationError("Không tìm thấy thí sinh hợp lệ")

    dataset.sort_values(by=["total_score", "student_id"], ascending=[False, True], inplace=True)
    dataset = dataset.reset_index(drop=True)
    dataset["global_rank"] = dataset["total_score"].rank(method="min", ascending=False).fillna(dataset.shape[0]).astype(int)

    # Calculate class_rank: rank within each class by total_score
    dataset["class_rank"] = dataset.groupby("class_name", sort=False)["total_score"].rank(method="min", ascending=False).astype(int)

    total = len(dataset)
    if total <= 1:
        dataset["percentile"] = 100.0
    else:
        dataset["percentile"] = ((total - dataset["global_rank"]) / (total - 1) * 100).round(2)

    return dataset.reset_index(drop=True)


def persist_contest(db: Session, mapping: UploadContestMapping, dataset: pd.DataFrame) -> Contest:
    benchmark = float(dataset["total_score"].mean().round(2))

    contest = Contest(
        name=mapping.contest_name,
        description=mapping.description,
        benchmark_score=benchmark,
    )
    db.add(contest)
    db.flush()

    results = []
    for row in dataset.to_dict(orient="records"):
        results.append(
            ContestResult(
                contest_id=contest.id,
                student_id=row["student_id"],
                full_name=row["full_name"],
                class_name=row["class_name"],
                component_scores=json.dumps(row["component_scores"], ensure_ascii=False),
                total_score=float(row["total_score"]),
                global_rank=int(row["global_rank"]),
                class_rank=int(row["class_rank"]),
                percentile=float(row["percentile"]),
            )
        )

    db.add_all(results)
    db.commit()
    db.refresh(contest)
    return contest


def import_excel_file(db: Session, file_bytes: bytes, mapping: UploadContestMapping) -> Contest:
    dataset = transform_excel(file_bytes, mapping)
    return persist_contest(db, mapping, dataset)
