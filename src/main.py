import os
import sys
import logging
import logging
from database import init_database, save_document, save_chunks, get_unique_filename
from processors.txt_processor import process_txt
from processors.pdf_processor import process_pdf
from processors.docx_processor import process_docx
from chunker import chunk_text

# Cấu hình logging với UTF-8 encoding (hỗ trợ tiếng Việt trên Windows)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pipeline.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
# Fix encoding cho stdout trên Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Ánh xạ đuôi file với processor tương ứng
PROCESSORS = {
    '.txt': process_txt,
    '.pdf': process_pdf,
    '.docx': process_docx
}

def process_file(filepath, chunk_mode="sentence"):
    """
    Xử lý một file cụ thể: Extract -> Chunk -> Save DB.
    Trả về True nếu thành công, False nếu thất bại.
    """
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in PROCESSORS:
        logging.warning(f"Bỏ qua file không được hỗ trợ: {filename}")
        return None  # None = bỏ qua, không phải thất bại

    # Tạo tên file duy nhất nếu trùng tên
    unique_filename = get_unique_filename(filename)
    if unique_filename != filename:
        logging.info(f"Phát hiện trùng tên. Đổi tên từ {filename} thành {unique_filename}")

    logging.info(f"Đang xử lý file: {filename} với chế độ chunking: {chunk_mode}")
    
    try:
        processor = PROCESSORS[ext]
        result = processor(filepath)

        if not result:
            logging.warning(f"Không thể trích xuất nội dung từ {filename} (kết quả rỗng).")
            return False

        content = result['content']
        metadata = result['metadata']
        
        # Chia nhỏ nội dung
        chunks_text = chunk_text(content, mode=chunk_mode)
        
        # Chuẩn bị metadata document
        file_info = {
            'file_name': unique_filename,
            'file_path': filepath,
            'file_type': ext,
            'file_size': metadata.get('file_size'),
            'chunk_count': len(chunks_text)
        }
        
        # Lưu document
        doc_id = save_document(file_info)
        
        # Chuẩn bị dữ liệu chunks
        chunks_data = []
        for i, chunk_content in enumerate(chunks_text):
            chunks_data.append({
                'chunk_index': i,
                'content': chunk_content,
                'char_count': len(chunk_content)
            })
        
        # Lưu chunks
        # Lưu chunks vào database
        save_chunks(doc_id, chunks_data)
        
        # Lưu chunks ra file vật lý
        try:
            # Tạo tên thư mục: tenfile_duoifile_chunks (ví dụ: test_ocr_txt_chunks)
            clean_filename = unique_filename.replace('.', '_')
            
            # Logic: Input ở folder nào thì chunks_data sẽ nằm ngang hàng với folder đó
            # Ví dụ: input_docs/file.txt -> chunks_data/file_txt_mode_chunks
            parent_dir = os.path.dirname(filepath) # Folder chứa file
            root_dir = os.path.dirname(parent_dir) # Folder cha của folder chứa file
            chunks_base_dir = os.path.join(root_dir, "chunks_data")
            
            chunks_dir = os.path.join(chunks_base_dir, f"{clean_filename}_{chunk_mode}_chunks")
            
            if not os.path.exists(chunks_dir):
                os.makedirs(chunks_dir)
                
            for i, chunk_content in enumerate(chunks_text):
                chunk_filename = f"chunk_{i}.txt"
                chunk_path = os.path.join(chunks_dir, chunk_filename)
                with open(chunk_path, "w", encoding="utf-8") as f:
                    f.write(chunk_content)
            
            logging.info(f"Đã lưu {len(chunks_text)} file chunks vào thư mục: {chunks_dir}")
            
        except Exception as e:
            logging.error(f"Lỗi khi lưu file chunks vật lý: {e}")

        logging.info(f"Xử lý thành công {filename}. Đã lưu {len(chunks_data)} chunks vào DB.")
        return True
            
    except Exception as e:
        logging.error(f"Lỗi khi xử lý {filename}: {e}", exc_info=True)
        return False

def process_directory(directory_path):
    """
    Duyệt và xử lý toàn bộ file trong thư mục.
    """
    # Khởi tạo database
    try:
        init_database()
        logging.info("Khởi tạo database thành công.")
    except Exception as e:
        logging.critical(f"Không thể khởi tạo database: {e}")
        return

    if not os.path.exists(directory_path):
        logging.error(f"Không tìm thấy thư mục: {directory_path}")
        return

    logging.info(f"Đang quét thư mục: {directory_path}")
    
    count_success = 0
    count_fail = 0
    count_skip = 0
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            filepath = os.path.join(root, file)
            result = process_file(filepath)
            if result is True:
                count_success += 1
            elif result is False:
                count_fail += 1
            else:  # result is None -> bỏ qua
                count_skip += 1
                
    logging.info(f"Hoàn thành xử lý batch. Thành công: {count_success}, Thất bại: {count_fail}, Bỏ qua: {count_skip}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = "input_docs"  # Thư mục mặc định
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            logging.info(f"Đã tạo thư mục đầu vào mặc định: {target_dir}")
    
    process_directory(target_dir)
