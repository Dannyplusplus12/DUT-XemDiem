from __future__ import annotations

import pandas as pd
from fastapi import HTTPException

from .schemas import UploadContestMapping


REQUIRED_SYSTEM_COLUMNS = [
    "student_id",
    "full_name",
    "class_name",
]


def _validate_mapping(df: pd.DataFrame, mapping: UploadContestMapping) -> None:
    required_cols = [
        mapping.id_col,
        mapping.name_col,
        mapping.class_col,
        *mapping.component_score_cols,
    ]

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Thiếu cột trong file Excel: {', '.join(missing)}")


def transform_contest_dataframe(df: pd.DataFrame, mapping: UploadContestMapping) -> pd.DataFrame:
    _validate_mapping(df, mapping)

    transformed = pd.DataFrame()
    transformed["student_id"] = df[mapping.id_col].astype(str).str.strip()
    transformed["full_name"] = df[mapping.name_col].astype(str).str.strip()
    transformed["class_name"] = df[mapping.class_col].astype(str).str.strip()

    component_scores = df[mapping.component_score_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

    if mapping.weights:
        weight_series = pd.Series(mapping.weights, dtype=float)
        unknown_weight_cols = set(weight_series.index) - set(mapping.component_score_cols)
        if unknown_weight_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Cột trọng số không hợp lệ: {', '.join(sorted(unknown_weight_cols))}",
            )

        normalized_weights = pd.Series(0.0, index=mapping.component_score_cols)
        normalized_weights.update(weight_series)
        if normalized_weights.sum() <= 0:
            raise HTTPException(status_code=400, detail="Tổng trọng số phải lớn hơn 0")
        normalized_weights = normalized_weights / normalized_weights.sum()
        transformed["total_score"] = component_scores.mul(normalized_weights, axis=1).sum(axis=1)
    else:
        transformed["total_score"] = component_scores.sum(axis=1)

    transformed["component_scores"] = component_scores.to_dict(orient="records")

    transformed = transformed[transformed["student_id"] != ""].copy()
    transformed.sort_values(by=["total_score", "student_id"], ascending=[False, True], inplace=True)

    transformed["global_rank"] = transformed["total_score"].rank(method="min", ascending=False).astype(int)
    transformed["class_rank"] = transformed.groupby("class_name")["total_score"].rank(method="min", ascending=False).astype(int)

    total_students = len(transformed)
    if total_students <= 1:
        transformed["percentile"] = 100.0
    else:
        transformed["percentile"] = ((total_students - transformed["global_rank"]) / (total_students - 1) * 100).round(2)

    transformed["total_score"] = transformed["total_score"].round(4)
    return transformed
