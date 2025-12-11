# 📄 OCR Pipeline

Pipeline tự động đọc, xử lý và lưu trữ nội dung từ tài liệu (PDF, DOCX, TXT) vào cơ sở dữ liệu PostgreSQL.

---

## 📋 Mục lục

- [Giới thiệu](#intro)
- [Tính năng](#features)
- [Cấu trúc dự án](#structure)
- [Cài đặt](#install)
- [Cấu hình](#config)
- [Cách sử dụng](#usage)
- [API Endpoints](#api)
- [Quy trình hoạt động](#workflow)
- [Cấu trúc Database](#db)

---

## <a id="intro"></a>🎯 Giới thiệu

**OCR Pipeline** là một hệ thống xử lý tài liệu tự động được xây dựng bằng Python. Hệ thống có khả năng:
- Đọc và trích xuất nội dung từ nhiều định dạng file
- Chia nhỏ văn bản thành các đoạn (chunks) để dễ dàng xử lý
- Lưu trữ nội dung và metadata vào PostgreSQL
- Cung cấp API để upload và truy vấn tài liệu

---

## <a id="features"></a>✨ Tính năng

| Tính năng | Mô tả |
|-----------|-------|
| **Hỗ trợ đa định dạng** | PDF, DOCX, TXT |
| **Tự động nhận diện encoding** | Sử dụng `chardet` để nhận diện mã hóa file TXT |
| **Phát hiện PDF scan** | Tự động bỏ qua PDF dạng scan (không có text layer) |
| **Chunking thông minh** | Chia văn bản theo câu hoặc đoạn, tối đa 1000 ký tự/chunk |
| **Xử lý file trùng tên** | Tự động đổi tên nếu file đã tồn tại: `file.txt` → `file(1).txt` |
| **REST API** | Upload file và truy vấn dữ liệu qua FastAPI |
| **Ghi log đầy đủ** | Log ra file và console để theo dõi quá trình xử lý |

---

## <a id="structure"></a>📁 Cấu trúc dự án

```
OCR_Pipeline/
├── input_docs/         # Thư mục file đầu vào
├── chunks_data/        # Thư mục chứa các file chunks đã xử lý
├── src/                # Mã nguồn chính
│   ├── processors/     # Xử lý PDF, DOCX, TXT
│   ├── static/         # Giao diện web
│   ├── app.py          # FastAPI server
│   ├── chunker.py      # Chia nhỏ văn bản
│   ├── database.py     # Kết nối và CRUD database
│   └── main.py         # Entry point - xử lý batch
├── tests/              # Unit tests
├── README.md           # Tài liệu hướng dẫn
├── DEVLOG.md           # Nhật ký phát triển
└── requirements.txt    # Danh sách thư viện Python
```


## <a id="install"></a>🚀 Cài đặt

### 1. Clone repository

```bash
git clone <repository-url>
cd OCR_Pipeline
```

### 2. Tạo môi trường ảo (khuyến nghị)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 4. Cài đặt PostgreSQL

Tải và cài đặt PostgreSQL từ [https://www.postgresql.org/download/](https://www.postgresql.org/download/)

Tạo database mới:
```sql
CREATE DATABASE OCR;
```

---

## <a id="config"></a>⚙️ Cấu hình

### Biến môi trường

Tạo file `.env` trong thư mục gốc của dự án:

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/OCR
```

**Giải thích:**
- `postgres`: Tên người dùng PostgreSQL
- `your_password`: Mật khẩu của bạn
- `localhost:5432`: Địa chỉ và cổng PostgreSQL
- `OCR`: Tên database

> ⚠️ **Lưu ý**: Không commit file `.env` lên git. Thêm `.env` vào `.gitignore`.

---

## <a id="usage"></a>📖 Cách sử dụng

### Cách 1: Chạy Pipeline CLI (Xử lý batch)

Xử lý tất cả file trong thư mục mặc định (`input_docs/`):

```bash
cd src
python main.py
```

Xử lý thư mục tùy chỉnh:

```bash
cd src
python main.py "D:\Documents\MyFiles"
```

### Cách 2: Chạy Web Server (API)

Khởi động server:

```bash
cd src
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Truy cập:
- **Giao diện web**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Cách 3: Sử dụng như thư viện

```python
import sys
sys.path.append('src')  # Thêm thư mục src vào path

from main import process_file, process_directory
from database import init_database

# Khởi tạo database
init_database()

# Xử lý một file
process_file("path/to/document.pdf")

# Xử lý cả thư mục
process_directory("path/to/folder")
```

---

## <a id="api"></a>🔌 API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `GET` | `/` | Trang chủ (giao diện upload) |
| `POST` | `/upload/` | Upload và xử lý file |
| `GET` | `/documents/` | Lấy danh sách tất cả documents |
| `GET` | `/documents/{id}` | Lấy chi tiết document và chunks |

### Ví dụ sử dụng API

**Upload file:**
```bash
curl -X POST "http://localhost:8000/upload/" \
  -F "files=@document.pdf" \
  -F "files=@report.docx"
```

**Lấy danh sách documents:**
```bash
curl "http://localhost:8000/documents/"
```

---

## <a id="workflow"></a>🔄 Quy trình hoạt động

### Sơ đồ tổng quan

```mermaid
flowchart TD
    subgraph Inputs [📂 Input Sources]
        A1[📄 PDF Files]
        A2[📝 DOCX Files]
        A3[📃 TXT Files]
    end

    subgraph Processing [⚙️ Processing Layer]
        B1[⚡ PDF Processor]
        B2[⚡ DOCX Processor]
        B3[⚡ TXT Processor]
        
        A1 -->|PyPDF2| B1
        A2 -->|python-docx| B2
        A3 -->|chardet| B3
        
        B1 -.->|Skip Scanned| X[🚫 Ignore]
    end

    C[📄 Raw Text + Metadata]

    subgraph Chunking [✂️ Chunking Layer]
        D{Chunking Mode?}
        D -->|Sentence| E1[Sentence Splitter]
        D -->|Paragraph| E2[Paragraph Splitter]
        
        E1 --> F[🧩 Chunks]
        E2 --> F
    end

    subgraph Storage [💾 Storage Layer]
        G[(🐘 PostgreSQL)]
        H[📂 File System]
        
        F -->|Save Metadata| G
        F -->|Save Content| H
    end

    B1 --> C
    B2 --> C
    B3 --> C
    C --> D
```

### Chi tiết từng bước

#### Bước 1: Đọc file đầu vào
- **Vị trí**: Thư mục `input_docs/` hoặc upload qua API
- **Định dạng hỗ trợ**: PDF, DOCX, TXT
- **Hành động**: `main.py` quét thư mục và phân loại file theo đuôi mở rộng

#### Bước 2: Processor trích xuất text
Mỗi loại file có processor riêng:

| Loại file | Processor | Thư viện | Ghi chú |
|-----------|-----------|----------|---------|
| `.pdf` | `pdf_processor.py` | PyPDF2 | Bỏ qua PDF scan (không có text) |
| `.docx` | `docx_processor.py` | python-docx | Trích xuất từ paragraphs |
| `.txt` | `txt_processor.py` | chardet | Tự động nhận diện encoding |

**Output**: Văn bản thô + metadata (tên file, kích thước, số trang...)

#### Bước 3: Chunker chia nhỏ văn bản
- **File**: `chunker.py`
- **Chế độ**: Chia theo câu (`sentence`) hoặc đoạn (`paragraph`)
- **Kích thước**: Tối đa 1000 ký tự/chunk
- **Thuật toán**:
  1. Tách văn bản thành các câu/đoạn
  2. Ghép nhiều câu/đoạn vào 1 chunk (nếu chưa vượt max_size)
  3. Nếu 1 câu quá dài → chia nhỏ thêm

**Output**: Danh sách các chunks

#### Bước 4: Lưu vào Database
- **File**: `database.py`
- **Bảng `documents`**: Lưu metadata (tên file, đường dẫn, loại file, ngày upload)
- **Bảng `chunks`**: Lưu nội dung từng chunk, liên kết với document qua `document_id`

```
documents (1) ──────< chunks (n)
     │                    │
     └── id ─────────── document_id (FK)
```

---

## <a id="db"></a>🗄️ Cấu trúc Database

### Bảng `documents`

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `id` | INTEGER | Khóa chính, tự động tăng |
| `file_name` | VARCHAR | Tên file (đã xử lý trùng) |
| `file_path` | VARCHAR | Đường dẫn đầy đủ |
| `file_type` | VARCHAR | Loại file (.pdf, .docx, .txt) |
| `file_size` | INTEGER | Kích thước file (bytes) |
| `upload_date` | DATETIME | Ngày upload |
| `chunk_count` | INTEGER | Số lượng chunks |

### Bảng `chunks`

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `id` | INTEGER | Khóa chính, tự động tăng |
| `document_id` | INTEGER | Khóa ngoại liên kết với documents |
| `chunk_index` | INTEGER | Thứ tự chunk trong document |
| `content` | TEXT | Nội dung chunk |
| `char_count` | INTEGER | Số ký tự trong chunk |

---

## 🧪 Chạy Tests

```bash
# Chạy tests đơn giản
pytest tests/ -v

# Để xác định độ phủ code (coverage)
pytest tests/ --cov=src --cov-report=term-missing
```