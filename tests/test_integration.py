import sys
import os
import pytest
# Thêm thư mục src vào path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from database import init_database, save_document, save_chunks, get_document, get_chunks, Document, Chunk
from chunker import chunk_text

from unittest.mock import patch

# Sử dụng fixture test_db từ conftest.py một cách ngầm định bằng cách truyền nó vào test
# Nhưng chúng ta cần patch SessionLocal cho các hàm được import từ database.py

@pytest.fixture
def setup_integration(test_db):
    # Patch SessionLocal để trả về test_db của chúng ta
    # Điều này bao phủ save_document, save_chunks, get_document, v.v.
    with patch('database.SessionLocal') as mock_session_cls:
        mock_session_cls.return_value = test_db
        yield test_db

def test_full_flow(setup_integration):
    db_session = setup_integration
    """
    Quy trình kiểm tra:
    1. Chuẩn bị dữ liệu (mô phỏng đọc file)
    2. Chia nhỏ (Chunking)
    3. Lưu Document
    4. Lưu Chunks
    5. Xác minh dữ liệu trong DB
    """
    
    # 1. Chuẩn bị
    filename = "integration_test.txt"
    content = "Integration test content. Chunk 1. Chunk 2."
    file_path = f"/tmp/{filename}"
    
    # 2. Chia nhỏ
    chunks_text = chunk_text(content, max_size=20)
    assert len(chunks_text) > 1
    
    # 3. Lưu Document
    doc_info = {
        'file_name': filename,
        'file_path': file_path,
        'file_type': '.txt',
        'file_size': len(content),
        'chunk_count': len(chunks_text)
    }
    
    # Xóa lần chạy trước nếu có
    existing = db_session.query(Document).filter_by(file_name=filename).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()

    doc_id = save_document(doc_info)
    assert doc_id is not None
    
    # 4. Lưu Chunks
    chunks_data = []
    for i, c_content in enumerate(chunks_text):
        chunks_data.append({
            'chunk_index': i,
            'content': c_content,
            'char_count': len(c_content)
        })
        
    save_chunks(doc_id, chunks_data)
    
    # 5. Xác minh
    saved_doc = get_document(doc_id)
    assert saved_doc.file_name == filename
    assert saved_doc.chunk_count == len(chunks_text)
    
    saved_chunks = get_chunks(doc_id)
    assert len(saved_chunks) == len(chunks_text)
    assert saved_chunks[0].content == chunks_text[0]

if __name__ == "__main__":
    pytest.main([__file__])
