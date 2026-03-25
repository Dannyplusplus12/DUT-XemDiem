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

## 6) Quy trình nhập 1 kỳ thi từ Excel (mẫu tiếng Anh định kỳ)

1. Sao chép file Excel gốc vào `backend/excels/`. Mẫu hiện tại có tiêu đề bảng ở dòng 8 (`TT, SBD, Thẻ SV, Họ và tên, Lớp, NGHE, ĐỌC, TỔNG ĐIỂM, GHI CHÚ`).
2. Cập nhật hoặc nhân bản `backend/scripts/sample_mapping.json` nếu cần đổi tên cột. Các trường đã khớp với cấu trúc trong ảnh (header ở dòng 8, dùng cột `NGHE` và `ĐỌC`).
3. Chạy tiện ích chuẩn hóa để kiểm tra nhanh dữ liệu:
   ```bash
   cd backend
   python -m venv .venv
   . .venv/Scripts/Activate.ps1
   pip install -r requirements.txt
   python scripts/process_excel.py excels/ky-thi.xlsx scripts/sample_mapping.json excels/normalized.json
   ```
   File `excels/normalized.json` giúp đối chiếu thứ hạng/điểm trước khi đẩy lên server.
4. Upload trực tiếp Excel lên backend đang chạy Railway (thay đường dẫn file cục bộ):
   ```bash
   curl -X POST "https://contestanalys-production.up.railway.app/upload-contest" ^
     -H "accept: application/json" ^
     -H "Content-Type: multipart/form-data" ^
     -F "file=@D:/Dev/APP/DUT/backend/excels/ky-thi.xlsx" ^
     -F "mapping_json=$(Get-Content scripts/sample_mapping.json -Raw)"
   ```
   Kết quả trả về `contest_id` → dùng cho giao diện tra cứu.
5. Kiểm tra giao diện:
   - Cá nhân: nhập `contest_id` + `SBD`.
   - Bảng xếp hạng: nhập `contest_id`, chọn lớp nếu cần, dùng nút `Vị trí của tôi` để tô đậm thí sinh.
