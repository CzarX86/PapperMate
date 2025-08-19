"""
Tests for PapperMate data models.

Testing Document, Contract, and ContractHierarchy models.
"""

import pytest
from datetime import datetime
from pappermate.models.document import (
    Document, 
    Contract, 
    ContractHierarchy,
    DocumentType, 
    DocumentStatus, 
    ContractType
)


class TestDocument:
    """Test Document model."""
    
    def test_document_creation(self):
        """Test creating a basic document."""
        doc = Document(
            id="doc_001",
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            document_type=DocumentType.PDF,
            mime_type="application/pdf",
            file_size=1024
        )
        
        assert doc.id == "doc_001"
        assert doc.filename == "test.pdf"
        assert doc.document_type == DocumentType.PDF
        assert doc.status == DocumentStatus.UPLOADED
        assert doc.uploaded_at is not None
        assert doc.processed_at is None
    
    def test_document_status_transitions(self):
        """Test document status transitions."""
        doc = Document(
            id="doc_002",
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            document_type=DocumentType.PDF,
            mime_type="application/pdf",
            file_size=1024
        )
        
        # Initial status
        assert doc.status == DocumentStatus.UPLOADED
        
        # Update status
        doc.status = DocumentStatus.PROCESSING
        assert doc.status == DocumentStatus.PROCESSING
        
        doc.status = DocumentStatus.CONVERTED
        assert doc.status == DocumentStatus.CONVERTED
    
    def test_document_metadata(self):
        """Test document metadata handling."""
        doc = Document(
            id="doc_003",
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            document_type=DocumentType.PDF,
            mime_type="application/pdf",
            file_size=1024,
            metadata={"author": "Test Author", "pages": 10}
        )
        
        assert doc.metadata["author"] == "Test Author"
        assert doc.metadata["pages"] == 10


class TestContract:
    """Test Contract model."""
    
    def test_contract_creation(self):
        """Test creating a contract."""
        # Create base document
        doc = Document(
            id="doc_004",
            filename="contract.pdf",
            file_path="/path/to/contract.pdf",
            document_type=DocumentType.PDF,
            mime_type="application/pdf",
            file_size=2048
        )
        
        # Create contract
        contract = Contract(
            document=doc,
            contract_type=ContractType.MSA,
            contract_number="MSA-2024-001",
            contract_name="Master Service Agreement",
            client_name="Client Corp",
            vendor_name="Vendor Inc"
        )
        
        assert contract.contract_type == ContractType.MSA
        assert contract.contract_number == "MSA-2024-001"
        assert contract.client_name == "Client Corp"
        assert contract.vendor_name == "Vendor Inc"
        assert contract.currency == "USD"  # Default value
    
    def test_contract_hierarchy(self):
        """Test contract hierarchy relationships."""
        # Create MSA
        msa_doc = Document(
            id="msa_doc",
            filename="msa.pdf",
            file_path="/path/to/msa.pdf",
            document_type=DocumentType.PDF,
            mime_type="application/pdf",
            file_size=1024
        )
        
        msa = Contract(
            document=msa_doc,
            contract_type=ContractType.MSA,
            contract_number="MSA-2024-001",
            contract_name="Master Service Agreement",
            client_name="Client Corp",
            vendor_name="Vendor Inc"
        )
        
        # Create SOW (child of MSA)
        sow_doc = Document(
            id="sow_doc",
            filename="sow.pdf",
            file_path="/path/to/sow.pdf",
            document_type=DocumentType.PDF,
            mime_type="application/pdf",
            file_size=512
        )
        
        sow = Contract(
            document=sow_doc,
            contract_type=ContractType.SOW,
            contract_number="SOW-2024-001",
            contract_name="Statement of Work",
            client_name="Client Corp",
            vendor_name="Vendor Inc",
            parent_contract_id="MSA-2024-001"
        )
        
        # Test hierarchy
        assert sow.parent_contract_id == msa.contract_number
        assert msa.child_contracts == []  # Not populated yet


class TestContractHierarchy:
    """Test ContractHierarchy model."""
    
    def test_hierarchy_creation(self):
        """Test creating a contract hierarchy."""
        hierarchy = ContractHierarchy(
            hierarchy_id="hier_001",
            name="Client-Vendor Relationship 2024",
            root_contract_id="MSA-2024-001"
        )
        
        assert hierarchy.hierarchy_id == "hier_001"
        assert hierarchy.name == "Client-Vendor Relationship 2024"
        assert hierarchy.root_contract_id == "MSA-2024-001"
        assert hierarchy.is_valid is True
        assert len(hierarchy.contracts) == 0
    
    def test_hierarchy_validation(self):
        """Test hierarchy validation."""
        hierarchy = ContractHierarchy(
            hierarchy_id="hier_002",
            name="Test Hierarchy",
            root_contract_id="ROOT-001"
        )
        
        # Initially valid
        assert hierarchy.is_valid is True
        
        # Add validation error
        hierarchy.validation_errors.append("Missing contract information")
        hierarchy.is_valid = False
        
        assert hierarchy.is_valid is False
        assert len(hierarchy.validation_errors) == 1
        assert "Missing contract information" in hierarchy.validation_errors


class TestEnums:
    """Test enum values."""
    
    def test_document_types(self):
        """Test document type enum values."""
        assert DocumentType.PDF == "pdf"
        assert DocumentType.MARKDOWN == "markdown"
        assert DocumentType.JSON == "json"
        assert DocumentType.TEXT == "text"
    
    def test_contract_types(self):
        """Test contract type enum values."""
        assert ContractType.MSA == "msa"
        assert ContractType.LSA == "lsa"
        assert ContractType.SOW == "sow"
        assert ContractType.PWO == "pwo"
        assert ContractType.CR == "cr"
        assert ContractType.CNF == "cnf"
    
    def test_document_statuses(self):
        """Test document status enum values."""
        assert DocumentStatus.UPLOADED == "uploaded"
        assert DocumentStatus.PROCESSING == "processing"
        assert DocumentStatus.CONVERTED == "converted"
        assert DocumentStatus.ANALYZED == "analyzed"
        assert DocumentStatus.ERROR == "error"
