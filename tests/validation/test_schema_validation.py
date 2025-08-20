"""
Tests for Schema Validation Service.

Tests the schema generation, validation, and business rule validation.
"""

import pytest
import json
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock

from src.pappermate.validation.schema import SchemaValidator
from src.pappermate.models.document import Document, Contract, ContractHierarchy, ContractType, DocumentType, DocumentStatus
from datetime import datetime, timezone


class TestSchemaValidator:
    """Test cases for SchemaValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SchemaValidator()
        
        # Create sample models for testing
        self.sample_document = Document(
            id="test-doc-1",
            filename="test_contract.pdf",
            file_path="/path/to/test_contract.pdf",
            document_type=DocumentType.PDF,
            mime_type="application/pdf",
            file_size=1024,
            status=DocumentStatus.CONVERTED,
            content="Sample contract content",
            metadata={"source": "test"}
        )
        
        self.sample_contract = Contract(
            document=self.sample_document,
            contract_type=ContractType.MSA,
            contract_number="MSA-2024-001",
            contract_name="Test Master Service Agreement",
            client_name="Test Client Inc.",
            vendor_name="Test Vendor Ltd.",
            effective_date=datetime(2024, 1, 1),
            expiration_date=datetime(2024, 12, 31),
            total_value=100000.0,
            currency="USD",
            entities={
                'sections': {'section1': 'content1'},
                'extracted_entities': {'key_clauses': {'vigência': True}},
                'parsing_metadata': {
                    'parser_version': '1.0',
                    'extraction_date': datetime.utcnow().isoformat(),
                    'confidence_score': 0.9
                }
            }
        )
        
        self.sample_hierarchy = ContractHierarchy(
            hierarchy_id="hierarchy-1",
            name="Test Contract Hierarchy",
            root_contract_id="test-doc-1",
            contracts=[self.sample_contract],
            is_valid=True,
            validation_errors=[]
        )
    
    def test_validator_initialization(self):
        """Test that validator initializes with schemas."""
        assert self.validator.schemas is not None
        assert 'Document' in self.validator.schemas
        assert 'Contract' in self.validator.schemas
        assert 'ContractHierarchy' in self.validator.schemas
        assert 'ContractValidation' in self.validator.schemas
    
    def test_get_schema(self):
        """Test getting specific schemas."""
        document_schema = self.validator.get_schema('Document')
        assert document_schema is not None
        assert document_schema['title'] == 'Document'
        
        contract_schema = self.validator.get_schema('Contract')
        assert contract_schema is not None
        assert contract_schema['title'] == 'Contract'
        
        # Test non-existent schema
        non_existent = self.validator.get_schema('NonExistent')
        assert non_existent is None
    
    def test_get_all_schemas(self):
        """Test getting all schemas."""
        all_schemas = self.validator.get_all_schemas()
        
        assert 'Document' in all_schemas
        assert 'Contract' in all_schemas
        assert 'ContractHierarchy' in all_schemas
        assert 'ContractValidation' in all_schemas
        
        # Should be a copy, not the original
        assert all_schemas is not self.validator.schemas
    
    def test_export_schemas(self):
        """Test schema export to files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exported_files = self.validator.export_schemas(temp_dir)
            
            assert len(exported_files) == 5  # 4 individual + 1 combined
            
            # Check that files were created
            for file_path in exported_files:
                assert Path(file_path).exists()
                assert Path(file_path).stat().st_size > 0
            
            # Check specific files
            document_schema_file = Path(temp_dir) / "document_schema.json"
            assert document_schema_file.exists()
            
            validation_schema_file = Path(temp_dir) / "validation_schema.json"
            assert validation_schema_file.exists()
            
            # Check validation schema content
            with open(validation_schema_file, 'r') as f:
                validation_data = json.load(f)
                assert validation_data['title'] == 'PapperMate Contract Validation Schema'
                assert validation_data['version'] == '1.0.0'
                assert 'schemas' in validation_data
    
    def test_validate_contract_success(self):
        """Test successful contract validation."""
        errors = self.validator.validate_contract(self.sample_contract)
        
        # Should have no errors
        assert len(errors) == 0
    
    def test_validate_contract_missing_required_fields(self):
        """Test contract validation with missing required fields."""
        # Create contract with missing fields
        invalid_contract = Contract(
            document=self.sample_document,
            contract_type=ContractType.MSA,
            contract_number="N/A",  # Missing
            contract_name="N/A",    # Missing
            client_name="N/A",      # Missing
            vendor_name="N/A",      # Missing
            entities={}
        )
        
        errors = self.validator.validate_contract(invalid_contract)
        
        # Should have errors for missing fields
        assert len(errors) > 0
        assert any("Contract must have a valid name" in err for err in errors)
        assert any("Contract must have a valid contract number" in err for err in errors)
        assert any("Contract must have a valid client name" in err for err in errors)
        assert any("Contract must have a valid vendor name" in err for err in errors)
    
    def test_validate_contract_invalid_dates(self):
        """Test contract validation with invalid dates."""
        # Create contract with invalid date logic
        invalid_contract = Contract(
            document=self.sample_document,
            contract_type=ContractType.MSA,
            contract_number="TEST-001",
            contract_name="Test Contract",
            client_name="Test Client",
            vendor_name="Test Vendor",
            effective_date=datetime(2024, 12, 31),  # After expiration
            expiration_date=datetime(2024, 1, 1),   # Before effective
            entities={}
        )
        
        errors = self.validator.validate_contract(invalid_contract)
        
        # Should have error for invalid date logic
        assert len(errors) > 0
        assert any("Effective date must be before expiration date" in err for err in errors)
    
    def test_validate_contract_invalid_value(self):
        """Test contract validation with invalid value."""
        # Create contract with invalid value
        invalid_contract = Contract(
            document=self.sample_document,
            contract_type=ContractType.MSA,
            contract_number="TEST-001",
            contract_name="Test Contract",
            client_name="Test Client",
            vendor_name="Test Vendor",
            total_value=-1000.0,  # Negative value
            entities={}
        )
        
        errors = self.validator.validate_contract(invalid_contract)
        
        # Should have error for invalid value
        assert len(errors) > 0
        assert any("Contract total value must be positive" in err for err in errors)
    
    def test_validate_contract_missing_entities_structure(self):
        """Test contract validation with missing entities structure."""
        # Create contract with incomplete entities
        invalid_contract = Contract(
            document=self.sample_document,
            contract_type=ContractType.MSA,
            contract_number="TEST-001",
            contract_name="Test Contract",
            client_name="Test Client",
            vendor_name="Test Vendor",
            entities={
                'sections': {'section1': 'content1'}
                # Missing extracted_entities and parsing_metadata
            }
        )
        
        errors = self.validator.validate_contract(invalid_contract)
        
        # Should have errors for missing entities structure
        assert len(errors) > 0
        assert any("Contract entities must include extracted entities" in err for err in errors)
        assert any("Contract entities must include parsing metadata" in err for err in errors)
    
    def test_validate_document_success(self):
        """Test successful document validation."""
        errors = self.validator.validate_document(self.sample_document)
        
        # Should have no errors
        assert len(errors) == 0
    
    def test_validate_document_missing_fields(self):
        """Test document validation with missing fields."""
        # Create document with missing fields
        invalid_document = Document(
            id="test-doc-2",
            filename="",  # Missing
            file_path="",  # Missing
            document_type=DocumentType.PDF,
            mime_type="application/pdf",
            file_size=0,  # Invalid
            status=DocumentStatus.ERROR,
            error_message="",  # Missing for error status
            metadata={}
        )
        
        errors = self.validator.validate_document(invalid_document)
        
        # Should have errors for missing fields
        assert len(errors) > 0
        assert any("Document must have a valid filename" in err for err in errors)
        assert any("Document must have a valid file path" in err for err in errors)
        assert any("Document must have a positive file size" in err for err in errors)
        assert any("Document with error status must have an error message" in err for err in errors)
    
    def test_validate_contract_hierarchy_success(self):
        """Test successful contract hierarchy validation."""
        errors = self.validator.validate_contract_hierarchy(self.sample_hierarchy)
        
        # Should have no errors
        assert len(errors) == 0
    
    def test_validate_contract_hierarchy_missing_fields(self):
        """Test contract hierarchy validation with missing fields."""
        # Create hierarchy with missing fields
        invalid_hierarchy = ContractHierarchy(
            hierarchy_id="hierarchy-2",
            name="",  # Missing
            root_contract_id="",  # Missing
            contracts=[],
            is_valid=False,
            validation_errors=[]  # Missing for invalid status
        )
        
        errors = self.validator.validate_contract_hierarchy(invalid_hierarchy)
        
        # Should have errors for missing fields
        assert len(errors) > 0
        assert any("Contract hierarchy must have a valid name" in err for err in errors)
        assert any("Contract hierarchy must have a root contract ID" in err for err in errors)
        assert any("Invalid hierarchy must have validation error messages" in err for err in errors)
    
    def test_validate_json_against_schema_success(self):
        """Test successful JSON validation against schema."""
        # Valid JSON data that matches the Contract schema
        valid_json = {
            "document": {
                "id": "test-doc-1",
                "filename": "test_contract.pdf",
                "file_path": "/path/to/test_contract.pdf",
                "document_type": "pdf",
                "mime_type": "application/pdf",
                "file_size": 1024,
                "status": "converted",
                "content": "Sample content",
                "metadata": {"source": "test"}
            },
            "contract_type": "msa",
            "contract_number": "TEST-001",
            "contract_name": "Test Contract",
            "client_name": "Test Client",
            "vendor_name": "Test Vendor",
            "entities": {
                "sections": {"section1": "content1"},
                "extracted_entities": {"key_clauses": {"vigência": True}},
                "parsing_metadata": {
                    "parser_version": "1.0",
                    "extraction_date": datetime.now(timezone.utc).isoformat(),
                    "confidence_score": 0.9
                }
            }
        }
        
        errors = self.validator.validate_json_against_schema(valid_json, "Contract")
        
        # Should have no errors
        assert len(errors) == 0
    
    def test_validate_json_against_schema_missing_required(self):
        """Test JSON validation with missing required fields."""
        # Invalid JSON data (missing required fields)
        invalid_json = {
            "contract_name": "Test Contract"
            # Missing contract_number, client_name, vendor_name
        }
        
        errors = self.validator.validate_json_against_schema(invalid_json, "Contract")
        
        # Should have errors for missing required fields
        assert len(errors) > 0
        assert any("Required field" in err for err in errors)
    
    def test_validate_json_against_schema_invalid_format(self):
        """Test JSON validation with invalid JSON format."""
        # Invalid JSON string
        invalid_json = "invalid json content"
        
        errors = self.validator.validate_json_against_schema(invalid_json, "Contract")
        
        # Should have error for invalid JSON
        assert len(errors) > 0
        assert any("Invalid JSON format" in err for err in errors)
    
    def test_validate_json_against_schema_not_found(self):
        """Test JSON validation with non-existent schema."""
        # Valid JSON data
        valid_json = {"test": "data"}
        
        errors = self.validator.validate_json_against_schema(valid_json, "NonExistentSchema")
        
        # Should have error for schema not found
        assert len(errors) > 0
        assert any("Schema 'NonExistentSchema' not found" in err for err in errors)
    
    def test_get_validation_summary(self):
        """Test validation summary generation."""
        summary = self.validator.get_validation_summary(self.sample_contract)
        
        # Check summary structure
        assert 'is_valid' in summary
        assert 'error_count' in summary
        assert 'errors' in summary
        assert 'confidence_score' in summary
        assert 'extracted_clauses' in summary
        assert 'section_count' in summary
        assert 'validation_timestamp' in summary
        assert 'contract_type' in summary
        assert 'has_dates' in summary
        assert 'has_value' in summary
        
        # Check summary values
        assert summary['is_valid'] is True
        assert summary['error_count'] == 0
        assert summary['confidence_score'] == 0.9
        assert summary['extracted_clauses'] == 1
        assert summary['section_count'] == 1
        assert summary['contract_type'] == 'msa'
        assert summary['has_dates'] is True
        assert summary['has_value'] is True
    
    def test_get_validation_summary_with_errors(self):
        """Test validation summary generation with errors."""
        # Create invalid contract
        invalid_contract = Contract(
            document=self.sample_document,
            contract_type=ContractType.MSA,
            contract_number="N/A",
            contract_name="N/A",
            client_name="N/A",
            vendor_name="N/A",
            entities={}
        )
        
        summary = self.validator.get_validation_summary(invalid_contract)
        
        # Check summary values
        assert summary['is_valid'] is False
        assert summary['error_count'] > 0
        assert summary['confidence_score'] == 0.0
        assert summary['extracted_clauses'] == 0
        assert summary['section_count'] == 0
    
    def test_validate_json_structure_basic_types(self):
        """Test basic JSON structure validation."""
        # Test string type
        errors = self.validator._validate_json_structure("test", {"type": "string"})
        assert len(errors) == 0
        
        # Test integer type
        errors = self.validator._validate_json_structure(123, {"type": "integer"})
        assert len(errors) == 0
        
        # Test number type
        errors = self.validator._validate_json_structure(123.45, {"type": "number"})
        assert len(errors) == 0
        
        # Test boolean type
        errors = self.validator._validate_json_structure(True, {"type": "boolean"})
        assert len(errors) == 0
        
        # Test array type
        errors = self.validator._validate_json_structure([1, 2, 3], {"type": "array"})
        assert len(errors) == 0
        
        # Test object type
        errors = self.validator._validate_json_structure({"key": "value"}, {"type": "object"})
        assert len(errors) == 0
    
    def test_validate_json_structure_type_mismatch(self):
        """Test JSON structure validation with type mismatches."""
        # Test string type mismatch
        errors = self.validator._validate_json_structure(123, {"type": "string"})
        assert len(errors) > 0
        assert any("Expected string type" in err for err in errors)
        
        # Test integer type mismatch
        errors = self.validator._validate_json_structure("123", {"type": "integer"})
        assert len(errors) > 0
        assert any("Expected integer type" in err for err in errors)
        
        # Test number type mismatch
        errors = self.validator._validate_json_structure("123.45", {"type": "number"})
        assert len(errors) > 0
        assert any("Expected number type" in err for err in errors)
    
    def test_validate_json_structure_required_fields(self):
        """Test JSON structure validation with required fields."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name", "age"]
        }
        
        # Valid data
        valid_data = {"name": "John", "age": 30}
        errors = self.validator._validate_json_structure(valid_data, schema)
        assert len(errors) == 0
        
        # Missing required field
        invalid_data = {"name": "John"}  # Missing age
        errors = self.validator._validate_json_structure(invalid_data, schema)
        assert len(errors) > 0
        assert any("Required field 'age' is missing" in err for err in errors)
    
    def test_validate_json_structure_nested_objects(self):
        """Test JSON structure validation with nested objects."""
        schema = {
            "type": "object",
            "properties": {
                "person": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"}
                    },
                    "required": ["name", "age"]
                }
            }
        }
        
        # Valid nested data
        valid_data = {"person": {"name": "John", "age": 30}}
        errors = self.validator._validate_json_structure(valid_data, schema)
        assert len(errors) == 0
        
        # Invalid nested data
        invalid_data = {"person": {"name": "John"}}  # Missing age
        errors = self.validator._validate_json_structure(invalid_data, schema)
        assert len(errors) > 0
        assert any("Property 'person': Required field 'age' is missing" in err for err in errors)
    
    def test_validate_json_structure_arrays(self):
        """Test JSON structure validation with arrays."""
        schema = {
            "type": "object",
            "properties": {
                "numbers": {
                    "type": "array",
                    "items": {"type": "integer"}
                }
            }
        }
        
        # Valid array data
        valid_data = {"numbers": [1, 2, 3, 4, 5]}
        errors = self.validator._validate_json_structure(valid_data, schema)
        assert len(errors) == 0
        
        # Invalid array data
        invalid_data = {"numbers": [1, "2", 3, "4", 5]}  # Mixed types
        errors = self.validator._validate_json_structure(invalid_data, schema)
        assert len(errors) > 0
        assert any("Item 1: Expected integer type" in err for err in errors)
        assert any("Item 3: Expected integer type" in err for err in errors)
