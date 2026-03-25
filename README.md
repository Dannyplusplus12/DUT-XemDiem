# DUT Exam Results Portal (Cổng Tra Cứu Kết Quả Thi)

> **Vietnamese Exam Results Lookup System** - Flask backend + HTML/CSS/JavaScript frontend with UTF-8 support

## 🎯 Overview

DUT Exam Results Portal là một hệ thống tra cứu kết quả thi dành cho sinh viên Đại học Duy Tân. Giao diện hoàn toàn tiếng Việt, hỗ trợ xem bảng xếp hạng, tra cứu điểm cá nhân, và quản lý kết quả thi.

**Tính năng chính:**
- 📊 **Bảng xếp hạng** - Xem top sinh viên theo kỳ thi, có thể lọc theo lớp
- 🔍 **Tra cứu cá nhân** - Tìm kết quả, xếp hạng, phần trăm, chi tiết từng thành phần
- 📁 **Đóng góp kỳ thi** - Upload file Excel để thêm kết quả mới
- 🎨 **Giao diện responsive** - Hoạt động tốt trên điện thoại, máy tính bảng, desktop

## 🏗️ Tech Stack

- **Backend:** Flask 3.0.0 + SQLAlchemy 2.0.36 + SQLite
- **Frontend:** HTML5 + CSS3 + Vanilla JavaScript (No frameworks)
- **Data Processing:** Pandas 3.0.1 + OpenPyXL 3.1.5
- **Configuration:** Python-dotenv 1.0.1 + Pydantic 1.10.17

## ⚡ Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/Dannyplusplus12/DUT-XemDiem.git
cd DUT-XemDiem
```

### 2. Setup Backend
```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
copy .env.example .env
```

File `.env` mặc định:
```
DATABASE_URL=sqlite:///./backend/contest.db
APP_HOST=0.0.0.0
APP_PORT=8000
```

### 4. Run Backend
```bash
cd backend
python run.py
```

Server sẽ chạy tại `http://localhost:8000`

### 5. Access Frontend
- Mở trình duyệt: `http://localhost:8000`
- Giao diện hiện thị ngay lập tức (không cần build)

## 📚 Project Structure

```
DUT-XemDiem/
├── backend/
│   ├── app/
│   │   ├── __init__.py           # Flask app initialization
│   │   ├── main.py               # API routes (11 endpoints)
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── services.py           # Excel import + ranking calculations
│   │   ├── database.py           # SQLite configuration with UTF-8
│   │   └── schemas.py            # Pydantic validation schemas
│   ├── static/
│   │   └── index.html            # Single-page application
│   ├── uploads/                  # User-submitted files (auto-created)
│   ├── tools/
│   │   ├── import_excel.py       # CLI tool for Excel import
│   │   └── TADK-1.xlsx           # Sample data
│   ├── config/
│   │   └── sample_mapping.json   # Excel column mapping
│   ├── contest.db                # SQLite database (auto-created)
│   ├── requirements.txt          # Python dependencies
│   ├── run.py                    # Flask entry point
│   └── .env / .env.example       # Environment config
├── .gitignore                    # Git ignore patterns
└── README.md                     # This file
```

## 🔌 API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `GET` | `/health` | Kiểm tra tình trạng service |
| `GET` | `/contests` | Danh sách tất cả kỳ thi |
| `GET` | `/contests/{contest_id}/leaderboard` | Bảng xếp hạng (filter class, pagination) |
| `GET` | `/contests/{contest_id}/results/{student_id}` | Kết quả cá nhân chi tiết |
| `GET` | `/contests/{contest_id}/classes` | Danh sách lớp trong kỳ thi |
| `POST` | `/files/submit` | Upload file Excel |
| `GET` | `/files/list` | Danh sách file đã upload |
| `POST` | `/files/{id}/import` | Import file vào database |
| `DELETE` | `/files/{id}/delete` | Xóa file đã upload |
| `GET` | `/contests/{contest_id}` | Chi tiết kỳ thi |
| `DELETE` | `/contests/{contest_id}` | Xóa kỳ thi |

### Ví dụ API calls:

**Lấy danh sách kỳ thi:**
```bash
curl http://localhost:8000/contests
```

**Lấy bảng xếp hạng:**
```bash
curl "http://localhost:8000/contests/{contest_id}/leaderboard?page_size=10000"
```

**Lọc theo lớp:**
```bash
curl "http://localhost:8000/contests/{contest_id}/leaderboard?page_size=10000&class_name=23D1"
```

**Tra cứu điểm cá nhân:**
```bash
curl "http://localhost:8000/contests/{contest_id}/results/{student_id}"
```

## 📝 Nhập Dữ Liệu Từ Excel

### 1. Chuẩn bị file Excel

File Excel phải có cấu trúc:
- **Header ở dòng 8**
- **Cột bắt buộc:** `Thẻ SV`, `Họ và tên`, `Lớp`
- **Cột điểm:** `NGHE`, `ĐỌC`, v.v.

### 2. Upload via Frontend

1. Mở `http://localhost:8000`
2. Chọn tab **"Đóng góp kỳ thi"**
3. Điền thông tin và chọn file Excel
4. Nhấn **"Đăng ký"**

### 3. Import via Admin

Sang tab **Admin** (Ctrl+Shift+K):
- Click **"Import"** trên file
- Hệ thống sẽ xử lý và lưu vào database

### 4. CLI Import (tùy chọn)

```bash
cd backend
python tools/import_excel.py tools/TADK-1.xlsx --contest-name "Tên kỳ thi"
```

## 🎨 Frontend Features

### Tab: Kỳ Thi
- Hiển thị grid card của tất cả kỳ thi
- Click vào card để xem bảng xếp hạng

### Tab: Bảng Xếp Hạng
- **Lọc theo lớp:** Dropdown, chọn lớp để filter
- **Tìm kiếm:** Input mã sinh viên, tìm + highlight
- **Click hàng:** Mở modal chi tiết
- **Bảng dữ liệu:** Thứ hạng, Tên, Lớp, Tổng điểm, Phần trăm

### Tab: Tra Cứu Cá Nhân
- Input mã sinh viên → Enter
- Hiển thị: Tên, mã SV, lớp, tổng điểm, xếp hạng, chi tiết từng thành phần

### Tab: Đóng Góp Kỳ Thi
- Form upload file Excel
- Quản lý file (Admin)

## ⚙️ Configuration

### Environment Variables (`.env`)

```ini
DATABASE_URL=sqlite:///./backend/contest.db
APP_HOST=0.0.0.0
APP_PORT=8000
```

## 🚀 Production Deployment

### Local Server
```bash
cd backend
python run.py
```

### Gunicorn
```bash
pip install gunicorn
cd backend
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Docker
```bash
docker build -t dut-exam-portal .
docker run -p 8000:8000 dut-exam-portal
```

## 🛠️ Development

### Setup
```bash
cd backend
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Check Database
```bash
sqlite3 backend/contest.db "SELECT * FROM contests;"
```

## 📋 Troubleshooting

### UTF-8 encoding error
Flask backend xử lý tất cả encoding. Đảm bảo file `.env` có UTF-8 encoding.

### Database file not found
Chạy `python run.py` lần đầu sẽ tự động tạo database.

### Port 8000 is already in use
Thay đổi `APP_PORT` trong `.env` hoặc kill process:
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### File upload fails
Kiểm tra quyền ghi thư mục `backend/uploads/`. Thư mục sẽ tự động tạo.

## 📄 License

MIT License

## 📞 Support

Liên hệ hoặc tạo Issue trên GitHub: https://github.com/Dannyplusplus12/DUT-XemDiem/issues

---

**Version:** 1.0.0  
**Last Updated:** 2024  
**Tech:** Flask + SQLite + HTML/CSS/JavaScript
