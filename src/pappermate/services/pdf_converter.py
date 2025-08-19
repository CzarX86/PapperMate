"""
PDF Converter Service for PapperMate

Service for converting PDFs to Markdown and JSON using Marker PDF.
"""

import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

import marker
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
    
    def __init__(self, output_dir: str = "converted_documents"):
        """
        Initialize the PDF converter service.
        
        Args:
            output_dir: Directory to store converted documents
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Ensure subdirectories exist
        (self.output_dir / "markdown").mkdir(exist_ok=True)
        (self.output_dir / "json").mkdir(exist_ok=True)
    
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
                return ConversionResult(
                    success=False,
                    error_message=f"PDF file not found: {pdf_path}"
                )
            
            # Generate output filename if not provided
            if not output_filename:
                base_name = Path(pdf_path).stem
                output_filename = f"{base_name}_{uuid.uuid4().hex[:8]}.md"
            
            output_path = self.output_dir / "markdown" / output_filename
            
            # Convert using Marker
            markdown_content = marker.convert_pdf_to_markdown(pdf_path)
            
            # Save markdown file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ConversionResult(
                success=True,
                markdown_content=markdown_content,
                processing_time=processing_time,
                metadata={
                    "input_file": pdf_path,
                    "output_file": str(output_path),
                    "file_size": len(markdown_content.encode('utf-8'))
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
                return ConversionResult(
                    success=False,
                    error_message=f"PDF file not found: {pdf_path}"
                )
            
            # Generate output filename if not provided
            if not output_filename:
                base_name = Path(pdf_path).stem
                output_filename = f"{base_name}_{uuid.uuid4().hex[:8]}.json"
            
            output_path = self.output_dir / "json" / output_filename
            
            # Convert using Marker
            json_content = marker.convert_pdf_to_json(pdf_path)
            
            # Save JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(json_content, f, indent=2, ensure_ascii=False)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ConversionResult(
                success=True,
                json_content=json_content,
                processing_time=processing_time,
                metadata={
                    "input_file": pdf_path,
                    "output_file": str(output_path),
                    "file_size": len(json.dumps(json_content).encode('utf-8'))
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
                    "json": json_result.metadata
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
                    error_message=f"Both conversions failed. Markdown: {markdown_result.error_message}, JSON: {json_result.error_message}"
                )
    
    def get_conversion_stats(self) -> Dict[str, Any]:
        """Get statistics about conversions."""
        markdown_files = list((self.output_dir / "markdown").glob("*.md"))
        json_files = list((self.output_dir / "json").glob("*.json"))
        
        return {
            "total_markdown_files": len(markdown_files),
            "total_json_files": len(json_files),
            "markdown_files": [f.name for f in markdown_files],
            "json_files": [f.name for f in json_files],
            "output_directory": str(self.output_dir)
        }
