import PyPDF2
import os

def process_pdf(filepath):
    """
    Trích xuất văn bản từ file PDF.
    Trả về dictionary gồm content và metadata.
    Bỏ qua PDF dạng scan (không có text layer).
    """
    text = ""
    try:
        file_size = os.path.getsize(filepath)
        file_name = os.path.basename(filepath)
        
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            num_pages = len(reader.pages)
            
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # Nếu không trích xuất được text nào, coi là file scan và bỏ qua
        if not text.strip():
            print(f"Bỏ qua PDF dạng scan (không có text layer): {filepath}")
            return None

        return {
            "content": text,
            "metadata": {
                "file_name": file_name,
                "file_size": file_size,
                "page_count": num_pages
            }
        }
    except Exception as e:
        print(f"Lỗi khi xử lý file PDF {filepath}: {e}")
        return None
