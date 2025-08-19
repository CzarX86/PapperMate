"""
Contract Parser Service for PapperMate

Service for parsing contracts from Marker-generated Markdown and JSON files,
extracting metadata, sections, and entities.
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from dateutil import parser as date_parser
import logging

from ..models.document import Contract, ContractType, Document, DocumentType, DocumentStatus

# Configure logging
logger = logging.getLogger(__name__)


class ContractParser:
    """Parser for extracting contract information from Marker outputs."""
    
    def __init__(self):
        # Regex patterns for common contract elements
        self.patterns = {
            'contract_number': r'(?i)(?:contrato|contract|número|number|ref|reference)[\s:]*([A-Z0-9\-_/]+)',
            'currency': r'(?i)(R\$|US\$|USD|BRL|EUR|€|£)',
            'amount': r'(?i)(?:valor|value|amount|total)[\s:]*([R$US$USD€£]?\s*[\d,]+\.?\d*)',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'cnpj_cpf': r'(?:\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{3}\.\d{3}\.\d{3}-\d{2})',
            'date_formats': [
                r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY
                r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
                r'(\d{1,2})\s+(?:de\s+)?(?:jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)[a-z]*\s+(\d{4})',  # DD Month YYYY
            ]
        }
        
        # Common contract section headers
        self.section_headers = [
            'vigência', 'duração', 'termo', 'prazo', 'expiração',
            'rescisão', 'terminação', 'cancelamento',
            'confidencialidade', 'sigilo', 'não divulgação',
            'pagamentos', 'pagamento', 'valor', 'preço', 'compensação',
            'obrigações', 'responsabilidades', 'deveres',
            'foro', 'jurisdição', 'lei aplicável', 'disputas'
        ]
    
    def parse_from_markdown(self, markdown_path: str) -> Contract:
        """Parse contract from Marker-generated Markdown file."""
        logger.info(f"Parsing contract from Markdown: {markdown_path}")
        
        try:
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata
            metadata = self._extract_metadata_from_markdown(content)
            
            # Extract sections
            sections = self._extract_sections_from_markdown(content)
            
            # Extract entities
            entities = self._extract_entities_from_markdown(content)
            
            # Create document model
            document = self._create_document_model(markdown_path, content)
            
            # Create contract model
            contract = self._create_contract_model(document, metadata, sections, entities)
            
            logger.info(f"Successfully parsed contract: {contract.contract_name}")
            return contract
            
        except Exception as e:
            logger.error(f"Error parsing Markdown file {markdown_path}: {e}")
            raise
    
    def parse_from_json(self, json_path: str) -> Contract:
        """Parse contract from Marker-generated JSON file."""
        logger.info(f"Parsing contract from JSON: {json_path}")
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract metadata
            metadata = self._extract_metadata_from_json(data)
            
            # Extract sections
            sections = self._extract_sections_from_json(data)
            
            # Extract entities
            entities = self._extract_entities_from_json(data)
            
            # Create document model
            document = self._create_document_model(json_path, str(data))
            
            # Create contract model
            contract = self._create_contract_model(document, metadata, sections, entities)
            
            logger.info(f"Successfully parsed contract: {contract.contract_name}")
            return contract
            
        except Exception as e:
            logger.error(f"Error parsing JSON file {json_path}: {e}")
            raise
    
    def _extract_metadata_from_markdown(self, content: str) -> Dict[str, Any]:
        """Extract metadata from Markdown content."""
        metadata = {}
        
        # Extract title (first H1 or H2)
        title_match = re.search(r'^#{1,2}\s+(.+)$', content, re.MULTILINE)
        if title_match:
            metadata['title'] = title_match.group(1).strip()
        
        # Extract contract number - look for patterns like "Contract Number: MSA-2024-001"
        contract_num_pattern = r'(?i)(?:contract\s+number|número\s+do\s+contrato|ref|reference)[\s:]*([A-Z0-9\-_/]+)'
        contract_num_match = re.search(contract_num_pattern, content)
        if contract_num_match:
            metadata['contract_number'] = contract_num_match.group(1).strip()
        
        # Also look for patterns like "**Contract Number:** MSA-2024-001" (Markdown bold)
        if not metadata.get('contract_number'):
            bold_contract_pattern = r'\*\*Contract Number:\*\*\s*([A-Z0-9\-_/]+)'
            bold_match = re.search(bold_contract_pattern, content)
            if bold_match:
                metadata['contract_number'] = bold_match.group(1).strip()
        
        # Extract currency and amount
        currency_match = re.search(self.patterns['currency'], content)
        if currency_match:
            metadata['currency'] = currency_match.group(1)
            
            # Look for amount near currency - improved pattern
            amount_pattern = r'(?i)(?:valor|value|amount|total)[\s:]*([R$US$USD€£]?\s*[\d,]+\.?\d*)'
            amount_match = re.search(amount_pattern, content)
            if amount_match:
                metadata['total_value'] = self._parse_amount(amount_match.group(1))
        
        # Also look for bold patterns like "**Total Value:** R$ 150.000,00"
        if not metadata.get('total_value'):
            bold_amount_pattern = r'\*\*Total Value:\*\*\s*([R$US$USD€£]?\s*[\d,]+\.?\d*)'
            bold_amount_match = re.search(bold_amount_pattern, content)
            if bold_amount_match:
                metadata['total_value'] = self._parse_amount(bold_amount_match.group(1))
        
        # Extract dates
        dates = self._extract_dates(content)
        if dates:
            metadata['dates'] = dates
        
        # Also look for bold patterns like "**Effective Date:** 01/01/2024"
        if not metadata.get('dates'):
            bold_effective_pattern = r'\*\*Effective Date:\*\*\s*(\d{1,2}/\d{1,2}/\d{4})'
            bold_effective_match = re.search(bold_effective_pattern, content)
            if bold_effective_match:
                effective_date = self._extract_dates(bold_effective_match.group(0))
                if effective_date:
                    metadata['dates'] = effective_date
            
            bold_expiration_pattern = r'\*\*Expiration Date:\*\*\s*(\d{1,2}/\d{1,2}/\d{4})'
            bold_expiration_match = re.search(bold_expiration_pattern, content)
            if bold_expiration_match and metadata.get('dates'):
                expiration_date = self._extract_dates(bold_expiration_match.group(0))
                if expiration_date:
                    metadata['dates'].extend(expiration_date)
        
        # Extract parties (client/vendor)
        parties = self._extract_parties(content)
        if parties:
            metadata.update(parties)
        
        # Also look for bold patterns like "**Client:** TechCorp Inc."
        if not metadata.get('client_name'):
            bold_client_pattern = r'\*\*Client:\*\*\s*([A-Z][A-Za-z\s&\.]+)'
            bold_client_match = re.search(bold_client_pattern, content)
            if bold_client_match:
                metadata['client_name'] = bold_client_match.group(1).strip()
        
        if not metadata.get('vendor_name'):
            bold_vendor_pattern = r'\*\*Vendor:\*\*\s*([A-Z][A-Za-z\s&\.]+)'
            bold_vendor_match = re.search(bold_vendor_pattern, content)
            if bold_vendor_match:
                metadata['vendor_name'] = bold_vendor_match.group(1).strip()
        
        # Extract contract type
        contract_type = self._detect_contract_type(content)
        if contract_type:
            metadata['contract_type'] = contract_type
        
        return metadata
    
    def _extract_metadata_from_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from JSON data structure."""
        metadata = {}
        
        # Extract from blocks if available
        if 'blocks' in data:
            for block in data['blocks']:
                if block.get('type') == 'heading':
                    if not metadata.get('title'):
                        metadata['title'] = block.get('text', '').strip()
                elif block.get('type') == 'paragraph':
                    text = block.get('text', '')
                    # Extract contract number
                    if not metadata.get('contract_number'):
                        contract_num_pattern = r'(?i)(?:contract\s+number|número\s+do\s+contrato|ref|reference)[\s:]*([A-Z0-9\-_/]+)'
                        contract_num_match = re.search(contract_num_pattern, text)
                        if contract_num_match:
                            metadata['contract_number'] = contract_num_match.group(1).strip()
                    
                    # Extract currency and amount
                    if not metadata.get('currency'):
                        currency_match = re.search(self.patterns['currency'], text)
                        if currency_match:
                            metadata['currency'] = currency_match.group(1)
                    
                    # Extract dates
                    if not metadata.get('dates'):
                        dates = self._extract_dates(text)
                        if dates:
                            metadata['dates'] = dates
                    
                    # Extract parties
                    if not metadata.get('client_name') or not metadata.get('vendor_name'):
                        parties = self._extract_parties(text)
                        if parties:
                            metadata.update(parties)
        
        # Extract contract type
        if not metadata.get('contract_type'):
            contract_type = self._detect_contract_type(str(data))
            if contract_type:
                metadata['contract_type'] = contract_type
        
        return metadata
    
    def _extract_sections_from_markdown(self, content: str) -> Dict[str, str]:
        """Extract contract sections from Markdown content."""
        sections = {}
        
        # Split content by headers
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            # Check if line is a header
            header_match = re.match(r'^#{1,2,3}\s+(.+)$', line)
            if header_match:
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = header_match.group(1).lower()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        # If no sections were found, try to extract from bold patterns
        if not sections:
            # Look for sections with bold headers
            bold_section_pattern = r'\*\*([^*]+):\*\*([^*\n]*)'
            bold_matches = re.finditer(bold_section_pattern, content)
            
            for match in bold_matches:
                section_name = match.group(1).lower()
                section_content = match.group(2).strip()
                if section_content:
                    sections[section_name] = section_content
        
        return sections
    
    def _extract_sections_from_json(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Extract contract sections from JSON data structure."""
        sections = {}
        
        if 'blocks' in data:
            current_section = None
            current_content = []
            
            for block in data['blocks']:
                if block.get('type') == 'heading':
                    # Save previous section
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    
                    # Start new section
                    current_section = block.get('text', '').lower()
                    current_content = []
                elif block.get('type') == 'paragraph' and current_section:
                    current_content.append(block.get('text', ''))
            
            # Save last section
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _extract_entities_from_markdown(self, content: str) -> Dict[str, Any]:
        """Extract entities from Markdown content."""
        entities = {}
        
        # Extract emails
        emails = re.findall(self.patterns['email'], content)
        if emails:
            entities['emails'] = list(set(emails))
        
        # Extract CNPJ/CPF
        cnpj_cpf = re.findall(self.patterns['cnpj_cpf'], content)
        if cnpj_cpf:
            entities['cnpj_cpf'] = list(set(cnpj_cpf))
        
        # Extract tables (basic detection)
        table_lines = re.findall(r'^\|.*\|$', content, re.MULTILINE)
        if table_lines:
            entities['tables'] = {
                'count': len(table_lines),
                'has_headers': any('---' in line for line in table_lines)
            }
        
        # Extract key clauses
        key_clauses = {}
        for header in self.section_headers:
            if header.lower() in content.lower():
                key_clauses[header] = True
        
        if key_clauses:
            entities['key_clauses'] = key_clauses
        
        return entities
    
    def _extract_entities_from_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entities from JSON data structure."""
        entities = {}
        
        if 'blocks' in data:
            content = ' '.join([block.get('text', '') for block in data['blocks'] if block.get('text')])
            
            # Extract emails
            emails = re.findall(self.patterns['email'], content)
            if emails:
                entities['emails'] = list(set(emails))
            
            # Extract CNPJ/CPF
            cnpj_cpf = re.findall(self.patterns['cnpj_cpf'], content)
            if cnpj_cpf:
                entities['cnpj_cpf'] = list(set(cnpj_cpf))
            
            # Extract tables
            table_blocks = [block for block in data['blocks'] if block.get('type') == 'table']
            if table_blocks:
                entities['tables'] = {
                    'count': len(table_blocks),
                    'has_content': any(block.get('text') for block in table_blocks)
                }
            
            # Extract key clauses
            key_clauses = {}
            for header in self.section_headers:
                if header.lower() in content.lower():
                    key_clauses[header] = True
            
            if key_clauses:
                entities['key_clauses'] = key_clauses
        
        return entities
    
    def _extract_dates(self, content: str) -> List[Dict[str, Any]]:
        """Extract dates from content using multiple patterns."""
        dates = []
        
        for pattern in self.patterns['date_formats']:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    if len(match.groups()) == 3:
                        if '/' in pattern:
                            # DD/MM/YYYY format
                            day, month, year = match.groups()
                            date_obj = datetime(int(year), int(month), int(day))
                        elif '-' in pattern:
                            # YYYY-MM-DD format
                            year, month, day = match.groups()
                            date_obj = datetime(int(year), int(month), int(day))
                        else:
                            # Month format
                            day, month, year = match.groups()
                            month_map = {
                                'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4,
                                'mai': 5, 'jun': 6, 'jul': 7, 'ago': 8,
                                'set': 9, 'out': 10, 'nov': 11, 'dez': 12
                            }
                            month_num = month_map.get(month.lower()[:3], 1)
                            date_obj = datetime(int(year), month_num, int(day))
                        
                        dates.append({
                            'date': date_obj,
                            'text': match.group(0),
                            'position': match.start()
                        })
                except (ValueError, TypeError):
                    continue
        
        # Sort by position in text
        dates.sort(key=lambda x: x['position'])
        return dates
    
    def _extract_parties(self, content: str) -> Dict[str, str]:
        """Extract client and vendor names from content."""
        parties = {}
        
        # Look for common patterns - improved regex
        client_patterns = [
            r'(?i)(?:cliente|client|contratante|buyer)[\s:]*([A-Z][A-Za-z\s&\.]+?)(?=\s+(?:vendor|fornecedor|contratado|seller|supplier|prestador|provider|contractor)|$)',
            r'(?i)(?:empresa|company|corporation)[\s:]*([A-Z][A-Za-z\s&\.]+?)(?=\s+(?:vendor|fornecedor|contratado|seller|supplier|prestador|provider|contractor)|$)'
        ]
        
        vendor_patterns = [
            r'(?i)(?:fornecedor|vendor|contratado|seller|supplier)[\s:]*([A-Z][A-Za-z\s&\.]+?)(?=\s+(?:cliente|client|contratante|buyer|empresa|company|corporation)|$)',
            r'(?i)(?:prestador|provider|contractor)[\s:]*([A-Z][A-Za-z\s&\.]+?)(?=\s+(?:cliente|client|contratante|buyer|empresa|company|corporation)|$)'
        ]
        
        # Extract client
        for pattern in client_patterns:
            match = re.search(pattern, content)
            if match:
                parties['client_name'] = match.group(1).strip()
                break
        
        # Extract vendor
        for pattern in vendor_patterns:
            match = re.search(pattern, content)
            if match:
                parties['vendor_name'] = match.group(1).strip()
                break
        
        return parties
    
    def _detect_contract_type(self, content: str) -> Optional[ContractType]:
        """Detect contract type from content."""
        content_lower = content.lower()
        
        if any(term in content_lower for term in ['master service agreement', 'msa', 'acordo quadro']):
            return ContractType.MSA
        elif any(term in content_lower for term in ['local service agreement', 'lsa', 'acordo local']):
            return ContractType.LSA
        elif any(term in content_lower for term in ['statement of work', 'sow', 'escopo de trabalho']):
            return ContractType.SOW
        elif any(term in content_lower for term in ['project work order', 'pwo', 'ordem de serviço']):
            return ContractType.PWO
        elif any(term in content_lower for term in ['change request', 'cr', 'solicitação de mudança']):
            return ContractType.CR
        elif any(term in content_lower for term in ['change notification form', 'cnf', 'formulário de notificação']):
            return ContractType.CNF
        
        return None
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float."""
        try:
            # Remove currency symbols and spaces
            clean_amount = re.sub(r'[R$US$USD€£\s]', '', amount_str)
            
            # Handle Brazilian format: 150.000,00 -> 150000.00
            if ',' in clean_amount and '.' in clean_amount:
                # Brazilian format: dots for thousands, comma for decimal
                clean_amount = clean_amount.replace('.', '').replace(',', '.')
            elif ',' in clean_amount:
                # European format: comma for decimal
                clean_amount = clean_amount.replace(',', '.')
            
            return float(clean_amount)
        except (ValueError, TypeError):
            return None
    
    def _create_document_model(self, file_path: str, content: str) -> Document:
        """Create Document model from file."""
        path = Path(file_path)
        
        return Document(
            id=str(hash(file_path)),
            filename=path.name,
            file_path=str(path),
            document_type=DocumentType.MARKDOWN if path.suffix == '.md' else DocumentType.JSON,
            mime_type='text/markdown' if path.suffix == '.md' else 'application/json',
            file_size=len(content.encode('utf-8')),
            status=DocumentStatus.CONVERTED,
            content=content[:1000],  # First 1000 chars
            metadata={'source': 'marker', 'parser': 'contract_parser'}
        )
    
    def _create_contract_model(self, document: Document, metadata: Dict[str, Any], 
                              sections: Dict[str, str], entities: Dict[str, Any]) -> Contract:
        """Create Contract model from parsed data."""
        
        # Determine contract type
        contract_type = metadata.get('contract_type', ContractType.MSA)
        
        # Extract dates
        dates = metadata.get('dates', [])
        effective_date = None
        expiration_date = None
        
        if dates:
            if len(dates) >= 1:
                effective_date = dates[0]['date']
            if len(dates) >= 2:
                expiration_date = dates[1]['date']
        
        # Create contract
        contract = Contract(
            document=document,
            contract_type=contract_type,
            contract_number=metadata.get('contract_number', 'N/A'),
            contract_name=metadata.get('title', document.filename),
            client_name=metadata.get('client_name', 'N/A'),
            vendor_name=metadata.get('vendor_name', 'N/A'),
            effective_date=effective_date,
            expiration_date=expiration_date,
            total_value=metadata.get('total_value'),
            currency=metadata.get('currency', 'USD'),
            entities={
                'sections': sections,
                'extracted_entities': entities,
                'parsing_metadata': {
                    'parser_version': '1.0',
                    'extraction_date': datetime.now(timezone.utc).isoformat(),
                    'confidence_score': self._calculate_confidence(metadata, sections, entities)
                }
            }
        )
        
        return contract
    
    def _calculate_confidence(self, metadata: Dict[str, Any], sections: Dict[str, str], 
                             entities: Dict[str, Any]) -> float:
        """Calculate confidence score for extraction (0.0 to 1.0)."""
        score = 0.0
        total_checks = 0
        
        # Check metadata completeness
        if metadata.get('title'):
            score += 1.0
        total_checks += 1
        
        if metadata.get('contract_number'):
            score += 1.0
        total_checks += 1
        
        if metadata.get('client_name') and metadata.get('vendor_name'):
            score += 1.0
        total_checks += 1
        
        if metadata.get('dates'):
            score += 1.0
        total_checks += 1
        
        # Check sections
        if sections:
            score += min(len(sections) / 5.0, 1.0)  # Cap at 1.0 for sections
        total_checks += 1
        
        # Check entities
        if entities.get('key_clauses'):
            score += min(len(entities['key_clauses']) / 3.0, 1.0)  # Cap at 1.0 for clauses
        total_checks += 1
        
        return score / total_checks if total_checks > 0 else 0.0
