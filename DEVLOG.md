# 📓 DEVLOG - OCR Pipeline

Nhật ký phát triển dự án OCR Pipeline.

---

## [27-30/11/2025] Xây dựng Processors

### Hoàn thành
- ✅ Thiết kế cấu trúc thư mục `processors/`
- ✅ Triển khai `pdf_processor.py`:
  - Sử dụng PyPDF2 để trích xuất text
  - Phát hiện và bỏ qua PDF dạng scan (không có text layer)
  - Trả về content + metadata (file_name, file_size, page_count)
- ✅ Triển khai `docx_processor.py`:
  - Sử dụng python-docx để đọc nội dung
  - Trích xuất text từ tất cả paragraphs
  - Trả về content + metadata (file_name, file_size, paragraph_count)
- ✅ Triển khai `txt_processor.py`:
  - Tự động nhận diện encoding bằng chardet
  - Xử lý fallback khi encoding không chính xác
  - Trả về content + metadata (file_name, file_size)

---

## [01-05/12/2025] Xây dựng Core Modules

### 01/12 - Chunker
- ✅ Triển khai `chunker.py`:
  - Hỗ trợ 2 chế độ: chia theo câu (`sentence`) và đoạn (`paragraph`)
  - Giới hạn kích thước chunk tối đa (mặc định 500 ký tự)
  - Xử lý edge cases: text quá dài, text rỗng

### 02-03/12 - Database
- ✅ Triển khai `database.py`:
  - Định nghĩa SQLAlchemy models: `Document`, `Chunk`
  - Thiết lập relationship giữa Document và Chunk (cascade delete)
  - Hàm CRUD: `save_document`, `save_chunks`, `get_document`, `get_chunks`
  - Hàm tiện ích: `check_document_exists`, `get_unique_filename`
  - Hàm mở rộng: `delete_document`, `update_document`, `search_documents_by_name`, `get_all_documents`
  - Hỗ trợ pagination với `limit` và `offset`

### 04/12 - Main Pipeline
- ✅ Triển khai `main.py`:
  - Entry point cho xử lý batch từ thư mục
  - Ánh xạ đuôi file với processor tương ứng
  - Xử lý file trùng tên (tự động đổi tên)
  - Logging ra file `pipeline.log` và console
  - Hàm `process_file` và `process_directory`

### 05/12 - FastAPI Server
- ✅ Triển khai `app.py`:
  - REST API với FastAPI
  - Endpoint upload file (`POST /upload/`)
  - Endpoint lấy danh sách documents (`GET /documents/`)
  - Endpoint lấy chi tiết document (`GET /documents/{id}`)
  - Mount thư mục static cho giao diện web
  - Tự động xử lý file trong `input_docs/` khi khởi động server

---

## [08-10/12/2025] Documentation & Testing

### 08/12 - Unit Tests
- ✅ Tạo thư mục `tests/`
- ✅ Viết unit tests cho các processors
- ✅ Viết unit tests cho chunker
- ✅ Viết unit tests cho database functions

### 09/12 - Error Handling & Logging
- ✅ Kiểm tra và cải thiện error handling trong tất cả modules
- ✅ Đảm bảo logging hoạt động chính xác
- ✅ Test các edge cases và error scenarios

### 10/12 - Documentation & Final Polish
- ✅ Viết lại `README.md` hoàn chỉnh:
  - Mục lục, hướng dẫn cài đặt, cách sử dụng
  - API Endpoints, sơ đồ quy trình, schema database
- ✅ Sửa bug trong `docx_processor.py` (đang đọc như TXT)
- ✅ Cải thiện Test Coverage > 60%:
  - Thêm `tests/test_main.py` để test logic batch processing
  - Thêm `tests/conftest.py` để isolate môi trường test
  - Thêm unit tests với mock cho `pdf_processor` và `docx_processor`
- ✅ Sửa lỗi `NameError` và `ImportError` trong `test_database.py`
- ✅ Cập nhật giao diện Web:
  - Hiển thị thông báo chi tiết cho từng file (thành công/thất bại)
  - Không auto-process khi khởi động server
  - Chỉ cho phép upload file hỗ trợ (.pdf, .docx, .txt)
- ✅ Refine Features (Chunking & Storage):
  - Thêm tùy chọn `Chunking Mode` (Sentence/Paragraph)
  - Lưu chunks vào thư mục `chunks_data/`
  - Cải thiện Document List & Detail Viewer

## Ghi chú kỹ thuật

### Cấu trúc Database
```
documents (1) ──────< chunks (n)
     │                    │
     └── id ─────────── document_id (FK)
```

### Luồng xử lý chính
```
File → Processor → Raw Text → Chunker → Chunks → Database
```

### Dependencies chính
- **PyPDF2**: Xử lý PDF
- **python-docx**: Xử lý DOCX
- **chardet**: Nhận diện encoding
- **SQLAlchemy**: ORM cho PostgreSQL
- **FastAPI**: REST API framework

