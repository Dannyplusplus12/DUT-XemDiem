from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy.orm import Session

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.database import Base, SessionLocal, engine
from app.schemas import UploadContestMapping
from app.services import import_excel_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Nhập file Excel kỳ thi vào cơ sở dữ liệu")
    parser.add_argument("excel", type=Path, help="Đường dẫn tới file Excel (.xlsx)")
    parser.add_argument(
        "--mapping",
        type=Path,
        help="File JSON mô tả mapping cột (mặc định dùng cấu hình chuẩn SBD/Họ và tên/Lớp/NGHE/ĐỌC)",
    )
    parser.add_argument(
        "--contest-name",
        dest="contest_name",
        type=str,
        help="Ghi đè tên kỳ thi (ưu tiên hơn mapping)",
    )
    return parser.parse_args()


def load_mapping(path: Path | None, contest_name_override: str | None) -> UploadContestMapping:
    if path:
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {
            "contest_name": "Kỳ thi tiếng Anh",
            "header_row": 8,
            "id_col": "SBD",
            "name_col": "Họ và tên",
            "class_col": "Lớp",
            "component_score_cols": ["NGHE", "ĐỌC"],
        }
    if contest_name_override:
        data["contest_name"] = contest_name_override
    return UploadContestMapping.model_validate(data)


def main() -> None:
    args = parse_args()
    if not args.excel.exists():
        raise SystemExit(f"Không tìm thấy file Excel: {args.excel}")

    mapping = load_mapping(args.mapping, args.contest_name)

    Base.metadata.create_all(bind=engine)
    file_bytes = args.excel.read_bytes()

    db: Session = SessionLocal()
    try:
        contest = import_excel_file(db, file_bytes, mapping)
        print("Đã lưu kỳ thi", contest.name)
        print("contest_id:", contest.id)
    finally:
        db.close()


if __name__ == "__main__":
    main()
