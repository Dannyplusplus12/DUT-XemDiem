# Multi-Contest Analytics & Ranking System

> Phiên bản rework: backend FastAPI + SQLite/Pandas, công cụ nhập Excel dòng lệnh, frontend Flutter Web tiếng Việt.

## Cấu trúc

- `backend/`: FastAPI + SQLAlchemy + SQLite (có thể chuyển sang PostgreSQL qua biến `DATABASE_URL`).
- `backend/tools/import_excel.py`: tiện ích CLI xử lý Excel theo mẫu và nhập dữ liệu vào DB.
- `frontend/`: Flutter Web với các nhãn cố định "Cổng tra cứu kết quả thi", "Cá nhân", "Bảng xếp hạng", "Thứ hạng theo lớp", "Vị trí của tôi", "Trích xuất báo cáo", "Chia sẻ kết quả".

## 1. Backend

### Cài đặt & chạy local

Yêu cầu: Python 3.11+ (đã thêm vào PATH).

```bash
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Mặc định `DATABASE_URL=sqlite:///./contest.db`. Muốn dùng DB khác, chỉnh trong `.env` và khởi động lại.

### API chính

| Method | Endpoint | Mô tả |
| --- | --- | --- |
| GET | `/health` | Kiểm tra tình trạng service |
| POST | `/contests/upload` | Upload file Excel (multipart) cùng `mapping_json` |
| GET | `/contests` | Danh sách kỳ thi |
| GET | `/contests/{contest_id}/results/{student_id}` | Kết quả cá nhân |
| GET | `/contests/{contest_id}/leaderboard` | Bảng xếp hạng, hỗ trợ filter `class_name`, `page`, `page_size` |

### Công cụ nhập Excel

```bash
cd backend
python tools/import_excel.py data/ky-thi.xlsx \
  --mapping config/mapping.json \
  --contest-name "Kỳ thi tiếng Anh định kỳ"
```

- Nếu không truyền `--mapping`, script tự dùng cấu hình chuẩn: header dòng 8, cột `SBD`, `Họ và tên`, `Lớp`, `NGHE`, `ĐỌC`.
- File mapping (JSON) khớp schema `UploadContestMapping` trong `backend/app/schemas.py`.
- Sau khi chạy, script in `contest_id` để tra cứu trên giao diện.

## 2. Frontend (Flutter Web)

```bash
cd frontend
flutter pub get
flutter run -d chrome --dart-define=BACKEND_URL=http://localhost:8000
```

- Khi build: `flutter build web --release --dart-define=BACKEND_URL=https://backend-domain`.
- UI gồm 2 tab "Cá nhân" và "Bảng xếp hạng" đúng nhãn yêu cầu, có các nút "Vị trí của tôi", "Trích xuất báo cáo", "Chia sẻ kết quả".

## 3. Quy trình mẫu

1. Chuẩn bị Excel kỳ thi (header ở dòng 8 với các cột `SBD`, `Họ và tên`, `Lớp`, `NGHE`, `ĐỌC`).
2. Chạy `python tools/import_excel.py <file>.xlsx` để ghi dữ liệu.
3. Ghi lại `contest_id` trả về.
4. Mở Flutter Web (`flutter run ...`) và nhập `contest_id` + SBD/MSSV để tra cứu hoặc xem bảng xếp hạng.

## 4. Ghi chú deploy

- Backend: có thể dựng Docker hoặc deploy Railway bằng cách chạy `uvicorn app.main:app`. Bạn đồng nghiệp phụ trách deploy có thể dùng `DATABASE_URL` tùy môi trường.
- Frontend: sau khi `flutter build web`, upload thư mục `build/web` lên hosting tĩnh và trỏ về backend public.
