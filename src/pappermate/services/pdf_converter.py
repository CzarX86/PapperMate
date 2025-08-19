"""
PDF Converter Service for PapperMate

Service for converting PDFs to Markdown and JSON using Marker PDF.
"""

import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import json
import sys

# Add Marker to path for local submodule import
marker_path = Path(__file__).parent.parent.parent / "Marker_PapperMate"
if str(marker_path) not in sys.path:
    sys.path.insert(0, str(marker_path))

# Force CPU usage to avoid MPS GPU issues
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["USE_MPS"] = "0"

try:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.config.parser import ConfigParser
    from marker.processors.table import TableProcessor as MarkerTableProcessor
    from marker.logger import get_logger
    from .safe_table_processor import SafeTableProcessor # Import the new SafeTableProcessor

    MARKER_AVAILABLE = True
    logger = get_logger()
except ImportError as e:
    print(f"Warning: Marker not available: {e}")
    MARKER_AVAILABLE = False
    logger = None

from pydantic import BaseModel

from ..models.document import Document, DocumentType, DocumentStatus
from .file_handler import FileHandler


class ConversionResult(BaseModel):
    success: bool
    markdown_content: Optional[str] = None
    json_content: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    metadata: Dict[str, Any] = None


class PDFConverterService:
    def __init__(self, output_dir: str = "converted_documents", skip_tables: Optional[bool] = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "markdown").mkdir(exist_ok=True)
        (self.output_dir / "json").mkdir(exist_ok=True)

        # Initialize file handler for special characters
        self.file_handler = FileHandler()

        # Configuration: skip_tables can be set via:
        # 1. Constructor parameter (highest priority)
        # 2. Environment variable PAPPERMATE_SKIP_TABLES
        # 3. Default to True for MS1 stability (will be False after Marker fix)
        if skip_tables is not None:
            self.skip_tables = skip_tables
        else:
            env_skip = os.environ.get("PAPPERMATE_SKIP_TABLES", "1")
            self.skip_tables = env_skip.lower() in ("1", "true", "yes")

        print(f"🔧 PapperMate: skip_tables = {self.skip_tables} (tables will be {'disabled' if self.skip_tables else 'enabled'} for conversion)")

        try:
            self.models = create_model_dict()
            self.config_parser = ConfigParser({})
            self.converter = PdfConverter(artifact_dict=self.models)
            self.marker_initialized = True
            print("✅ Marker initialized successfully")

            # Apply the runtime patch for SafeTableProcessor if tables are enabled
            if not self.skip_tables and MARKER_AVAILABLE:
                self._apply_safe_table_patch()

        except Exception as e:
            print(f"⚠️ Warning: Marker initialization failed: {e}")
            self.marker_initialized = False

    def _apply_safe_table_patch(self):
        """
        Dynamically replaces Marker's TableProcessor.__call__ with a safe version
        that catches exceptions and logs them, allowing the pipeline to continue.
        """
        if not hasattr(MarkerTableProcessor, '_original_call'):
            MarkerTableProcessor._original_call = MarkerTableProcessor.__call__

        def safe_call(instance, document):
            try:
                return MarkerTableProcessor._original_call(instance, document)
            except Exception as e:
                logger.error(f"PapperMate SafeTable patch: skipping table processing due to error: {e}")
                # Return a dummy document or modify the existing one to remove table blocks
                # For now, just return None or an empty list of tables to prevent crash
                # The rest of the pipeline will proceed without table data
                return None # Or an empty Document object if that's what's expected

        MarkerTableProcessor.__call__ = safe_call
        logger.info("PapperMate SafeTable patch applied to MarkerTableProcessor.__call__")

    def _get_conversion_config(self, output_format: str = "markdown") -> Dict[str, Any]:
        """Get Marker configuration with skip_tables options."""
        config = {
            "skip_tables": self.skip_tables,
            "disable_table_processing": self.skip_tables,
        }
        
        if self.skip_tables:
            config["table_processor"] = "none"
        
        return config

    def _process_pdf_safely(self, pdf_path: str, processor_func, *args, **kwargs):
        """
        Process PDF safely using FileHandler to handle special characters in filenames.
        """
        try:
            # Check if filename needs sanitization
            if self.file_handler.is_safe_filename(pdf_path):
                # Filename is safe, process directly
                return processor_func(pdf_path, *args, **kwargs)
            else:
                # Filename has special characters, use FileHandler
                print(f"🔧 Filename contains special characters, using safe processing for: {pdf_path}")
                result = self.file_handler.process_file_safely(pdf_path, processor_func, *args, **kwargs)
                
                # Check if there were translation issues
                self._check_translation_status(pdf_path)
                
                return result
        except Exception as e:
            raise Exception(f"Error in safe PDF processing: {e}")
    
    def _check_translation_status(self, pdf_path: str):
        """Check and report translation status for processed files."""
        status = self.file_handler.get_reprocessing_status()
        
        if status['total_items'] > 0:
            print(f"\n📊 Translation Status Summary:")
            print(f"   Files with translation issues: {status['total_items']}")
            print(f"   Ready for retry: {status['retry_ready']}")
            print(f"   Still failed: {status['failed']}")
            
            # Show specific issues for this file
            pdf_name = Path(pdf_path).name
            for item_data in status['items']:
                if item_data['original_filename'] == pdf_name:
                    print(f"\n⚠️ Translation issue for '{pdf_name}':")
                    print(f"   Error: {item_data['error_message']}")
                    if item_data['retry_after']:
                        print(f"   Will retry after: {item_data['retry_after']}")
                    break
    
    def get_translation_status(self) -> Dict[str, any]:
        """Get current translation status from FileHandler."""
        return self.file_handler.get_reprocessing_status()
    
    def retry_failed_translations(self) -> Dict[str, any]:
        """Retry failed translations that are ready for retry."""
        return self.file_handler.retry_failed_translations()
    
    def print_translation_summary(self):
        """Print a summary of translation issues."""
        self.file_handler.print_reprocessing_summary()

    def convert_pdf_to_markdown(
        self, 
        pdf_path: str, 
        output_filename: Optional[str] = None
    ) -> ConversionResult:
        """
        Convert PDF to Markdown using Marker with safe filename handling.
        
        Args:
            pdf_path: Path to the PDF file
            output_filename: Optional custom output filename
            
        Returns:
            ConversionResult with Markdown content
        """
        start_time = datetime.now()
        
        try:
            # Validate input file
            if not os.path.exists(pdf_path):
                processing_time = (datetime.now() - start_time).total_seconds()
                return ConversionResult(
                    success=False,
                    error_message=f"PDF file not found: {pdf_path}",
                    processing_time=processing_time
                )
            
            # Check if Marker is initialized
            if not self.marker_initialized:
                processing_time = (datetime.now() - start_time).total_seconds()
                return ConversionResult(
                    success=False,
                    error_message="Marker not initialized properly",
                    processing_time=processing_time
                )
            
            # Generate output filename if not provided
            if not output_filename:
                base_name = Path(pdf_path).stem
                output_filename = f"{base_name}_{uuid.uuid4().hex[:8]}.md"
            
            output_path = self.output_dir / "markdown" / output_filename
            
            # Convert using Marker with error handling and skip_tables config
            def _convert_markdown(safe_pdf_path):
                try:
                    config = self._get_conversion_config("markdown")
                    config_parser = ConfigParser(config)
                    
                    processors = config_parser.get_processors()
                    if self.skip_tables:
                        processors = [
                            p for p in processors if p.__class__.__name__ != "TableProcessor"
                        ]

                    converter = PdfConverter(
                        artifact_dict=self.models,
                        config=config_parser.generate_config_dict(),
                        processor_list=processors,
                        renderer=config_parser.get_renderer()
                    )
                    
                    print(f"🔄 Converting {safe_pdf_path} to Markdown...")
                    rendered = converter(safe_pdf_path)
                    markdown_content = rendered.markdown
                    
                except Exception as e:
                    # Fallback: try with basic configuration
                    print(f"⚠️ Primary Markdown conversion failed, trying fallback: {e}")
                    try:
                        basic_converter = PdfConverter(artifact_dict=self.models)
                        rendered = basic_converter(safe_pdf_path)
                        markdown_content = rendered.markdown
                    except Exception as e2:
                        raise Exception(f"PDF to Markdown conversion failed: {e2}")
                
                return markdown_content

            # Process PDF safely
            markdown_content = self._process_pdf_safely(pdf_path, _convert_markdown)
            
            # Save Markdown file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"✅ Markdown conversion successful: {len(markdown_content)} characters in {processing_time:.2f}s")
            
            return ConversionResult(
                success=True,
                markdown_content=markdown_content,
                processing_time=processing_time,
                metadata={
                    "input_file": pdf_path,
                    "output_file": str(output_path),
                    "file_size": len(markdown_content.encode('utf-8')),
                    "skip_tables": self.skip_tables,
                    "conversion_method": "marker_with_fallback"
                }
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            return ConversionResult(
                success=False,
                error_message=str(e),
                processing_time=processing_time
            )
    
    def convert_pdf_to_json(
        self, 
        pdf_path: str, 
        output_filename: Optional[str] = None
    ) -> ConversionResult:
        """
        Convert PDF to JSON using Marker with safe filename handling.
        
        Args:
            pdf_path: Path to the PDF file
            output_filename: Optional custom output filename
            
        Returns:
            ConversionResult with JSON content
        """
        start_time = datetime.now()
        
        try:
            # Validate input file
            if not os.path.exists(pdf_path):
                processing_time = (datetime.now() - start_time).total_seconds()
                return ConversionResult(
                    success=False,
                    error_message=f"PDF file not found: {pdf_path}",
                    processing_time=processing_time
                )
            
            # Check if Marker is initialized
            if not self.marker_initialized:
                processing_time = (datetime.now() - start_time).total_seconds()
                return ConversionResult(
                    success=False,
                    error_message="Marker not initialized properly",
                    processing_time=processing_time
                )
            
            # Generate output filename if not provided
            if not output_filename:
                base_name = Path(pdf_path).stem
                output_filename = f"{base_name}_{uuid.uuid4().hex[:8]}.json"
            
            output_path = self.output_dir / "json" / output_filename
            
            # Convert using Marker with error handling and skip_tables config
            def _convert_json(safe_pdf_path):
                try:
                    config = self._get_conversion_config("json")
                    config_parser = ConfigParser(config)
                    
                    processors = config_parser.get_processors()
                    if self.skip_tables:
                        processors = [
                            p for p in processors if p.__class__.__name__ != "TableProcessor"
                        ]

                    converter = PdfConverter(
                        artifact_dict=self.models,
                        config=config_parser.generate_config_dict(),
                        processor_list=processors,
                        renderer=config_parser.get_renderer()
                    )
                    
                    print(f"🔄 Converting {safe_pdf_path} to JSON...")
                    rendered = converter(safe_pdf_path)
                    
                    # Handle different output types from Marker
                    if hasattr(rendered, 'children'):
                        json_content = rendered.children
                    elif hasattr(rendered, 'json'):
                        json_content = rendered.json
                    else:
                        # Fallback: convert to dict representation
                        json_content = rendered.dict() if hasattr(rendered, 'dict') else str(rendered)
                    
                except Exception as e:
                    # Fallback: try with basic configuration
                    print(f"⚠️ Primary JSON conversion failed, trying fallback: {e}")
                    try:
                        basic_converter = PdfConverter(artifact_dict=self.models)
                        rendered = basic_converter(safe_pdf_path)
                        
                        if hasattr(rendered, 'children'):
                            json_content = rendered.children
                        elif hasattr(rendered, 'json'):
                            json_content = rendered.json
                        else:
                            json_content = rendered.dict() if hasattr(rendered, 'dict') else str(rendered)
                            
                    except Exception as e2:
                        raise Exception(f"PDF to JSON conversion failed: {e2}")
                
                return json_content

            # Process PDF safely
            json_content = self._process_pdf_safely(pdf_path, _convert_json)
            
            # Save JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_content, f, indent=2, ensure_ascii=False, default=str)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"✅ JSON conversion successful: {len(str(json_content))} characters in {processing_time:.2f}s")
            
            return ConversionResult(
                success=True,
                json_content=json_content,
                processing_time=processing_time,
                metadata={
                    "input_file": pdf_path,
                    "output_file": str(output_path),
                    "file_size": len(json.dumps(json_content, default=str).encode('utf-8')),
                    "skip_tables": self.skip_tables,
                    "conversion_method": "marker_with_fallback"
                }
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            return ConversionResult(
                success=False,
                error_message=str(e),
                processing_time=processing_time
            )
    
    def convert_pdf_to_both(
        self, 
        pdf_path: str, 
        base_filename: Optional[str] = None
    ) -> ConversionResult:
        """
        Convert PDF to both Markdown and JSON formats with safe filename handling.
        
        Args:
            pdf_path: Path to the PDF file
            base_filename: Optional base filename for outputs
            
        Returns:
            ConversionResult with both formats
        """
        # Convert to Markdown
        markdown_result = self.convert_pdf_to_markdown(pdf_path, base_filename)
        
        # Convert to JSON
        json_result = self.convert_pdf_to_json(pdf_path, base_filename)
        
        # Combine results
        if markdown_result.success and json_result.success:
            return ConversionResult(
                success=True,
                markdown_content=markdown_result.markdown_content,
                json_content=json_result.json_content,
                processing_time=markdown_result.processing_time + json_result.processing_time,
                metadata={
                    "markdown": markdown_result.metadata,
                    "json": json_result.metadata,
                    "skip_tables": self.skip_tables,
                    "conversion_method": "marker_both_formats"
                }
            )
        else:
            # Return the first successful result, or the one with error
            if markdown_result.success:
                return markdown_result
            elif json_result.success:
                return json_result
            else:
                return ConversionResult(
                    success=False,
                    error_message=f"Both conversions failed. Markdown: {markdown_result.error_message}, JSON: {json_result.error_message}",
                    processing_time=(markdown_result.processing_time or 0) + (json_result.processing_time or 0)
                )
    
    def get_conversion_stats(self) -> Dict[str, Any]:
        """Get statistics about converted documents."""
        markdown_dir = self.output_dir / "markdown"
        json_dir = self.output_dir / "json"
        
        markdown_files = [f.name for f in markdown_dir.glob("*.md")] if markdown_dir.exists() else []
        json_files = [f.name for f in json_dir.glob("*.json")] if json_dir.exists() else []
        
        return {
            "total_markdown_files": len(markdown_files),
            "total_json_files": len(json_files),
            "markdown_files": markdown_files,
            "json_files": json_files,
            "output_directory": str(self.output_dir),
            "skip_tables": self.skip_tables,
            "marker_initialized": self.marker_initialized,
            "filename_mapping": self.file_handler.get_filename_mapping()
        }
    
    def cleanup(self):
        """Clean up temporary files and resources."""
        self.file_handler.cleanup_temp_files()
