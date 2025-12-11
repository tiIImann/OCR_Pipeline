import os
import chardet

def process_txt(filepath):
    """
    Đọc nội dung từ file TXT, tự động nhận diện encoding.
    Trả về dictionary gồm content và metadata.
    """
    try:
        file_size = os.path.getsize(filepath)
        file_name = os.path.basename(filepath)
        
        with open(filepath, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'
        
        with open(filepath, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
            
        return {
            "content": content,
            "metadata": {
                "file_name": file_name,
                "file_size": file_size
            }
        }
    except Exception as e:
        print(f"Lỗi khi xử lý file TXT {filepath}: {e}")
        return None
