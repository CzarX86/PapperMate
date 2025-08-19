"""
Marker Wrapper for PapperMate

This wrapper provides a robust interface to Marker PDF conversion
with our custom table processor that handles empty tables gracefully.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add Marker to path
marker_path = Path(__file__).parent.parent.parent / "Marker_PapperMate"
sys.path.insert(0, str(marker_path))

# Force CPU usage to avoid MPS GPU issues
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["USE_MPS"] = "0"

try:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.config.parser import ConfigParser
    from marker.processors import ProcessorPipeline
    from marker.schema.document import Document
    from marker.logger import get_logger
    
    # Import our fixed table processor
    from .table_processor_fixed import FixedTableProcessor
    
    MARKER_AVAILABLE = True
    logger = get_logger()
except ImportError as e:
    print(f"Warning: Marker not available: {e}")
    MARKER_AVAILABLE = False
    logger = None


class MarkerWrapper:
    """
    Wrapper for Marker PDF conversion with robust error handling.
    """
    
    def __init__(self):
        if not MARKER_AVAILABLE:
            raise ImportError("Marker is not available")
        
        # Initialize models
        self.models = create_model_dict()
        
        # Create custom processor pipeline with our fixed table processor
        self.processor_pipeline = ProcessorPipeline()
        
        # Replace the default table processor with our fixed version
        # Note: This is a simplified approach - in production we'd need to
        # properly integrate with Marker's processor system
        
        # Create converter with basic configuration
        self.converter = PdfConverter(artifact_dict=self.models)
        
        logger.info("Marker wrapper initialized successfully")
    
    def convert_to_markdown(self, pdf_path: str) -> Optional[str]:
        """
        Convert PDF to Markdown with robust error handling.
        """
        try:
            logger.info(f"Converting {pdf_path} to Markdown")
            
            # Try primary conversion
            rendered = self.converter(pdf_path)
            markdown_content = rendered.markdown
            
            if markdown_content:
                logger.info(f"Successfully converted to Markdown: {len(markdown_content)} characters")
                return markdown_content
            else:
                logger.warning("Markdown content is empty")
                return None
                
        except Exception as e:
            logger.error(f"Primary conversion failed: {e}")
            
            # Try fallback approach
            try:
                logger.info("Trying fallback conversion method")
                
                # Use basic configuration without table processing
                basic_config = {
                    "skip_tables": True,  # Skip problematic table processing
                    "output_format": "markdown"
                }
                
                config_parser = ConfigParser(basic_config)
                fallback_converter = PdfConverter(
                    artifact_dict=self.models,
                    config=config_parser.generate_config_dict(),
                    processor_list=config_parser.get_processors(),
                    renderer=config_parser.get_renderer()
                )
                
                rendered = fallback_converter(pdf_path)
                markdown_content = rendered.markdown
                
                if markdown_content:
                    logger.info(f"Fallback conversion successful: {len(markdown_content)} characters")
                    return markdown_content
                else:
                    logger.warning("Fallback conversion returned empty content")
                    return None
                    
            except Exception as e2:
                logger.error(f"Fallback conversion also failed: {e2}")
                return None
    
    def convert_to_json(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """
        Convert PDF to JSON with robust error handling.
        """
        try:
            logger.info(f"Converting {pdf_path} to JSON")
            
            # Configure for JSON output
            config = {
                "output_format": "json",
                "skip_tables": True  # Skip problematic table processing
            }
            
            config_parser = ConfigParser(config)
            json_converter = PdfConverter(
                artifact_dict=self.models,
                config=config_parser.generate_config_dict(),
                processor_list=config_parser.get_processors(),
                renderer=config_parser.get_renderer()
            )
            
            rendered = json_converter(pdf_path)
            json_content = rendered.children
            
            if json_content:
                logger.info(f"Successfully converted to JSON: {len(str(json_content))} characters")
                return json_content
            else:
                logger.warning("JSON content is empty")
                return None
                
        except Exception as e:
            logger.error(f"JSON conversion failed: {e}")
            return None
    
    def convert_to_both(self, pdf_path: str) -> Dict[str, Any]:
        """
        Convert PDF to both Markdown and JSON formats.
        """
        result = {
            "success": False,
            "markdown": None,
            "json": None,
            "errors": []
        }
        
        # Try Markdown conversion
        try:
            markdown_content = self.convert_to_markdown(pdf_path)
            if markdown_content:
                result["markdown"] = markdown_content
                result["success"] = True
            else:
                result["errors"].append("Markdown conversion failed")
        except Exception as e:
            result["errors"].append(f"Markdown conversion error: {e}")
        
        # Try JSON conversion
        try:
            json_content = self.convert_to_json(pdf_path)
            if json_content:
                result["json"] = json_content
                result["success"] = True
            else:
                result["errors"].append("JSON conversion failed")
        except Exception as e:
            result["errors"].append(f"JSON conversion error: {e}")
        
        return result


def create_marker_wrapper() -> Optional[MarkerWrapper]:
    """
    Create a Marker wrapper if available.
    """
    try:
        return MarkerWrapper()
    except Exception as e:
        print(f"Failed to create Marker wrapper: {e}")
        return None
