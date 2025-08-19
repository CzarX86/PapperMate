"""
Schema Validation Service for PapperMate

Service for generating JSON Schema from Pydantic models and validating contracts.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
import logging

from pydantic import BaseModel, ValidationError
from pydantic.json import pydantic_encoder

from ..models.document import Document, Contract, ContractHierarchy, ContractType, DocumentType, DocumentStatus

# Configure logging
logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validator for contract schemas and data validation."""
    
    def __init__(self):
        # Initialize empty dictionary to store generated schemas
        self.schemas = {}
        # Generate all required schemas during initialization
        self._generate_schemas()
    
    def _generate_schemas(self):
        """Generate JSON Schema for all Pydantic models."""
        try:
            # Generate schemas for each model
            self.schemas['Document'] = Document.model_json_schema()
            self.schemas['Contract'] = Contract.model_json_schema()
            self.schemas['ContractHierarchy'] = ContractHierarchy.model_json_schema()
            
            # Generate combined schema for validation
            self.schemas['ContractValidation'] = {
                "type": "object",
                "properties": {
                    "document": self.schemas['Document'],
                    "contract": self.schemas['Contract']
                },
                "required": ["document", "contract"],
                "additionalProperties": False
            }
            
            logger.info("Successfully generated JSON schemas for all models")
            
        except Exception as e:
            logger.error(f"Error generating schemas: {e}")
            raise
    
    def get_schema(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get JSON Schema for a specific model."""
        return self.schemas.get(model_name)
    
    def get_all_schemas(self) -> Dict[str, Any]:
        """Get all generated JSON schemas."""
        return self.schemas.copy()
    
    def export_schemas(self, output_dir: str = "schemas") -> List[str]:
        """Export all schemas to JSON files."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        exported_files = []
        
        try:
            for schema_name, schema_data in self.schemas.items():
                file_path = output_path / f"{schema_name.lower()}_schema.json"
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(schema_data, f, indent=2, ensure_ascii=False, default=pydantic_encoder)
                
                exported_files.append(str(file_path))
                logger.info(f"Exported schema: {file_path}")
            
            # Export combined validation schema
            validation_schema = {
                "title": "PapperMate Contract Validation Schema",
                "version": "1.0.0",
                "description": "Combined schema for validating contracts and documents",
                "schemas": self.schemas
            }
            
            validation_file = output_path / "validation_schema.json"
            with open(validation_file, 'w', encoding='utf-8') as f:
                json.dump(validation_schema, f, indent=2, ensure_ascii=False, default=pydantic_encoder)
            
            exported_files.append(str(validation_file))
            logger.info(f"Exported validation schema: {validation_file}")
            
        except Exception as e:
            logger.error(f"Error exporting schemas: {e}")
            raise
        
        return exported_files
    
    def validate_contract(self, contract: Contract) -> List[str]:
        """Validate a contract against its schema and return error messages."""
        errors = []
        
        try:
            # Validate the contract model itself
            contract.model_validate(contract.model_dump())
            
            # Additional business logic validations
            business_errors = self._validate_business_rules(contract)
            errors.extend(business_errors)
            
            # Validate document reference
            if contract.document:
                try:
                    contract.document.model_validate(contract.document.model_dump())
                except ValidationError as e:
                    errors.extend([f"Document validation error: {err}" for err in e.errors()])
            
            logger.info(f"Contract validation completed with {len(errors)} errors")
            
        except ValidationError as e:
            errors.extend([f"Contract validation error: {err}" for err in e.errors()])
            logger.error(f"Contract validation failed: {e}")
        
        return errors
    
    def validate_document(self, document: Document) -> List[str]:
        """Validate a document against its schema and return error messages."""
        errors = []
        
        try:
            # Validate the document model itself
            document.model_validate(document.model_dump())
            
            # Additional business logic validations
            business_errors = self._validate_document_rules(document)
            errors.extend(business_errors)
            
            logger.info(f"Document validation completed with {len(errors)} errors")
            
        except ValidationError as e:
            errors.extend([f"Document validation error: {err}" for err in e.errors()])
            logger.error(f"Document validation failed: {e}")
        
        return errors
    
    def validate_contract_hierarchy(self, hierarchy: ContractHierarchy) -> List[str]:
        """Validate a contract hierarchy against its schema and return error messages."""
        errors = []
        
        try:
            # Validate the hierarchy model itself
            hierarchy.model_validate(hierarchy.model_dump())
            
            # Additional business logic validations
            business_errors = self._validate_hierarchy_rules(hierarchy)
            errors.extend(business_errors)
            
            logger.info(f"Contract hierarchy validation completed with {len(errors)} errors")
            
        except ValidationError as e:
            errors.extend([f"Contract hierarchy validation error: {err}" for err in e.errors()])
            logger.error(f"Contract hierarchy validation failed: {e}")
        
        return errors
    
    def _validate_business_rules(self, contract: Contract) -> List[str]:
        """Validate business rules for contracts."""
        errors = []
        
        # Check if contract has required basic information
        if not contract.contract_name or contract.contract_name == 'N/A':
            errors.append("Contract must have a valid name")
        
        if not contract.contract_number or contract.contract_number == 'N/A':
            errors.append("Contract must have a valid contract number")
        
        if not contract.client_name or contract.client_name == 'N/A':
            errors.append("Contract must have a valid client name")
        
        if not contract.vendor_name or contract.vendor_name == 'N/A':
            errors.append("Contract must have a valid vendor name")
        
        # Check date logic
        if contract.effective_date and contract.expiration_date:
            if contract.effective_date >= contract.expiration_date:
                errors.append("Effective date must be before expiration date")
        
        # Check value and currency consistency
        if contract.total_value is not None:
            if contract.total_value <= 0:
                errors.append("Contract total value must be positive")
            
            if not contract.currency:
                errors.append("Contract must have currency when value is specified")
        
        # Check entities structure
        if contract.entities:
            if 'sections' not in contract.entities:
                errors.append("Contract entities must include sections")
            
            if 'extracted_entities' not in contract.entities:
                errors.append("Contract entities must include extracted entities")
            
            if 'parsing_metadata' not in contract.entities:
                errors.append("Contract entities must include parsing metadata")
        
        return errors
    
    def _validate_document_rules(self, document: Document) -> List[str]:
        """Validate business rules for documents."""
        errors = []
        
        # Check if document has required basic information
        if not document.filename:
            errors.append("Document must have a valid filename")
        
        if not document.file_path:
            errors.append("Document must have a valid file path")
        
        if document.file_size <= 0:
            errors.append("Document must have a positive file size")
        
        # Check status transitions
        if document.status == DocumentStatus.ERROR and not document.error_message:
            errors.append("Document with error status must have an error message")
        
        # Check content consistency
        if document.content and len(document.content) > document.file_size:
            errors.append("Document content length cannot exceed file size")
        
        return errors
    
    def _validate_hierarchy_rules(self, hierarchy: ContractHierarchy) -> List[str]:
        """Validate business rules for contract hierarchies."""
        errors = []
        
        # Check if hierarchy has required basic information
        if not hierarchy.name:
            errors.append("Contract hierarchy must have a valid name")
        
        if not hierarchy.root_contract_id:
            errors.append("Contract hierarchy must have a root contract ID")
        
        # Check if root contract exists in contracts list
        if hierarchy.contracts:
            root_contract_ids = [c.document.id for c in hierarchy.contracts]
            if hierarchy.root_contract_id not in root_contract_ids:
                errors.append("Root contract ID must exist in contracts list")
        
        # Check hierarchy validity
        if not hierarchy.is_valid and not hierarchy.validation_errors:
            errors.append("Invalid hierarchy must have validation error messages")
        
        return errors
    
    def validate_json_against_schema(self, json_data: Union[str, Dict[str, Any]], 
                                   schema_name: str = "Contract") -> List[str]:
        """Validate JSON data against a specific schema."""
        errors = []
        
        try:
            # Parse JSON if it's a string
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data
            
            # Get the schema
            schema = self.get_schema(schema_name)
            if not schema:
                errors.append(f"Schema '{schema_name}' not found")
                return errors
            
            # Basic schema validation (this is a simplified version)
            # In production, you might want to use a proper JSON Schema validator like jsonschema
            errors.extend(self._validate_json_structure(data, schema))
            
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON format: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return errors
    
    def _validate_json_structure(self, data: Any, schema: Dict[str, Any]) -> List[str]:
        """Basic JSON structure validation."""
        errors = []
        
        # Check required fields
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in data:
                errors.append(f"Required field '{field}' is missing")
        
        # Check type constraints
        if 'type' in schema:
            expected_type = schema['type']
            if expected_type == 'object' and not isinstance(data, dict):
                errors.append(f"Expected object type, got {type(data).__name__}")
            elif expected_type == 'array' and not isinstance(data, list):
                errors.append(f"Expected array type, got {type(data).__name__}")
            elif expected_type == 'string' and not isinstance(data, str):
                errors.append(f"Expected string type, got {type(data).__name__}")
            elif expected_type == 'integer' and not isinstance(data, int):
                errors.append(f"Expected integer type, got {type(data).__name__}")
            elif expected_type == 'number' and not isinstance(data, (int, float)):
                errors.append(f"Expected number type, got {type(data).__name__}")
            elif expected_type == 'boolean' and not isinstance(data, bool):
                errors.append(f"Expected boolean type, got {type(data).__name__}")
        
        # Check properties if it's an object
        if isinstance(data, dict) and 'properties' in schema:
            for prop_name, prop_schema in schema['properties'].items():
                if prop_name in data:
                    prop_errors = self._validate_json_structure(data[prop_name], prop_schema)
                    errors.extend([f"Property '{prop_name}': {err}" for err in prop_errors])
        
        # Check items if it's an array
        if isinstance(data, list) and 'items' in schema:
            for i, item in enumerate(data):
                item_errors = self._validate_json_structure(item, schema['items'])
                errors.extend([f"Item {i}: {err}" for err in item_errors])
        
        return errors
    
    def get_validation_summary(self, contract: Contract) -> Dict[str, Any]:
        """Get a summary of contract validation results."""
        errors = self.validate_contract(contract)
        
        # Calculate confidence score
        confidence_score = 0.0
        if contract.entities and 'parsing_metadata' in contract.entities:
            confidence_score = contract.entities['parsing_metadata'].get('confidence_score', 0.0)
        
        # Count extracted information
        extracted_count = 0
        if contract.entities and 'extracted_entities' in contract.entities:
            entities = contract.entities['extracted_entities']
            extracted_count = len(entities.get('key_clauses', {}))
        
        section_count = 0
        if contract.entities and 'sections' in contract.entities:
            section_count = len(contract.entities['sections'])
        
        return {
            'is_valid': len(errors) == 0,
            'error_count': len(errors),
            'errors': errors,
            'confidence_score': confidence_score,
            'extracted_clauses': extracted_count,
            'section_count': section_count,
            'validation_timestamp': datetime.now(timezone.utc).isoformat(),
            'contract_type': contract.contract_type.value,
            'has_dates': contract.effective_date is not None or contract.expiration_date is not None,
            'has_value': contract.total_value is not None
        }
