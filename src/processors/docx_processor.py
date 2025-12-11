import docx
import os

def process_docx(filepath):
    """
    Trích xuất văn bản từ file DOCX.
    - Sử dụng python-docx để đọc nội dung.
    - Trả về content + metadata (file_name, file_size, paragraph_count).
    """
    try:
        file_name = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)

        # Đọc file DOCX
        doc = docx.Document(filepath)
        
        # Trích xuất text từ tất cả paragraphs
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text)
        
        content = "\n".join(paragraphs)

        return {
            "content": content,
            "metadata": {
                "file_name": file_name,
                "file_size": file_size,
                "paragraph_count": len(paragraphs),
            }
        }

    except Exception as e:
        print(f"Lỗi khi xử lý file DOCX {filepath}: {e}")
        return None
