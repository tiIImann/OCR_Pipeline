import sys
import os
import pytest
# Thêm thư mục src vào path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# from app import app # app được sử dụng trong conftest, không cần ở đây trực tiếp
# client = TestClient(app) # Đã xóa, sử dụng fixture

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "OCR Pipeline Dashboard" in response.text

def test_get_documents_empty(client):
    # Giả sử DB trống cho test db mới
    response = client.get("/documents/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 0

def test_upload_file(client, tmp_path):
    # Tạo file giả lập
    d = tmp_path / "subdir"
    d.mkdir()
    p = d / "api_test.txt"
    p.write_text("API Test Content", encoding="utf-8")
    
    with open(p, "rb") as f:
        response = client.post(
            "/upload/",
            files={"files": ("api_test.txt", f, "text/plain")},
            data={"chunk_mode": "sentence"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    # Filename phải có suffix _sentence
    assert data["results"][0]["filename"] == "api_test.txt" # Tên gốc trả về trong result thường là tên gốc upload
    # Tuy nhiên, kiểm tra trong message hoặc query DB xem tên lưu là gì nếu cần.
    # Trong app.py: results.append({"filename": file.filename ...}) -> trả về tên gốc.
    
    # Kiểm tra DB xem đã lưu đúng tên mới chưa
    all_docs = client.get("/documents/").json()
    saved_doc = next((d for d in all_docs if d['file_name'].startswith("api_test")), None)
    assert saved_doc is not None
    assert "sentence" in saved_doc["file_name"] # api_test_sentence.txt

def test_document_crud(client, tmp_path):
    # 1. Upload file
    d = tmp_path / "subdir"
    d.mkdir()
    p = d / "crud_test.txt"
    p.write_text("CRUD Content", encoding="utf-8")
    
    with open(p, "rb") as f:
        response = client.post("/upload/", files={"files": ("crud_test.txt", f, "text/plain")})
    assert response.status_code == 200
    
    # Get all to find ID
    docs = client.get("/documents/").json()
    assert len(docs) > 0
    doc_id = docs[0]["id"]
    
    # 2. Get Detail
    resp_detail = client.get(f"/documents/{doc_id}")
    assert resp_detail.status_code == 200
    detail_data = resp_detail.json()
    # Tên file đã được thêm suffix _sentence mặc định
    assert detail_data["document"]["file_name"] == "crud_test_sentence.txt"
    assert len(detail_data["chunks"]) > 0
    
    # 3. Update
    new_name = "crud_updated.txt"
    resp_update = client.put(f"/documents/{doc_id}", params={"new_name": new_name})
    assert resp_update.status_code == 200
    assert resp_update.json()["document"]["file_name"] == new_name
    
    # 4. Delete
    resp_delete = client.delete(f"/documents/{doc_id}")
    assert resp_delete.status_code == 200
    
    # Verify deletion
    resp_check = client.get(f"/documents/{doc_id}")
    assert resp_check.status_code == 404

if __name__ == "__main__":
    pytest.main([__file__])
