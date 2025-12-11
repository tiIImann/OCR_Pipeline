import sys
import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Thêm thư mục src vào path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from database import (
    Base, Document, Chunk, get_unique_filename, check_document_exists, init_database,
    delete_document, update_document, search_documents_by_name, get_all_documents,
    get_document, get_chunks
)

# Sử dụng database kiểm thử riêng biệt hoặc cùng một database?
# Để đơn giản trong ngữ cảnh này, chúng ta sẽ sử dụng cái hiện có nhưng lý tưởng nhất là nên dùng DB kiểm thử.
# Chúng ta sẽ sử dụng mock hoặc thiết lập tạm thời nếu có thể, nhưng ở đây chúng ta kiểm thử logic thực tế.

from unittest.mock import patch, MagicMock

# Sử dụng fixture test_db từ conftest.py
@pytest.fixture
def db_session(test_db):
    # Patch SessionLocal trong database.py để trả về session test_db của chúng ta
    # Chúng ta cần patch nó ở nơi nó được sử dụng (bên trong các hàm của database.py)
    # Vì chúng ta import các hàm từ database, hãy patch 'database.SessionLocal'
    
    # Ngăn code ứng dụng đóng session (gây lỗi DetachedInstanceError)
    original_close = test_db.close
    test_db.close = MagicMock()
    
    with patch('database.SessionLocal') as mock_session_cls:
        # SessionLocal() trả về instance của session
        mock_session_cls.return_value = test_db
        yield test_db
    
    # Khôi phục hàm close để conftest có thể dọn dẹp đúng cách
    test_db.close = original_close

def test_connection(db_session):
    """Kiểm tra kết nối cơ sở dữ liệu"""
    result = db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1

def test_get_unique_filename(db_session):
    """Kiểm tra logic tự động đổi tên"""
    # Dọn dẹp các file có thể đang tồn tại
    base_name = "pytest_renaming.txt"
    existing = db_session.query(Document).filter(Document.file_name.like(f"pytest_renaming%")).all()
    for doc in existing:
        db_session.delete(doc)
    db_session.commit()

    # 1. File đầu tiên
    name1 = get_unique_filename(base_name)
    assert name1 == base_name
    
    # Tạo doc giả lập
    doc1 = Document(file_name=name1, file_path="path", file_type=".txt")
    db_session.add(doc1)
    db_session.commit()

    # 2. File thứ hai (trùng lặp)
    name2 = get_unique_filename(base_name)
    assert name2 == "pytest_renaming(1).txt"
    
    doc2 = Document(file_name=name2, file_path="path", file_type=".txt")
    db_session.add(doc2)
    db_session.commit()

    # 3. File thứ ba
    name3 = get_unique_filename(base_name)
    assert name3 == "pytest_renaming(2).txt"

def test_check_document_exists(db_session):
    """Kiểm tra sự tồn tại của tài liệu"""
    filename = "pytest_exists.txt"
    
    # Đảm bảo trạng thái sạch sẽ
    existing = db_session.query(Document).filter_by(file_name=filename).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()
    
    assert check_document_exists(filename) is False
    
    # Thêm doc
    doc = Document(file_name=filename, file_path="path", file_type=".txt")
    db_session.add(doc)
    db_session.commit()
    
    
    
    assert check_document_exists(filename) is True

def test_delete_document(db_session):
    """Kiểm tra chức năng xóa document"""
    filename = "pytest_delete.txt"
    doc = Document(file_name=filename, file_path="path", file_type=".txt")
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    doc_id = doc.id
    
    # Tạo chunk giả
    chunk = Chunk(document_id=doc_id, chunk_index=0, content="abc", char_count=3)
    db_session.add(chunk)
    db_session.commit()
    
    # Xóa thành công
    assert delete_document(doc_id) is True
    assert db_session.query(Document).filter_by(id=doc_id).first() is None
    assert db_session.query(Chunk).filter_by(document_id=doc_id).first() is None
    
    # Xóa fail (không tồn tại)
    assert delete_document(999999) is False

def test_update_document(db_session):
    """Kiểm tra chức năng cập nhật document"""
    filename = "pytest_update.txt"
    doc = Document(file_name=filename, file_path="path", file_type=".txt")
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    
    # Update thành công
    new_data = {'file_name': "pytest_updated.txt", 'file_size': 100}
    assert update_document(doc.id, new_data) is True
    
    updated_doc = db_session.query(Document).filter_by(id=doc.id).first()
    assert updated_doc.file_name == "pytest_updated.txt"
    assert updated_doc.file_size == 100
    
    # Update fail
    assert update_document(999999, new_data) is False

def test_search_documents(db_session):
    """Kiểm tra tìm kiếm document"""
    # Tạo dữ liệu mẫu
    doc1 = Document(file_name="invoice_2023.pdf", file_path="p1", file_type=".pdf")
    doc2 = Document(file_name="report_2023.docx", file_path="p2", file_type=".docx")
    doc3 = Document(file_name="notes.txt", file_path="p3", file_type=".txt")
    db_session.add_all([doc1, doc2, doc3])
    db_session.commit()
    
    # Tìm kiếm
    results = search_documents_by_name("2023")
    assert len(results) >= 2
    filenames = [r['file_name'] for r in results]
    assert "invoice_2023.pdf" in filenames
    assert "report_2023.docx" in filenames

def test_get_all_documents(db_session):
    """Kiểm tra lấy tất cả document"""
    # Count current
    initial_count = len(get_all_documents())
    
    # Add new
    doc = Document(file_name="new_doc.txt", file_path="p", file_type=".txt")
    db_session.add(doc)
    db_session.commit()
    
    new_count = len(get_all_documents())
    assert new_count == initial_count + 1

def test_get_document_and_chunks(db_session):
    """Kiểm tra lấy chi tiết document và chunks"""
    doc = Document(file_name="detail_test.txt", file_path="p", file_type=".txt")
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    
    # Add chunks
    c1 = Chunk(document_id=doc.id, chunk_index=0, content="c1", char_count=2)
    c2 = Chunk(document_id=doc.id, chunk_index=1, content="c2", char_count=2)
    db_session.add_all([c1, c2])
    db_session.commit()
    
    # Get document
    fetched_doc = get_document(doc.id)
    assert fetched_doc.file_name == "detail_test.txt"
    
    # Get chunks
    chunks = get_chunks(doc.id)
    assert len(chunks) == 2
    assert chunks[0].content == "c1"

if __name__ == "__main__":
    pytest.main([__file__])
