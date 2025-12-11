import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Lấy URL kết nối từ biến môi trường, mặc định là localhost nếu không có
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:123456@localhost:5432/OCR")

Base = declarative_base()

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    upload_date = Column(DateTime, default=datetime.utcnow)
    chunk_count = Column(Integer, default=0)
    
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

class Chunk(Base):
    __tablename__ = 'chunks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    char_count = Column(Integer, nullable=False)
    
    document = relationship("Document", back_populates="chunks")

# Engine và session factory toàn cục
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """Tạo database và các bảng nếu chưa tồn tại."""
    Base.metadata.create_all(bind=engine)
    print("Khởi tạo database thành công.")

def get_db_session():
    """Helper để lấy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_document(file_info: dict):
    """
    Lưu thông tin metadata của document.
    file_info: dict chứa các keys: file_name, file_path, file_type, file_size, chunk_count
    Trả về: id của document vừa tạo
    """
    session = SessionLocal()
    try:
        new_doc = Document(
            file_name=file_info['file_name'],
            file_path=file_info['file_path'],
            file_type=file_info['file_type'],
            file_size=file_info.get('file_size'),
            chunk_count=file_info.get('chunk_count', 0),
            upload_date=datetime.utcnow()
        )
        session.add(new_doc)
        session.commit()
        session.refresh(new_doc)
        return new_doc.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def save_chunks(document_id: int, chunks_data: list):
    """
    Lưu danh sách các chunks của document đó.
    chunks_data: list các dict, mỗi dict chứa: chunk_index, content, char_count
    """
    session = SessionLocal()
    try:
        chunks_objects = []
        for chunk in chunks_data:
            new_chunk = Chunk(
                document_id=document_id,
                chunk_index=chunk['chunk_index'],
                content=chunk['content'],
                char_count=chunk.get('char_count', len(chunk['content']))
            )
            chunks_objects.append(new_chunk)
        
        session.add_all(chunks_objects)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_document(document_id: int):
    """Truy vấn thông tin document theo ID."""
    session = SessionLocal()
    try:
        return session.query(Document).filter(Document.id == document_id).first()
    finally:
        session.close()

def get_chunks(document_id: int):
    """Truy vấn danh sách chunks của document theo ID."""
    session = SessionLocal()
    try:
        return session.query(Chunk).filter(Chunk.document_id == document_id).order_by(Chunk.chunk_index).all()
    finally:
        session.close()

def check_document_exists(file_name: str) -> bool:
    """Kiểm tra xem document với tên file này đã tồn tại chưa."""
    session = SessionLocal()
    try:
        exists = session.query(Document.id).filter(Document.file_name == file_name).first() is not None
        return exists
    finally:
        session.close()

def get_unique_filename(file_name: str) -> str:
    """
    Tạo tên file duy nhất bằng cách thêm (n) nếu trùng.
    Ví dụ: file.txt -> file(1).txt
    """
    session = SessionLocal()
    try:
        # Nếu chưa tồn tại thì trả về nguyên bản
        if session.query(Document.id).filter(Document.file_name == file_name).first() is None:
            return file_name
        
        name, ext = os.path.splitext(file_name)
        counter = 1
        while True:
            new_name = f"{name}({counter}){ext}"
            if session.query(Document.id).filter(Document.file_name == new_name).first() is None:
                return new_name
            counter += 1
    finally:
        session.close()

def delete_document(document_id: int) -> bool:
    """
    Xóa document theo ID (cascade xóa luôn tất cả chunks liên quan).
    Trả về: True nếu xóa thành công, False nếu không tìm thấy document.
    """
    session = SessionLocal()
    try:
        document = session.query(Document).filter(Document.id == document_id).first()
        if document is None:
            return False
        
        session.delete(document)  # Cascade sẽ tự động xóa các chunks
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def update_document(document_id: int, update_data: dict) -> bool:
    """
    Cập nhật thông tin document theo ID.
    update_data: dict chứa các fields cần cập nhật (file_name, file_path, file_type, file_size, chunk_count)
    Trả về: True nếu cập nhật thành công, False nếu không tìm thấy document.
    """
    session = SessionLocal()
    try:
        document = session.query(Document).filter(Document.id == document_id).first()
        if document is None:
            return False
        
        # Chỉ cập nhật các trường được phép
        allowed_fields = ['file_name', 'file_path', 'file_type', 'file_size', 'chunk_count']
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(document, field):
                setattr(document, field, value)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def search_documents_by_name(search_term: str, limit: int = 50) -> list:
    """
    Tìm kiếm documents theo tên file (tìm kiếm không phân biệt hoa thường, tìm kiếm một phần).
    search_term: chuỗi tìm kiếm
    limit: số lượng kết quả tối đa (mặc định 50)
    Trả về: danh sách các document phù hợp
    """
    session = SessionLocal()
    try:
        # Dùng ILIKE để tìm kiếm không phân biệt chữ hoa/thường
        documents = session.query(Document).filter(
            Document.file_name.ilike(f"%{search_term}%")
        ).order_by(Document.upload_date.desc()).limit(limit).all()
        
        # Chuyển đổi sang dict để tránh lỗi detached session
        results = []
        for doc in documents:
            results.append({
                'id': doc.id,
                'file_name': doc.file_name,
                'file_path': doc.file_path,
                'file_type': doc.file_type,
                'file_size': doc.file_size,
                'upload_date': doc.upload_date,
                'chunk_count': doc.chunk_count
            })
        return results
    finally:
        session.close()

def get_all_documents(limit: int = 100, offset: int = 0) -> list:
    """
    Lấy danh sách tất cả documents với phân trang.
    limit: số lượng kết quả tối đa
    offset: vị trí bắt đầu
    Trả về: danh sách các document
    """
    session = SessionLocal()
    try:
        documents = session.query(Document).order_by(
            Document.upload_date.desc()
        ).offset(offset).limit(limit).all()
        
        results = []
        for doc in documents:
            results.append({
                'id': doc.id,
                'file_name': doc.file_name,
                'file_path': doc.file_path,
                'file_type': doc.file_type,
                'file_size': doc.file_size,
                'upload_date': doc.upload_date,
                'chunk_count': doc.chunk_count
            })
        return results
    finally:
        session.close()

if __name__ == "__main__":
    init_database()
