from __future__ import annotations

# -*- coding: utf-8 -*-
import json
import os
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from sqlalchemy import func
from sqlalchemy.orm import Session

from .database import Base, engine, SessionLocal
from .models import Contest, ContestResult, FileSubmission
from .schemas import UploadContestMapping
from .services import import_excel_file, ValidationError

# Thiết lập UTF-8 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

Base.metadata.create_all(bind=engine)

# ✅ Get absolute path to static folder
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static')

# ✅ Get uploads folder
UPLOADS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
Path(UPLOADS_FOLDER).mkdir(exist_ok=True)

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='')

# ✅ UTF-8 Configuration
app.config["JSON_AS_ASCII"] = False  # Cho phép Unicode trong JSON response
app.config["JSON_SORT_KEYS"] = False
app.json.ensure_ascii = False  # Flask 2.2+

# CORS configuration
CORS(app, resources={r"/*": {"origins": "*", "methods": ["*"], "allow_headers": ["*"]}})

# ✅ Middleware: Đảm bảo mọi response có charset=utf-8
@app.after_request
def ensure_utf8_charset(response):
    """Thêm charset=utf-8 vào mọi response header."""
    content_type = response.headers.get('Content-Type', '')
    if content_type:
        if 'charset' not in content_type:
            if 'application/json' in content_type:
                response.headers['Content-Type'] = 'application/json; charset=utf-8'
            elif 'text/html' in content_type:
                response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

# ✅ Serve static HTML
@app.route('/')
def index():
    return send_from_directory(STATIC_FOLDER, 'index.html')


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})


@app.route("/contests/upload", methods=["POST"])
def upload_contest():
    db: Session = SessionLocal()
    try:
        if "file" not in request.files:
            return jsonify({"detail": "Vui lòng cung cấp file"}), 400

        file = request.files["file"]
        if not file.filename.lower().endswith((".xlsx", ".xls")):
            return (
                jsonify(
                    {"detail": "Vui lòng cung cấp file Excel (.xlsx hoặc .xls)"}
                ),
                400,
            )

        mapping_json = request.form.get("mapping_json")
        if not mapping_json:
            return (
                jsonify({"detail": "Vui lòng cung cấp mapping_json"}),
                400,
            )

        try:
            mapping_dict = json.loads(mapping_json)
            mapping = UploadContestMapping.parse_obj(mapping_dict)
        except Exception as exc:
            return (
                jsonify(
                    {"detail": f"mapping_json không hợp lệ: {exc}"}
                ),
                400,
            )

        try:
            content = file.read()
            contest = import_excel_file(db, content, mapping)
            return (
                jsonify(
                    {
                        "message": "Đã lưu kỳ thi",
                        "detail": {"contest_id": contest.id},
                    }
                ),
                201,
            )
        except ValidationError as e:
            return jsonify({"detail": e.message}), 400
    finally:
        db.close()


@app.route("/contests", methods=["GET"])
def list_contests():
    db: Session = SessionLocal()
    try:
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
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "benchmark_score": row[3],
                "created_at": row[4].isoformat() if row[4] else None,
                "participant_count": row[5],
            }
            for row in rows
        ]
        return jsonify({"contests": contests})
    finally:
        db.close()


@app.route("/contests/<contest_id>/results/<student_id>", methods=["GET"])
def get_personal_result(contest_id, student_id):
    db: Session = SessionLocal()
    try:
        contest = db.get(Contest, contest_id)
        if not contest:
            return jsonify({"detail": "Không tìm thấy kỳ thi"}), 404

        result = (
            db.query(ContestResult)
            .filter(
                ContestResult.contest_id == contest_id,
                ContestResult.student_id == student_id,
            )
            .first()
        )
        if not result:
            return jsonify({"detail": "Không tìm thấy thí sinh"}), 404

        component_scores = json.loads(result.component_scores)
        return jsonify(
            {
                "contest_id": contest_id,
                "student_id": result.student_id,
                "full_name": result.full_name,
                "class_name": result.class_name,
                "component_scores": component_scores,
                "total_score": result.total_score,
                "global_rank": result.global_rank,
                "class_rank": result.class_rank,
                "percentile": result.percentile,
                "benchmark_score": contest.benchmark_score,
                "gap_from_average": round(
                    result.total_score - contest.benchmark_score, 2
                ),
            }
        )
    finally:
        db.close()


@app.route("/contests/<contest_id>/leaderboard", methods=["GET"])
def get_leaderboard(contest_id):
    db: Session = SessionLocal()
    try:
        # Get query params
        class_name = request.args.get("class_name", default=None, type=str)
        page = request.args.get("page", default=1, type=int)
        page_size = request.args.get("page_size", default=50, type=int)

        # Validate query params
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 50
        if page_size > 10000:
            page_size = 10000

        contest = db.get(Contest, contest_id)
        if not contest:
            return jsonify({"detail": "Không tìm thấy kỳ thi"}), 404

        query = db.query(ContestResult).filter(
            ContestResult.contest_id == contest_id
        )
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
            {
                "student_id": row.student_id,
                "full_name": row.full_name,
                "class_name": row.class_name,
                "total_score": row.total_score,
                "global_rank": row.global_rank,
                "class_rank": row.class_rank,
                "percentile": row.percentile,
                "component_scores": json.loads(row.component_scores),
            }
            for row in rows
        ]

        return jsonify(
            {
                "contest_id": contest_id,
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "items": items,
            }
        )
    finally:
        db.close()


@app.route("/contests/<contest_id>/classes", methods=["GET"])
def get_classes(contest_id):
    """Get all unique class names for a contest"""
    db: Session = SessionLocal()
    try:
        contest = db.get(Contest, contest_id)
        if not contest:
            return jsonify({"detail": "Không tìm thấy kỳ thi"}), 404

        classes = (
            db.query(ContestResult.class_name)
            .filter(ContestResult.contest_id == contest_id)
            .distinct()
            .order_by(ContestResult.class_name)
            .all()
        )

        class_list = [c[0] for c in classes if c[0]]
        return jsonify({"classes": class_list})
    finally:
        db.close()


# ✅ FILE SUBMISSION ENDPOINTS
@app.route("/files/submit", methods=["POST"])
def submit_file():
    """Người dùng gửi file Excel"""
    db: Session = SessionLocal()
    try:
        if "file" not in request.files:
            return jsonify({"detail": "Vui lòng cung cấp file"}), 400

        file = request.files["file"]
        if not file.filename.lower().endswith((".xlsx", ".xls")):
            return jsonify({"detail": "Chỉ chấp nhận file Excel (.xlsx hoặc .xls)"}), 400

        contest_name = request.form.get("contest_name", "").strip()
        description = request.form.get("description", "").strip()

        if not contest_name:
            return jsonify({"detail": "Vui lòng nhập tên kỳ thi"}), 400

        # Tạo tên file duy nhất
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join(UPLOADS_FOLDER, safe_filename)

        # Lưu file
        file_content = file.read()
        file_size = len(file_content)

        with open(filepath, "wb") as f:
            f.write(file_content)

        # Lưu metadata vào database
        submission = FileSubmission(
            contest_name=contest_name,
            description=description,
            filename=safe_filename,
            file_size=file_size,
            status="pending"
        )
        db.add(submission)
        db.commit()

        return jsonify({
            "message": "Gửi file thành công",
            "detail": {
                "submission_id": submission.id,
                "filename": safe_filename
            }
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"detail": f"Lỗi: {str(e)}"}), 500
    finally:
        db.close()


@app.route("/files/list", methods=["GET"])
def list_submissions():
    """Liệt kê tất cả file đã submit (Admin)"""
    db: Session = SessionLocal()
    try:
        submissions = (
            db.query(FileSubmission)
            .order_by(FileSubmission.uploaded_at.desc())
            .all()
        )

        items = [
            {
                "id": s.id,
                "contest_name": s.contest_name,
                "description": s.description,
                "filename": s.filename,
                "file_size": f"{s.file_size / 1024:.2f} KB",
                "uploaded_at": s.uploaded_at.isoformat(),
                "status": s.status,
                "notes": s.notes
            }
            for s in submissions
        ]
        return jsonify({"submissions": items})
    finally:
        db.close()


@app.route("/files/<file_id>/import", methods=["POST"])
def import_submission(file_id):
    """Admin import file submit vào hệ thống"""
    db: Session = SessionLocal()
    try:
        submission = db.get(FileSubmission, file_id)
        if not submission:
            return jsonify({"detail": "Không tìm thấy file"}), 404

        filepath = os.path.join(UPLOADS_FOLDER, submission.filename)
        if not os.path.exists(filepath):
            return jsonify({"detail": "File không tồn tại trên server"}), 404

        # Đọc file
        with open(filepath, "rb") as f:
            file_content = f.read()

        # Import vào hệ thống
        mapping = UploadContestMapping(
            contest_name=submission.contest_name,
            description=submission.description,
            header_row=8,
            id_col="Thẻ SV",
            name_col="Họ và tên",
            class_col="Lớp ",
            component_score_cols=["NGHE", "ĐỌC"],
            weights=None
        )

        try:
            contest = import_excel_file(db, file_content, mapping)
            submission.status = "imported"
            submission.notes = f"Imported as contest {contest.id}"
            db.commit()

            return jsonify({
                "message": "Import thành công",
                "detail": {
                    "contest_id": contest.id,
                    "contest_name": contest.name
                }
            }), 201
        except ValidationError as e:
            submission.status = "rejected"
            submission.notes = e.message
            db.commit()
            return jsonify({"detail": f"Lỗi import: {e.message}"}), 400

    except Exception as e:
        db.rollback()
        return jsonify({"detail": f"Lỗi: {str(e)}"}), 500
    finally:
        db.close()


@app.route("/files/<file_id>/delete", methods=["DELETE"])
def delete_submission(file_id):
    """Admin xóa file đã submit"""
    db: Session = SessionLocal()
    try:
        submission = db.get(FileSubmission, file_id)
        if not submission:
            return jsonify({"detail": "Không tìm thấy file"}), 404

        # Xóa file từ disk
        filepath = os.path.join(UPLOADS_FOLDER, submission.filename)
        if os.path.exists(filepath):
            os.remove(filepath)

        # Xóa từ database
        db.delete(submission)
        db.commit()

        return jsonify({"message": "Xóa file thành công"})
    except Exception as e:
        db.rollback()
        return jsonify({"detail": f"Lỗi: {str(e)}"}), 500
    finally:
        db.close()


if __name__ == "__main__":
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    app.run(host=host, port=port, debug=True)
