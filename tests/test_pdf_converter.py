"""
Tests for PDFConverterService.
Tests PDF conversion functionality using mocked Marker components.
"""

import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import pytest

from src.pappermate.services.pdf_converter import PDFConverterService, ConversionResult


class TestPDFConverterService:
    """Test PDFConverterService functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.converter = PDFConverterService(output_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        if hasattr(self.converter, 'cleanup'):
            self.converter.cleanup()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.pappermate.services.pdf_converter.MARKER_AVAILABLE', True)
    @patch('src.pappermate.services.pdf_converter.create_model_dict')
    @patch('src.pappermate.services.pdf_converter.ConfigParser')
    @patch('src.pappermate.services.pdf_converter.PdfConverter')
    def test_service_initialization(self, mock_converter, mock_config_parser, mock_create_models):
        """Test service initialization."""
        # Mock Marker components
        mock_models = Mock()
        mock_create_models.return_value = mock_models
        
        mock_config = Mock()
        mock_config_parser.return_value = mock_config
        
        mock_pdf_converter = Mock()
        mock_converter.return_value = mock_pdf_converter
        
        # Create service
        service = PDFConverterService()
        
        assert service.marker_initialized is True
        assert service.models == mock_models
        assert service.converter == mock_pdf_converter

    def test_convert_pdf_to_markdown_file_not_found(self):
        """Test conversion when PDF file is not found."""
        result = self.converter.convert_pdf_to_markdown("nonexistent.pdf")
        
        assert result.success is False
        assert "PDF file not found" in result.error_message
        assert result.processing_time is not None

    @patch('src.pappermate.services.pdf_converter.MARKER_AVAILABLE', True)
    @patch('src.pappermate.services.pdf_converter.create_model_dict')
    @patch('src.pappermate.services.pdf_converter.ConfigParser')
    @patch('src.pappermate.services.pdf_converter.PdfConverter')
    def test_convert_pdf_to_markdown_success(self, mock_converter, mock_config_parser, mock_create_models):
        """Test successful PDF to Markdown conversion."""
        # Mock Marker components
        mock_models = Mock()
        mock_create_models.return_value = mock_models
        
        mock_config = Mock()
        mock_config_parser.return_value = mock_config
        mock_config.get_processors.return_value = []
        mock_config.generate_config_dict.return_value = {}
        mock_config.get_renderer.return_value = Mock()
        
        mock_pdf_converter = Mock()
        mock_converter.return_value = mock_pdf_converter
        
        # Mock Marker response
        mock_rendered = Mock()
        mock_rendered.markdown = "# Test Document\n\nThis is a test PDF content."
        mock_pdf_converter.return_value = mock_rendered
        
        # Create service with mocked components
        service = PDFConverterService()
        service.models = mock_models
        service.config_parser = mock_config_parser
        service.converter = mock_pdf_converter
        service.marker_initialized = True
        
        # Create temporary PDF file
        pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("PDF content")
        
        result = service.convert_pdf_to_markdown(pdf_path)
        
        assert result.success is True
        assert result.markdown_content == "# Test Document\n\nThis is a test PDF content."
        assert result.processing_time is not None

    @patch('src.pappermate.services.pdf_converter.MARKER_AVAILABLE', True)
    @patch('src.pappermate.services.pdf_converter.create_model_dict')
    @patch('src.pappermate.services.pdf_converter.ConfigParser')
    @patch('src.pappermate.services.pdf_converter.PdfConverter')
    def test_convert_pdf_to_json_success(self, mock_converter, mock_config_parser, mock_create_models):
        """Test successful PDF to JSON conversion."""
        # Mock Marker components
        mock_models = Mock()
        mock_create_models.return_value = mock_models
        
        mock_config = Mock()
        mock_config_parser.return_value = mock_config
        mock_config.get_processors.return_value = []
        mock_config.generate_config_dict.return_value = {}
        mock_config.get_renderer.return_value = Mock()
        
        mock_pdf_converter = Mock()
        mock_converter.return_value = mock_pdf_converter
        
        # Mock Marker response
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
        mock_pdf_converter.return_value = mock_rendered
        
        # Create service with mocked components
        service = PDFConverterService()
        service.models = mock_models
        service.config_parser = mock_config_parser
        service.converter = mock_pdf_converter
        service.marker_initialized = True
        
        # Create temporary PDF file
        pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("PDF content")
        
        result = service.convert_pdf_to_json(pdf_path)
        
        assert result.success is True
        assert result.json_content is not None
        assert result.processing_time is not None

    @patch('src.pappermate.services.pdf_converter.MARKER_AVAILABLE', True)
    @patch('src.pappermate.services.pdf_converter.create_model_dict')
    @patch('src.pappermate.services.pdf_converter.ConfigParser')
    @patch('src.pappermate.services.pdf_converter.PdfConverter')
    def test_convert_pdf_to_both_success(self, mock_converter, mock_config_parser, mock_create_models):
        """Test successful conversion to both formats."""
        # Mock Marker components
        mock_models = Mock()
        mock_create_models.return_value = mock_models
        
        mock_config = Mock()
        mock_config_parser.return_value = mock_config
        mock_config.get_processors.return_value = []
        mock_config.generate_config_dict.return_value = {}
        mock_config.get_renderer.return_value = Mock()
        
        mock_pdf_converter = Mock()
        mock_converter.return_value = mock_pdf_converter
        
        # Create service with mocked components
        service = PDFConverterService()
        service.models = mock_models
        service.config_parser = mock_config_parser
        service.converter = mock_pdf_converter
        service.marker_initialized = True
        
        # Mock responses for both conversions
        mock_rendered_md = Mock()
        mock_rendered_md.markdown = "# Test Document\n\nContent"
        
        mock_rendered_json = Mock()
        mock_rendered_json.children = {"pages": [{"content": "Test content"}]}
        
        # Configure mock to return different values on subsequent calls
        mock_pdf_converter.side_effect = [mock_rendered_md, mock_rendered_json]
        
        # Create temporary PDF file
        pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("PDF content")
        
        result = service.convert_pdf_to_both(pdf_path)
        
        assert result.success is True
        assert result.markdown_content is not None
        assert result.json_content is not None
        assert result.processing_time is not None

    def test_convert_pdf_to_both_partial_failure(self):
        """Test conversion when one format fails."""
        # Create temporary PDF file
        pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(pdf_path, 'w') as f:
            f.write("PDF content")
        
        # Test with service that has Marker not initialized
        result = self.converter.convert_pdf_to_both(pdf_path)
        
        # Should fail because Marker is not initialized
        assert result.success is False
        assert "Marker not initialized" in result.error_message

    def test_get_conversion_stats(self):
        """Test conversion statistics."""
        stats = self.converter.get_conversion_stats()
        
        assert "total_markdown_files" in stats
        assert "total_json_files" in stats
        assert "output_directory" in stats
        assert "skip_tables" in stats
        assert "marker_initialized" in stats
        assert "filename_mapping" in stats


class TestConversionResult:
    """Test ConversionResult model."""

    def test_conversion_result_creation(self):
        """Test ConversionResult creation."""
        result = ConversionResult(
            success=True,
            markdown_content="# Test",
            processing_time=1.5,
            metadata={"test": "value"}
        )
        
        assert result.success is True
        assert result.markdown_content == "# Test"
        assert result.processing_time == 1.5
        assert result.metadata["test"] == "value"

    def test_conversion_result_error(self):
        """Test ConversionResult with error."""
        result = ConversionResult(
            success=False,
            error_message="Test error",
            processing_time=0.5
        )
        
        assert result.success is False
        assert result.error_message == "Test error"
        assert result.processing_time == 0.5
