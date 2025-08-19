"""
Contract Analyzer Service
Analyzes PDF contracts to detect patterns and extract structured information
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import openai
from dataclasses import dataclass

from ..models.document import Document
from ..services.marker_wrapper import MarkerWrapper
from ..services.pdf_converter import PDFConverter

logger = logging.getLogger(__name__)

@dataclass
class ContractPattern:
    """Represents a detected contract pattern"""
    pattern_type: str  # e.g., "contract_id", "contract_name", "parent_child_relationship"
    confidence: float
    value: str
    context: str
    location: Dict[str, Any]  # page, coordinates, etc.

@dataclass
class ContractAnalysis:
    """Complete analysis of a contract"""
    contract_id: Optional[str] = None
    contract_name: Optional[str] = None
    parent_contracts: List[str] = None
    child_contracts: List[str] = None
    contract_type: Optional[str] = None
    parties: List[str] = None
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    patterns: List[ContractPattern] = None
    raw_text: Optional[str] = None
    
    def __post_init__(self):
        if self.parent_contracts is None:
            self.parent_contracts = []
        if self.child_contracts is None:
            self.child_contracts = []
        if self.parties is None:
            self.parties = []
        if self.patterns is None:
            self.patterns = []

class ContractAnalyzer:
    """
    Analyzes contracts using OpenAI API and local processing
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize the contract analyzer
        
        Args:
            openai_api_key: OpenAI API key (optional)
            model: OpenAI model to use
        """
        self.openai_client = None
        self.model = model
        self.marker_wrapper = MarkerWrapper()
        self.pdf_converter = PDFConverter()
        
        if openai_api_key:
            openai.api_key = openai_api_key
            self.openai_client = openai.OpenAI(api_key=openai_api_key)
            logger.info("OpenAI client initialized")
        else:
            logger.warning("No OpenAI API key provided - will use local processing only")
    
    def analyze_contract(self, pdf_path: str) -> ContractAnalysis:
        """
        Analyze a contract PDF and extract patterns
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ContractAnalysis object with extracted information
        """
        logger.info(f"Analyzing contract: {pdf_path}")
        
        # Step 1: Extract text using existing infrastructure
        extracted_text = self._extract_text_from_pdf(pdf_path)
        
        # Step 2: Analyze with OpenAI if available
        if self.openai_client:
            analysis = self._analyze_with_openai(extracted_text, pdf_path)
        else:
            analysis = self._analyze_locally(extracted_text, pdf_path)
        
        # Step 3: Post-process and validate
        analysis = self._post_process_analysis(analysis, extracted_text)
        
        logger.info(f"Analysis complete for {pdf_path}")
        return analysis
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using existing infrastructure"""
        try:
            # Use your existing PDF converter
            document = self.pdf_converter.convert_pdf(pdf_path)
            return document.get_text_content()
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            # Fallback to marker wrapper
            try:
                result = self.marker_wrapper.extract_text(pdf_path)
                return result.get("text", "")
            except Exception as e2:
                logger.error(f"Fallback extraction also failed: {e2}")
                return ""
    
    def _analyze_with_openai(self, text: str, pdf_path: str) -> ContractAnalysis:
        """Analyze contract text using OpenAI API"""
        try:
            prompt = self._build_analysis_prompt(text)
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a contract analysis expert. Extract structured information from contract text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=2000
            )
            
            # Parse OpenAI response
            content = response.choices[0].message.content
            return self._parse_openai_response(content, text)
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return self._analyze_locally(text, pdf_path)
    
    def _build_analysis_prompt(self, text: str) -> str:
        """Build the prompt for OpenAI analysis"""
        return f"""
        Analyze the following contract text and extract structured information in JSON format.
        
        Look for:
        1. Contract ID (any unique identifier)
        2. Contract Name/Title
        3. Parent contracts (references to other contracts)
        4. Child contracts (contracts that reference this one)
        5. Contract type (e.g., "Service Agreement", "NDA", "License")
        6. Parties involved
        7. Effective date
        8. Expiration date
        
        Return ONLY valid JSON with this structure:
        {{
            "contract_id": "string or null",
            "contract_name": "string or null",
            "parent_contracts": ["list of contract IDs"],
            "child_contracts": ["list of contract IDs"],
            "contract_type": "string or null",
            "parties": ["list of party names"],
            "effective_date": "string or null",
            "expiration_date": "string or null"
        }}
        
        Contract text:
        {text[:4000]}  # Limit text length for API efficiency
        """
    
    def _parse_openai_response(self, response: str, original_text: str) -> ContractAnalysis:
        """Parse OpenAI API response into ContractAnalysis object"""
        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()
            
            data = json.loads(json_str)
            
            # Create ContractAnalysis object
            analysis = ContractAnalysis(
                contract_id=data.get("contract_id"),
                contract_name=data.get("contract_name"),
                parent_contracts=data.get("parent_contracts", []),
                child_contracts=data.get("child_contracts", []),
                contract_type=data.get("contract_type"),
                parties=data.get("parties", []),
                effective_date=data.get("effective_date"),
                expiration_date=data.get("expiration_date"),
                raw_text=original_text
            )
            
            return analysis
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            # Fallback to local analysis
            return self._analyze_locally(original_text, "")
    
    def _analyze_locally(self, text: str, pdf_path: str) -> ContractAnalysis:
        """Fallback local analysis using regex and heuristics"""
        logger.info("Using local analysis fallback")
        
        analysis = ContractAnalysis(raw_text=text)
        
        # Basic pattern matching (you can enhance this)
        import re
        
        # Look for common contract ID patterns
        contract_id_patterns = [
            r'Contract\s+(?:No\.?|Number|#)\s*[:.]?\s*([A-Z0-9\-_]+)',
            r'Agreement\s+(?:No\.?|Number|#)\s*[:.]?\s*([A-Z0-9\-_]+)',
            r'([A-Z]{2,3}-\d{4}-\d{3,4})',  # Common format: XX-YYYY-ZZZ
        ]
        
        for pattern in contract_id_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                analysis.contract_id = match.group(1)
                break
        
        # Look for contract name/title
        title_patterns = [
            r'(?:This\s+)?(?:Agreement|Contract)\s+(?:is\s+)?(?:entered\s+into|made)\s+(?:by\s+and\s+between|between)\s+(.+?)(?:\s+and\s+|\.)',
            r'Title[:\s]+(.+?)(?:\n|\.)',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                analysis.contract_name = match.group(1).strip()
                break
        
        return analysis
    
    def _post_process_analysis(self, analysis: ContractAnalysis, text: str) -> ContractAnalysis:
        """Post-process and validate the analysis"""
        # Add confidence scores to patterns
        for pattern in analysis.patterns:
            if pattern.confidence is None:
                pattern.confidence = 0.8  # Default confidence
        
        # Validate contract ID format
        if analysis.contract_id:
            # Remove common prefixes/suffixes
            analysis.contract_id = analysis.contract_id.strip().strip('.').strip()
        
        # Clean up contract name
        if analysis.contract_name:
            analysis.contract_name = analysis.contract_name.strip()
            if len(analysis.contract_name) > 200:  # Truncate if too long
                analysis.contract_name = analysis.contract_name[:200] + "..."
        
        return analysis
    
    def batch_analyze(self, pdf_paths: List[str]) -> List[ContractAnalysis]:
        """Analyze multiple contracts in batch"""
        results = []
        for pdf_path in pdf_paths:
            try:
                analysis = self.analyze_contract(pdf_path)
                results.append(analysis)
            except Exception as e:
                logger.error(f"Failed to analyze {pdf_path}: {e}")
                # Add empty analysis for failed files
                results.append(ContractAnalysis())
        
        return results
    
    def export_analysis(self, analysis: ContractAnalysis, output_path: str):
        """Export analysis results to JSON"""
        output_data = {
            "contract_id": analysis.contract_id,
            "contract_name": analysis.contract_name,
            "parent_contracts": analysis.parent_contracts,
            "child_contracts": analysis.child_contracts,
            "contract_type": analysis.contract_type,
            "parties": analysis.parties,
            "effective_date": analysis.effective_date,
            "expiration_date": analysis.expiration_date,
            "patterns": [
                {
                    "pattern_type": p.pattern_type,
                    "confidence": p.confidence,
                    "value": p.value,
                    "context": p.context,
                    "location": p.location
                }
                for p in analysis.patterns
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analysis exported to {output_path}")
