import sys
import os
import pytest

# Thêm thư mục src vào path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from chunker import chunk_text

def test_chunk_text_empty():
    assert chunk_text("") == []
    assert chunk_text(None) == []

def test_chunk_text_basic():
    text = "Hello world. This is a test."
    chunks = chunk_text(text, max_size=100)
    # Tùy thuộc vào cách cài đặt, nó có thể là 1 hoặc 2 chunks
    assert len(chunks) > 0
    assert "Hello world" in chunks[0]

def test_chunk_text_limit():
    # Tạo văn bản dài
    text = "A" * 1000
    chunks = chunk_text(text, max_size=100)
    assert len(chunks) >= 10
    for chunk in chunks:
        assert len(chunk) <= 100

if __name__ == "__main__":
    pytest.main([__file__])
