"""
Document models for PapperMate

Base models for documents, contracts, and contract hierarchies.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class DocumentType(str, Enum):
    """Types of documents in the system."""
    PDF = "pdf"
    MARKDOWN = "markdown"
    JSON = "json"
    TEXT = "text"


class DocumentStatus(str, Enum):
    """Status of document processing."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    CONVERTED = "converted"
    ANALYZED = "analyzed"
    ERROR = "error"


class Document(BaseModel):
    """Base document model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    # Basic identification
    id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Path to stored file")
    
    # Metadata
    document_type: DocumentType = Field(..., description="Type of document")
    mime_type: str = Field(..., description="MIME type of the document")
    file_size: int = Field(..., description="File size in bytes")
    
    # Processing status
    status: DocumentStatus = Field(default=DocumentStatus.UPLOADED, description="Current processing status")
    
    # Timestamps
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing completion timestamp")
    
    # Content
    content: Optional[str] = Field(None, description="Extracted text content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if processing failed")


class ContractType(str, Enum):
    """Types of contracts in the system."""
    MSA = "msa"  # Master Service Agreement
    LSA = "lsa"  # Local Service Agreement
    SOW = "sow"  # Statement of Work
    PWO = "pwo"  # Project Work Order
    CR = "cr"    # Change Request
    CNF = "cnf"  # Change Notification Form


class Contract(BaseModel):
    """Contract-specific document model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    # Inherit from Document
    document: Document = Field(..., description="Base document information")
    
    # Contract-specific fields
    contract_type: ContractType = Field(..., description="Type of contract")
    contract_number: str = Field(..., description="Contract identifier number")
    contract_name: str = Field(..., description="Name/title of the contract")
    
    # Parties involved
    client_name: str = Field(..., description="Client company name")
    vendor_name: str = Field(..., description="Vendor/contractor company name")
    
    # Dates
    effective_date: Optional[datetime] = Field(None, description="Contract effective date")
    expiration_date: Optional[datetime] = Field(None, description="Contract expiration date")
    
    # Financial
    total_value: Optional[float] = Field(None, description="Total contract value")
    currency: str = Field(default="USD", description="Contract currency")
    
    # Relationships
    parent_contract_id: Optional[str] = Field(None, description="Parent contract ID (for hierarchy)")
    child_contracts: List[str] = Field(default_factory=list, description="Child contract IDs")
    
    # Extracted entities (will be populated by NLP processing)
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities and clauses")


class ContractHierarchy(BaseModel):
    """Model for managing contract relationships."""
    
    model_config = ConfigDict(from_attributes=True)
    
    # Hierarchy identification
    hierarchy_id: str = Field(..., description="Unique hierarchy identifier")
    name: str = Field(..., description="Hierarchy name/description")
    
    # Root contract (usually MSA)
    root_contract_id: str = Field(..., description="Root contract ID")
    
    # All contracts in hierarchy
    contracts: List[Contract] = Field(default_factory=list, description="All contracts in hierarchy")
    
    # Hierarchy metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Hierarchy creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Validation
    is_valid: bool = Field(default=True, description="Whether hierarchy is valid")
    validation_errors: List[str] = Field(default_factory=list, description="Validation error messages")
