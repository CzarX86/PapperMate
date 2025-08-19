"""
PDF Converter Service for PapperMate

Service for converting PDFs to Markdown and JSON using Marker PDF.
"""

import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

# Force CPU usage to avoid MPS GPU issues
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["USE_MPS"] = "0"

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
from pydantic import BaseModel

from ..models.document import Document, DocumentType, DocumentStatus


class ConversionResult(BaseModel):
    """Result of PDF conversion."""
    success: bool
    markdown_content: Optional[str] = None
    json_content: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    metadata: Dict[str, Any] = None


class PDFConverterService:
    """Service for converting PDF documents using Marker."""
    
    def __init__(self, output_dir: str = "converted_documents", skip_tables: Optional[bool] = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "markdown").mkdir(exist_ok=True)
        (self.output_dir / "json").mkdir(exist_ok=True)
        
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
        
        # Initialize Marker models once
        try:
            self.models = create_model_dict()
            self.config_parser = ConfigParser({})
            self.converter = PdfConverter(artifact_dict=self.models)
            self.marker_initialized = True
            print("✅ Marker initialized successfully")
        except Exception as e:
            print(f"⚠️ Warning: Marker initialization failed: {e}")
            self.marker_initialized = False
    
    def _get_conversion_config(self, output_format: str = "markdown") -> Dict[str, Any]:
        """
        Get conversion configuration with skip_tables support.
        """
        config = {
            "output_format": output_format,
        }
        
        # If skip_tables is enabled, add configuration to skip table processing
        if self.skip_tables:
            config.update({
                "skip_tables": True,
                "disable_table_processing": True,
                "table_processor": "none"
            })
            print(f"🔧 Skipping table processing for {output_format} conversion")
        
        return config
    
    def convert_pdf_to_markdown(
        self, 
        pdf_path: str, 
        output_filename: Optional[str] = None
    ) -> ConversionResult:
        """
        Convert PDF to Markdown using Marker.
        
        Args:
            pdf_path: Path to the PDF file
            output_filename: Optional custom output filename
            
        Returns:
            ConversionResult with markdown content
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
            try:
                config = self._get_conversion_config("markdown")
                config_parser = ConfigParser(config)
                
                converter = PdfConverter(
                    artifact_dict=self.models,
                    config=config_parser.generate_config_dict(),
                    processor_list=config_parser.get_processors(),
                    renderer=config_parser.get_renderer()
                )
                
                print(f"🔄 Converting {pdf_path} to Markdown...")
                rendered = converter(pdf_path)
                markdown_content = rendered.markdown
                
            except Exception as e:
                # Fallback: try with basic configuration
                print(f"⚠️ Primary conversion failed, trying fallback: {e}")
                try:
                    basic_converter = PdfConverter(artifact_dict=self.models)
                    rendered = basic_converter(pdf_path)
                    markdown_content = rendered.markdown
                except Exception as e2:
                    processing_time = (datetime.now() - start_time).total_seconds()
                    return ConversionResult(
                        success=False,
                        error_message=f"PDF conversion failed: {e2}",
                        processing_time=processing_time
                    )
            
            # Save markdown file
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
        Convert PDF to JSON using Marker.
        
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
            try:
                config = self._get_conversion_config("json")
                config_parser = ConfigParser(config)
                
                converter = PdfConverter(
                    artifact_dict=self.models,
                    config=config_parser.generate_config_dict(),
                    processor_list=config_parser.get_processors(),
                    renderer=config_parser.get_renderer()
                )
                
                print(f"🔄 Converting {pdf_path} to JSON...")
                rendered = converter(pdf_path)
                json_content = rendered.children
                
            except Exception as e:
                # Fallback: try with basic configuration
                print(f"⚠️ Primary JSON conversion failed, trying fallback: {e}")
                try:
                    basic_converter = PdfConverter(artifact_dict=self.models)
                    rendered = basic_converter(pdf_path)
                    json_content = rendered.children
                except Exception as e2:
                    processing_time = (datetime.now() - start_time).total_seconds()
                    return ConversionResult(
                        success=False,
                        error_message=f"PDF to JSON conversion failed: {e2}",
                        processing_time=processing_time
                    )
            
            # Save JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(json_content, f, indent=2, ensure_ascii=False)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"✅ JSON conversion successful: {len(str(json_content))} characters in {processing_time:.2f}s")
            
            return ConversionResult(
                success=True,
                json_content=json_content,
                processing_time=processing_time,
                metadata={
                    "input_file": pdf_path,
                    "output_file": str(output_path),
                    "file_size": len(json.dumps(json_content).encode('utf-8')),
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
        Convert PDF to both Markdown and JSON formats.
        
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
            "marker_initialized": self.marker_initialized
        }
