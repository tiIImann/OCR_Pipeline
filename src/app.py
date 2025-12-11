import os
import shutil
import threading
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from database import get_db_session, Document, Chunk, get_unique_filename
from main import process_file, process_directory

app = FastAPI(title="OCR Pipeline App")

# Lấy đường dẫn tuyệt đối của thư mục chứa file này
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
PROJECT_DIR = os.path.dirname(BASE_DIR)  # Thư mục gốc dự án
UPLOAD_DIR = os.path.join(PROJECT_DIR, "input_docs")
CHUNKS_DIR = os.path.join(PROJECT_DIR, "chunks_data")

# Mount thư mục static cho giao diện
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Tạo thư mục input và chunks nếu chưa tồn tại
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

if not os.path.exists(CHUNKS_DIR):
    os.makedirs(CHUNKS_DIR)

# Các định dạng file được hỗ trợ
SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.txt'}

@app.get("/", response_class=HTMLResponse)
async def read_root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>OCR Pipeline API</h1><p>Static files not found.</p>"

@app.post("/upload/")
async def upload_files(
    files: List[UploadFile] = File(...),
    chunk_mode: str = Form("sentence")
):
    results = []
    for file in files:
        try:
            # Kiểm tra định dạng file
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                results.append({
                    "filename": file.filename, 
                    "status": "error", 
                    "message": f"File không được hỗ trợ. Chỉ chấp nhận: {', '.join(SUPPORTED_EXTENSIONS)}"
                })
                continue
            
            # Thêm suffix mode vào tên file (ví dụ: file_sentence.txt hoặc file_paragraph.txt)
            name_only, extension = os.path.splitext(file.filename)
            new_filename = f"{name_only}_{chunk_mode}{extension}"
            
            # Lấy tên file duy nhất để tránh trùng lặp
            unique_filename = get_unique_filename(new_filename)
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            
            # Lưu file vào máy
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Xử lý file với chunk_mode được chọn
            result = process_file(file_path, chunk_mode=chunk_mode)
            if result:
                results.append({"filename": file.filename, "status": "success", "message": "Đã xử lý và lưu vào database"})
            else:
                results.append({"filename": file.filename, "status": "error", "message": "Không thể xử lý file"})
        except Exception as e:
            results.append({"filename": file.filename, "status": "error", "message": str(e)})
            
    return {"results": results}

@app.get("/documents/")
def get_documents(db: Session = Depends(get_db_session)):
    docs = db.query(Document).order_by(Document.upload_date.desc()).all()
    return docs

@app.get("/documents/{document_id}")
def get_document_detail(document_id: int, db: Session = Depends(get_db_session)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    chunks = db.query(Chunk).filter(Chunk.document_id == document_id).order_by(Chunk.chunk_index).all()
    return {"document": doc, "chunks": chunks}

@app.put("/documents/{document_id}")
def update_document(document_id: int, new_name: str, db: Session = Depends(get_db_session)):
    """Cập nhật tên document"""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc.file_name = new_name
    db.commit()
    db.refresh(doc)
    return {"message": "Document updated", "document": doc}

@app.delete("/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db_session)):
    """Xóa document và tất cả chunks liên quan"""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Xóa tất cả chunks trước
    db.query(Chunk).filter(Chunk.document_id == document_id).delete()
    # Xóa document
    db.delete(doc)
    db.commit()
    return {"message": f"Document {document_id} and its chunks deleted"}

