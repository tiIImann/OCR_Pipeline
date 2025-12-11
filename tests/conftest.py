import pytest
import sys
import os
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Thêm thư mục src vào đường dẫn
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# QUAN TRỌNG: Cấu hình biến môi trường DATABASE_URL thành SQLite in-memory 
# TRƯỚC KHI import bất kỳ module nào từ src (database, app, main).
# Điều này đảm bảo code không bao giờ kết nối đến database thật (Postgres) trong quá trình test.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from database import Base, get_db_session
from app import app

# Sử dụng SQLite in-memory cho việc kiểm thử
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def test_db():
    # Tạo các bảng
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Xóa các bảng sau khi test xong
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db, tmp_path):
    # Ghi đè dependency get_db_session
    def override_get_db_session():
        try:
            yield test_db
        finally:
            pass # Session được đóng trong fixture test_db
            
    app.dependency_overrides[get_db_session] = override_get_db_session
    
    # Ghi đè UPLOAD_DIR
    # Chúng ta cần patch UPLOAD_DIR trong module app. 
    # Vì nó là biến toàn cục, ta dùng unittest.mock để patch.
    from unittest.mock import patch, MagicMock
    
    # Tạo thư mục tạm để upload
    temp_upload_dir = tmp_path / "input_docs_test"
    temp_upload_dir.mkdir()
    
    # Mock session.close để tránh lỗi DetachedInstanceError khi code gọi close()
    original_close = test_db.close
    test_db.close = MagicMock()

    # Patch SessionLocal trong database.py để trả về test_db
    # Patch UPLOAD_DIR trong app
    with patch("app.UPLOAD_DIR", str(temp_upload_dir)), \
         patch("database.SessionLocal", return_value=test_db):
        
        with TestClient(app) as c:
            yield c
    
    # Khôi phục close
    test_db.close = original_close
            
    # Xóa dependency override (thực hành tốt)
    app.dependency_overrides.clear()
