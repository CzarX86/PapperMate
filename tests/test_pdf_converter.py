"""
Tests for PapperMate PDF converter service.

Testing PDF conversion functionality using Marker.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from pappermate.services.pdf_converter import PDFConverterService, ConversionResult


class TestPDFConverterService:
    """Test PDF converter service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directory for tests
        self.temp_dir = tempfile.mkdtemp()
        self.converter = PDFConverterService(output_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_service_initialization(self):
        """Test service initialization."""
        assert self.converter.output_dir.exists()
        assert (self.converter.output_dir / "markdown").exists()
        assert (self.converter.output_dir / "json").exists()
    
    def test_convert_pdf_to_markdown_file_not_found(self):
        """Test conversion with non-existent file."""
        result = self.converter.convert_pdf_to_markdown("/non/existent/file.pdf")
        
        assert result.success is False
        assert "PDF file not found" in result.error_message
        assert result.processing_time is not None
    
    @patch('pappermate.services.pdf_converter.PdfConverter')
    def test_convert_pdf_to_markdown_success(self, mock_converter):
        """Test successful PDF to Markdown conversion."""
        # Mock Marker response
        mock_instance = mock_converter.return_value
        mock_rendered = Mock()
        mock_rendered.markdown = "# Test Document\n\nThis is a test PDF content."
        mock_instance.return_value = mock_rendered
        
        # Create temporary PDF file
        pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("PDF content")
        
        result = self.converter.convert_pdf_to_markdown(pdf_path)
        
        assert result.success is True
        assert result.markdown_content == "# Test Document\n\nThis is a test PDF content."
        assert result.processing_time is not None
        assert result.metadata is not None
        assert "input_file" in result.metadata
        assert "output_file" in result.metadata
    
    @patch('pappermate.services.pdf_converter.PdfConverter')
    def test_convert_pdf_to_json_success(self, mock_converter):
        """Test successful PDF to JSON conversion."""
        # Mock Marker response
        mock_instance = mock_converter.return_value
        mock_rendered = Mock()
        mock_rendered.children = {
            "pages": [
                {
                    "id": "page_1",
                    "content": "Test content",
                    "blocks": []
                }
            ]
        }
        mock_instance.return_value = mock_rendered
        
        # Create temporary PDF file
        pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("PDF content")
        
        result = self.converter.convert_pdf_to_json(pdf_path)
        
        assert result.success is True
        assert result.json_content is not None
        assert "pages" in result.json_content
        assert result.processing_time is not None
        assert result.metadata is not None
    
    @patch('pappermate.services.pdf_converter.PdfConverter')
    def test_convert_pdf_to_both_success(self, mock_converter):
        """Test successful conversion to both formats."""
        # Mock Marker responses - simpler approach
        mock_instance = mock_converter.return_value
        
        # First call returns markdown result
        mock_rendered_md = Mock()
        mock_rendered_md.markdown = "# Test Document\n\nContent"
        
        # Second call returns JSON result  
        mock_rendered_json = Mock()
        mock_rendered_json.children = {"pages": [{"content": "Test content"}]}
        
        # Configure mock to return different values on subsequent calls
        mock_instance.side_effect = [mock_rendered_md, mock_rendered_json]
        
        # Create temporary PDF file
        pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("PDF content")
        
        result = self.converter.convert_pdf_to_both(pdf_path)
        
        assert result.success is True
        assert result.markdown_content is not None
        assert result.json_content is not None
        assert result.processing_time is not None
        assert result.metadata is not None
    
    def test_convert_pdf_to_both_partial_failure(self):
        """Test conversion when one format fails."""
        # Create temporary PDF file
        pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("PDF content")
        
        with patch('pappermate.services.pdf_converter.PdfConverter') as mock_converter:
            # Markdown succeeds, JSON fails
            mock_instance = mock_converter.return_value
            mock_rendered = Mock()
            mock_rendered.markdown = "# Test Document"
            mock_instance.return_value = mock_rendered
            
            result = self.converter.convert_pdf_to_both(pdf_path)
            
            assert result.success is True
            assert result.markdown_content is not None
            assert result.json_content is None
            assert result.processing_time is not None
    
    def test_get_conversion_stats(self):
        """Test getting conversion statistics."""
        # Create some test files
        markdown_dir = self.converter.output_dir / "markdown"
        json_dir = self.converter.output_dir / "json"
        
        # Create test markdown file
        (markdown_dir / "test1.md").write_text("# Test 1")
        (markdown_dir / "test2.md").write_text("# Test 2")
        
        # Create test JSON file
        (json_dir / "test1.json").write_text('{"test": "data"}')
        
        stats = self.converter.get_conversion_stats()
        
        assert stats["total_markdown_files"] == 2
        assert stats["total_json_files"] == 1
        assert "test1.md" in stats["markdown_files"]
        assert "test2.md" in stats["markdown_files"]
        assert "test1.json" in stats["json_files"]
        assert stats["output_directory"] == str(self.converter.output_dir)


class TestConversionResult:
    """Test ConversionResult model."""
    
    def test_conversion_result_creation(self):
        """Test creating ConversionResult."""
        result = ConversionResult(
            success=True,
            markdown_content="# Test",
            processing_time=1.5,
            metadata={"test": "data"}
        )
        
        assert result.success is True
        assert result.markdown_content == "# Test"
        assert result.processing_time == 1.5
        assert result.metadata["test"] == "data"
        assert result.error_message is None
    
    def test_conversion_result_error(self):
        """Test ConversionResult with error."""
        result = ConversionResult(
            success=False,
            error_message="Conversion failed",
            processing_time=0.5
        )
        
        assert result.success is False
        assert result.error_message == "Conversion failed"
        assert result.processing_time == 0.5
        assert result.markdown_content is None
        assert result.json_content is None
