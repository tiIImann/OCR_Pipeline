import re

def chunk_text(text, mode="sentence", max_size=1000):
    if not text:
        return []

    text = text.strip()
    chunks = []
    current = ""

    # --- Tách đoạn hoặc câu ---
    if mode == "paragraph":
        parts = [p.strip() for p in text.split("\n") if p.strip()]
        glue = "\n"

    else:  # mode == "sentence"
        # Regex: tách câu có . ? !
        parts = re.findall(r'[^.!?]*[.!?]', text)
        parts = [s.strip() for s in parts if s.strip()]
        glue = " "
        
        # Fallback: nếu không có câu nào, chia theo max_size
        if not parts:
            parts = [text[i:i+max_size] for i in range(0, len(text), max_size)]
            return [p.strip() for p in parts if p.strip()]

    # ==========================================================
    # XỬ LÝ TỪNG PHẦN (câu hoặc đoạn) ĐỂ TẠO CHUNKS
    # ==========================================================
    # Thuật toán:
    # - Duyệt qua từng phần (câu/đoạn) đã tách
    # - Cố gắng ghép nhiều phần vào 1 chunk sao cho không vượt max_size
    # - Nếu 1 phần đơn lẻ đã vượt max_size thì chia nhỏ phần đó
    # ==========================================================
    
    for p in parts:
        # Thêm ký tự nối (dấu cách hoặc xuống dòng) sau mỗi phần
        item = p + glue

        # ----- TRƯỜNG HỢP 1: Phần hiện tại QUÁ DÀI (> max_size) -----
        # Ví dụ: Một câu dài 1500 ký tự, max_size = 1000
        # => Phải chia câu đó thành nhiều chunks nhỏ hơn
        if len(item) > max_size:
            # Lưu chunk đang build (nếu có) trước khi xử lý phần dài
            if current:
                chunks.append(current.strip())
                current = ""

            # Chia phần dài thành nhiều mảnh, mỗi mảnh <= max_size
            start = 0
            while start < len(item):
                cut = item[start:start + max_size]
                chunks.append(cut.strip())
                start += max_size

            continue  # Bỏ qua logic ghép bên dưới, xử lý phần tiếp theo

        # ----- TRƯỜNG HỢP 2: Có thể GHÉP vào chunk hiện tại -----
        # Kiểm tra nếu ghép thêm phần này vẫn không vượt max_size
        if len(current) + len(item) <= max_size:
            current += item  # Ghép vào chunk đang build
        else:
            # ----- TRƯỜNG HỢP 3: Ghép sẽ VƯỢT max_size -----
            # Lưu chunk hiện tại và bắt đầu chunk mới với phần này
            chunks.append(current.strip())
            current = item

    # ==========================================================
    # LƯU CHUNK CUỐI CÙNG (nếu còn dữ liệu trong buffer)
    # ==========================================================
    if current:
        chunks.append(current.strip())

    return chunks
