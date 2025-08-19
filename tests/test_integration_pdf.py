"""
Integration tests for PapperMate PDF conversion.

These tests use real PDFs from pdfContracts/ to validate the system.
Marked as slow tests due to real PDF processing.
"""

import pytest
import os
from pathlib import Path
from pappermate.services.pdf_converter import PDFConverterService


@pytest.mark.slow
class TestPDFIntegration:
    """Integration tests with real PDFs."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use a temporary output directory for tests
        self.test_output_dir = "test_converted_documents"
        self.converter = PDFConverterService(output_dir=self.test_output_dir)
        
        # Find a small PDF for testing
        pdf_dir = Path("pdfContracts")
        if pdf_dir.exists():
            # Look for the smallest PDF file
            pdf_files = list(pdf_dir.glob("*.pdf"))
            if pdf_files:
                # Sort by file size and pick the smallest
                pdf_files.sort(key=lambda x: x.stat().st_size)
                self.test_pdf = str(pdf_files[0])
                print(f"📄 Using test PDF: {self.test_pdf} ({pdf_files[0].stat().st_size} bytes)")
            else:
                pytest.skip("No PDF files found in pdfContracts/")
        else:
            pytest.skip("pdfContracts/ directory not found")
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up test output directory
        import shutil
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)
    
    def test_convert_pdf_to_markdown_real(self):
        """Test PDF to Markdown conversion with real PDF."""
        print(f"🧪 Testing Markdown conversion with: {self.test_pdf}")
        
        result = self.converter.convert_pdf_to_markdown(self.test_pdf)
        
        # Basic validation
        assert result.success is True, f"Conversion failed: {result.error_message}"
        assert result.markdown_content is not None, "Markdown content is None"
        assert len(result.markdown_content) > 0, "Markdown content is empty"
        assert result.processing_time is not None, "Processing time not recorded"
        assert result.processing_time > 0, "Processing time should be positive"
        
        # Metadata validation
        assert result.metadata is not None, "Metadata is None"
        assert "input_file" in result.metadata, "Input file not in metadata"
        assert "output_file" in result.metadata, "Output file not in metadata"
        assert "skip_tables" in result.metadata, "skip_tables not in metadata"
        assert "conversion_method" in result.metadata, "Conversion method not in metadata"
        
        print(f"✅ Markdown conversion successful: {len(result.markdown_content)} characters")
        print(f"⏱️ Processing time: {result.processing_time:.2f}s")
        print(f"🔧 Skip tables: {result.metadata['skip_tables']}")
        print(f"📝 Conversion method: {result.metadata['conversion_method']}")
    
    def test_convert_pdf_to_json_real(self):
        """Test PDF to JSON conversion with real PDF."""
        print(f"🧪 Testing JSON conversion with: {self.test_pdf}")
        
        result = self.converter.convert_pdf_to_json(self.test_pdf)
        
        # Basic validation
        assert result.success is True, f"Conversion failed: {result.error_message}"
        assert result.json_content is not None, "JSON content is None"
        assert result.processing_time is not None, "Processing time not recorded"
        assert result.processing_time > 0, "Processing time should be positive"
        
        # Metadata validation
        assert result.metadata is not None, "Metadata is None"
        assert "input_file" in result.metadata, "Input file not in metadata"
        assert "output_file" in result.metadata, "Output file not in metadata"
        assert "skip_tables" in result.metadata, "skip_tables not in metadata"
        assert "conversion_method" in result.metadata, "Conversion method not in metadata"
        
        print(f"✅ JSON conversion successful: {len(str(result.json_content))} characters")
        print(f"⏱️ Processing time: {result.processing_time:.2f}s")
        print(f"🔧 Skip tables: {result.metadata['skip_tables']}")
        print(f"📝 Conversion method: {result.metadata['conversion_method']}")
    
    def test_convert_pdf_to_both_real(self):
        """Test PDF to both formats conversion with real PDF."""
        print(f"🧪 Testing both formats conversion with: {self.test_pdf}")
        
        result = self.converter.convert_pdf_to_both(self.test_pdf)
        
        # Basic validation
        assert result.success is True, f"Conversion failed: {result.error_message}"
        assert result.markdown_content is not None, "Markdown content is None"
        assert result.json_content is not None, "JSON content is None"
        assert result.processing_time is not None, "Processing time not recorded"
        assert result.processing_time > 0, "Processing time should be positive"
        
        # Metadata validation
        assert result.metadata is not None, "Metadata is None"
        assert "markdown" in result.metadata, "Markdown metadata not in result"
        assert "json" in result.metadata, "JSON metadata not in result"
        assert "skip_tables" in result.metadata, "skip_tables not in metadata"
        assert "conversion_method" in result.metadata, "Conversion method not in metadata"
        
        print(f"✅ Both formats conversion successful")
        print(f"📝 Markdown: {len(result.markdown_content)} characters")
        print(f"📊 JSON: {len(str(result.json_content))} characters")
        print(f"⏱️ Total processing time: {result.processing_time:.2f}s")
        print(f"🔧 Skip tables: {result.metadata['skip_tables']}")
        print(f"📝 Conversion method: {result.metadata['conversion_method']}")
    
    def test_conversion_stats(self):
        """Test conversion statistics after processing."""
        # First convert a PDF
        result = self.converter.convert_pdf_to_markdown(self.test_pdf)
        assert result.success is True, "Need successful conversion for stats test"
        
        # Get stats
        stats = self.converter.get_conversion_stats()
        
        # Validate stats
        assert "total_markdown_files" in stats, "Markdown file count not in stats"
        assert "total_json_files" in stats, "JSON file count not in stats"
        assert "output_directory" in stats, "Output directory not in stats"
        assert "skip_tables" in stats, "skip_tables not in stats"
        assert "marker_initialized" in stats, "Marker initialization status not in stats"
        
        # Validate values
        assert stats["total_markdown_files"] >= 0, "Markdown file count should be non-negative"
        assert stats["total_json_files"] >= 0, "JSON file count should be non-negative"
        assert stats["skip_tables"] is True, "skip_tables should be True for MS1 stability"
        assert stats["marker_initialized"] is True, "Marker should be initialized"
        
        print(f"📊 Conversion stats: {stats}")


@pytest.mark.slow
class TestPDFConfiguration:
    """Test PDF converter configuration options."""
    
    def test_skip_tables_constructor_override(self):
        """Test skip_tables constructor parameter override."""
        # Test with skip_tables=False (should override env default)
        converter = PDFConverterService(skip_tables=False)
        assert converter.skip_tables is False, "Constructor parameter should override env default"
        
        # Test with skip_tables=True (should override env default)
        converter = PDFConverterService(skip_tables=True)
        assert converter.skip_tables is True, "Constructor parameter should override env default"
    
    def test_environment_variable_parsing(self):
        """Test environment variable parsing for skip_tables."""
        # Test various environment variable values
        test_cases = [
            ("1", True),
            ("true", True),
            ("yes", True),
            ("0", False),
            ("false", False),
            ("no", False),
            ("", True),  # Default when not set
        ]
        
        for env_value, expected in test_cases:
            if env_value:
                os.environ["PAPPERMATE_SKIP_TABLES"] = env_value
            else:
                os.environ.pop("PAPPERMATE_SKIP_TABLES", None)
            
            converter = PDFConverterService()
            assert converter.skip_tables == expected, f"Expected {expected} for env value '{env_value}'"
    
    def test_output_directory_creation(self):
        """Test output directory creation."""
        test_dir = "test_output_dir_creation"
        
        # Ensure directory doesn't exist
        if os.path.exists(test_dir):
            import shutil
            shutil.rmtree(test_dir)
        
        # Create converter with new directory
        converter = PDFConverterService(output_dir=test_dir)
        
        # Check if directories were created
        assert os.path.exists(test_dir), "Output directory should be created"
        assert os.path.exists(os.path.join(test_dir, "markdown")), "Markdown subdirectory should be created"
        assert os.path.exists(os.path.join(test_dir, "json")), "JSON subdirectory should be created"
        
        # Clean up
        import shutil
        shutil.rmtree(test_dir)
