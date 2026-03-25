# Multi-Contest Analytics & Ranking System

## Cấu trúc dự án

- `backend/`: FastAPI + Pandas + SQLAlchemy + PostgreSQL.
- `frontend/`: Flutter Web giao diện tra cứu tiếng Việt.
- `scripts/deploy_flutter_railway.sh`: Script deploy Flutter Web lên Railway.

## 1) Backend

### Chạy local

```bash
cd backend
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API chính

- `POST /upload-contest`
- `GET /contests`
- `GET /results/{contest_id}/{student_id}`
- `GET /leaderboard/{contest_id}`
- `GET /suggest-classes/{contest_id}`
- `POST /contests/{contest_id}/feedback`
- `GET /contests/{contest_id}/feedback`

## 2) Frontend (Flutter Web)

```bash
cd frontend
flutter pub get
flutter run -d chrome
```

## 3) Docker

- Backend: `backend/Dockerfile`
- Frontend: `frontend/Dockerfile`

## 4) Deploy Railway

- Backend: dùng `backend/railway.toml`
- Frontend: chạy script `scripts/deploy_flutter_railway.sh`

## 5) Tạo repo GitHub

Tôi không thể tạo repo trực tiếp trên tài khoản GitHub của bạn, nhưng bạn có thể chạy:

```bash
git init
git add .
git commit -m "Initial commit: multi-contest analytics platform"
gh repo create multi-contest-analytics --private --source=. --remote=origin --push
```

Nếu muốn tách riêng backend để deploy Railway, tạo repo thứ hai ngay trong thư mục `backend/`:

```bash
cd backend
git init
git add .
git commit -m "Initial backend for Railway"
gh repo create multi-contest-backend --private --source=. --remote=origin --push
```
