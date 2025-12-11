import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Thêm thư mục src vào path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from main import process_directory, process_file

@patch('main.init_database')
@patch('main.process_file')
@patch('os.walk')
@patch('os.path.exists')
def test_process_directory(mock_exists, mock_walk, mock_process_file, mock_init_db, tmp_path):
    # Setup mocks
    mock_exists.return_value = True
    
    # Giả lập cấu trúc thư mục: root, dirs, files
    mock_walk.return_value = [
        ('/root', [], ['file1.txt', 'file2.pdf', 'file3.docx'])
    ]
    
    # file1: thành công
    # file2: thất bại
    # file3: bỏ qua (None)
    mock_process_file.side_effect = [True, False, None]
    
    process_directory('/fake/path')
    
    # Verify
    mock_init_db.assert_called_once()
    assert mock_process_file.call_count == 3
    
def test_process_file_success():
    with patch('main.PROCESSORS') as mock_processors:
        mock_handler = MagicMock()
        mock_handler.return_value = {
            'content': 'dummy content',
            'metadata': {'file_size': 123}
        }
        # Giả lập support .txt
        mock_processors.__contains__.return_value = True 
        mock_processors.__getitem__.return_value = mock_handler
        
        # Patch các hàm phụ thuộc khác
        with patch('main.get_unique_filename') as mock_unique, \
             patch('main.chunk_text') as mock_chunk, \
             patch('main.save_document') as mock_save_doc, \
             patch('main.save_chunks') as mock_save_chunks, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', new_callable=MagicMock) as mock_open:
            
            mock_unique.return_value = 'test.txt'
            mock_chunk.return_value = ['chunk1']
            mock_save_doc.return_value = 1
            
            # Gọi hàm với chế độ mặc định (sentence)
            result = process_file('path/to/test.txt')
            assert result is True
            mock_chunk.assert_called_with('dummy content', mode='sentence')
            mock_save_doc.assert_called_once()
            
            # Reset mocks cho lần gọi sau
            mock_chunk.reset_mock()
            mock_save_doc.reset_mock()
            mock_save_chunks.reset_mock()
            
            # Gọi hàm với chế độ paragraph
            result_para = process_file('path/to/test.txt', chunk_mode='paragraph')
            assert result_para is True
            mock_chunk.assert_called_with('dummy content', mode='paragraph')
            mock_save_doc.assert_called_once()
            mock_save_chunks.assert_called_once()
            
            # Verify file saving logic
            mock_makedirs.assert_called()
            mock_open.assert_called()

def test_process_file_unsupported():
    with patch('main.PROCESSORS', {}) as mock_processors: 
        # Dict rỗng -> không support gì cả
        result = process_file('test.xyz')
        assert result is None
