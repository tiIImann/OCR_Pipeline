import sys
import os
import pytest

# Thêm thư mục src vào path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from processors.txt_processor import process_txt
from processors.pdf_processor import process_pdf 
from processors.docx_processor import process_docx
from unittest.mock import MagicMock, patch

# Helper để tạo file giả lập
@pytest.fixture
def dummy_txt_file(tmp_path):
    d = tmp_path / "subdir"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text("Hello World content.", encoding="utf-8")
    return str(p)

def test_process_txt(dummy_txt_file):
    result = process_txt(dummy_txt_file)
    assert result is not None
    assert result['content'] == "Hello World content."
    assert result['metadata']['file_name'] == "hello.txt"
    assert result['metadata']['file_size'] > 0

@patch('processors.pdf_processor.PyPDF2.PdfReader')
def test_process_pdf(mock_pdf_reader, tmp_path):
    # Thiết lập mock
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "PDF Page Content"
    
    mock_reader_instance = MagicMock()
    mock_reader_instance.pages = [mock_page]
    mock_pdf_reader.return_value = mock_reader_instance

    # Tạo file PDF giả lập (nội dung rỗng cũng được vì chúng ta mock reader)
    d = tmp_path / "subdir"
    d.mkdir(exist_ok=True)
    p = d / "test.pdf"
    p.write_bytes(b"%PDF-1.4...") 
    
    result = process_pdf(str(p))
    
    assert result is not None
    assert "PDF Page Content" in result['content']
    assert result['metadata']['file_name'] == "test.pdf"
    assert result['metadata']['page_count'] == 1

@patch('processors.docx_processor.docx.Document')
def test_process_docx(mock_document, tmp_path):
    # Thiết lập mock
    mock_para = MagicMock()
    mock_para.text = "DOCX Paragraph Content"
    
    mock_doc_instance = MagicMock()
    mock_doc_instance.paragraphs = [mock_para]
    mock_document.return_value = mock_doc_instance

    # Tạo file DOCX giả lập
    d = tmp_path / "subdir"
    d.mkdir(exist_ok=True)
    p = d / "test.docx"
    p.write_bytes(b"PK...")
    
    result = process_docx(str(p))
    
    assert result is not None
    assert "DOCX Paragraph Content" in result['content']
    assert result['metadata']['file_name'] == "test.docx"
    assert result['metadata']['paragraph_count'] == 1

if __name__ == "__main__":
    pytest.main([__file__])
