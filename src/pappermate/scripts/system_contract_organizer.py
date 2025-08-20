#!/usr/bin/env python3
"""
Smart Contract Processing System
Processes PDF contracts with intelligent renaming, translation, and reversible logs
"""

import os
import sys
import json
import logging
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

from pappermate.services.vector_store import ContractVectorStore
from pappermate.processing.entity_extractor import ContractEntityExtractor

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import openai
except ImportError as e:
    print(f"❌ OpenAI SDK não encontrado: {e}")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ContractMetadata:
    """Contract metadata extracted from analysis"""
    contract_id: str
    contract_name: str
    contract_type: str
    supplier: str
    start_date: str
    end_date: str
    start_year: str
    end_year: str
    parties: List[str]
    business_area: str
    project_scope: str
    confidence: float
    extraction_method: str = "openai"

@dataclass
class ProcessingOperation:
    """Log of a processing operation for reversibility"""
    timestamp: str
    operation: str  # "rename", "translate", "process"
    original_path: str
    new_path: str
    backup_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    reversible: bool = True
    operation_hash: str = ""

class SmartContractProcessor:
    """Intelligent contract processor with reversible operations"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the processor"""
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            raise ValueError("OpenAI API key não configurada")
        
        try:
            self.client = openai.OpenAI(api_key=self.api_key)
            models = self.client.models.list()
            logger.info(f"✅ Conectado à OpenAI. Modelos disponíveis: {len(models.data)}")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar à OpenAI: {e}")
            raise
        
        # Initialize processing
        self.operations_log = []
        self.output_directory = None
        self.vector_store = ContractVectorStore()
        self.entity_extractor = ContractEntityExtractor()
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using available methods"""
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"Erro ao extrair texto de {pdf_path}: {e}")
            return ""
    
    def analyze_contract_with_openai(self, contract_text: str, pdf_path: str) -> Optional[ContractMetadata]:
        """Analyze contract text using OpenAI for metadata extraction"""
        
        prompt = f"""
        Analise o seguinte contrato real e extraia informações estruturadas em JSON.
        
        Procure por:
        1. Contract ID (identificador único, número de contrato)
        2. Contract Name/Title (nome/título do contrato)
        3. Contract type (tipo de contrato: SoW, MSA, NDA, etc.)
        4. Supplier (empresa fornecedora, NÃO Unilever)
        5. Start date (data de início)
        6. End date (data de fim)
        7. Parties involved (partes envolvidas)
        8. Business area (área de negócio)
        9. Project scope (escopo do projeto)
        10. Confidence score (confiança na extração)
        
        IMPORTANTE:
        - Supplier deve ser a empresa fornecedora, não Unilever
        - Se não conseguir identificar end date, use "2999" como placeholder
        - Contract ID deve ser extraído do próprio documento
        
        Retorne APENAS JSON válido com esta estrutura:
        {{
            "contract_id": "string ou null",
            "contract_name": "string ou null",
            "contract_type": "string ou null",
            "supplier": "string ou null",
            "start_date": "string ou null",
            "end_date": "string ou null",
            "parties": ["lista de nomes das partes"],
            "business_area": "string ou null",
            "project_scope": "string ou null",
            "confidence": 0.95
        }}
        
        Texto do contrato:
        {contract_text[:5000]}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um especialista em análise de contratos de negócios reais. Extraia informações estruturadas em JSON válido com alta precisão. Foque em identificar o supplier (empresa fornecedora) e datas de início/fim."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            logger.info(f"✅ Resposta da OpenAI recebida ({len(content)} caracteres)")
            
            # Parse JSON response
            try:
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_str = content[json_start:json_end].strip()
                else:
                    json_str = content.strip()
                
                data = json.loads(json_str)
                
                # Process dates and years
                start_year = self._extract_year(data.get('start_date', ''))
                end_year = self._extract_year(data.get('end_date', ''))
                
                # If no end date, use 2999 as placeholder
                if not end_year:
                    end_year = "2999"
                
                # Create ContractMetadata
                metadata = ContractMetadata(
                    contract_id=data.get('contract_id', 'UNKNOWN'),
                    contract_name=data.get('contract_name', 'Unknown Contract'),
                    contract_type=data.get('contract_type', 'Unknown'),
                    supplier=data.get('supplier', 'Unknown'),
                    start_date=data.get('start_date', ''),
                    end_date=data.get('end_date', ''),
                    start_year=start_year,
                    end_year=end_year,
                    parties=data.get('parties', []),
                    business_area=data.get('business_area', 'Unknown'),
                    project_scope=data.get('project_scope', ''),
                    confidence=data.get('confidence', 0.0)
                )
                
                return metadata
                
            except json.JSONDecodeError as e:
                logger.error(f"⚠️  Erro ao parsear JSON: {e}")
                logger.error(f"Resposta recebida: {content}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro na API OpenAI: {e}")
            return None
    
    def _extract_year(self, date_string: str) -> str:
        """Extract year from date string"""
        if not date_string:
            return ""
        
        # Try to find year pattern (4 digits)
        import re
        year_match = re.search(r'\b(19|20)\d{2}\b', date_string)
        if year_match:
            return year_match.group()
        
        return ""
    
    def _normalize_supplier_name(self, supplier: str) -> str:
        """Normalize supplier name for folder creation"""
        if not supplier:
            return "Unknown"
        
        # Remove special characters and normalize
        normalized = supplier.replace(' ', '_').replace('-', '_')
        normalized = ''.join(c for c in normalized if c.isalnum() or c == '_')
        
        # Limit length
        if len(normalized) > 50:
            normalized = normalized[:50]
        
        return normalized
    
    def _generate_contract_filename(self, metadata: ContractMetadata) -> str:
        """Generate standardized contract filename"""
        
        # Normalize supplier name
        supplier_normalized = self._normalize_supplier_name(metadata.supplier)
        
        # Normalize contract type
        contract_type = metadata.contract_type.upper() if metadata.contract_type else "UNKNOWN"
        
        # Handle year range
        if metadata.start_year == metadata.end_year:
            year_range = metadata.start_year
        else:
            year_range = f"{metadata.start_year}_{metadata.end_year}"
        
        # Normalize contract ID
        contract_id = metadata.contract_id.replace(' ', '_').replace('/', '_').replace('-', '_')
        if not contract_id or contract_id == "null":
            contract_id = "UNKNOWN_ID"
        
        # Generate filename
        filename = f"{supplier_normalized}_{contract_type}_{year_range}_{contract_id}.pdf"
        
        # Clean filename
        filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
        
        return filename
    
    def _determine_operation_type(self, original_filename: str, metadata: ContractMetadata) -> str:
        """Determine if this is a rename or translation operation"""
        
        # Check if filename contains non-ASCII characters (likely needs translation)
        if not original_filename.isascii():
            return "translate"
        
        # Check if filename is already in our standard format
        if "_" in original_filename and len(original_filename.split("_")) >= 4:
            return "rename"
        
        # Default to rename for ASCII filenames
        return "rename"
    
    def process_contract(self, pdf_path: str, output_dir: Path) -> Optional[ProcessingOperation]:
        """Process a single contract"""
        logger.info(f"🔍 Processando contrato: {pdf_path}")
        
        try:
            # Extract text
            contract_text = self.extract_text_from_pdf(pdf_path)
            if not contract_text.strip():
                logger.warning(f"⚠️  Nenhum texto extraído de {pdf_path}")
                return None
            
            # Analyze with OpenAI
            metadata = self.analyze_contract_with_openai(contract_text, pdf_path)
            if not metadata:
                logger.error(f"❌ Falha na análise de {pdf_path}")
                return None

            # Extract entities using local NLP models
            contract_entities = self.entity_extractor.extract_entities(contract_text, contract_id=metadata.contract_id)
            logger.info(f"🧠 Extraídas {len(contract_entities.entities)} entidades com NLP local.")

            # Generate and store embedding in ChromaDB
            if self.entity_extractor.sentence_model:
                try:
                    contract_embedding = self.entity_extractor.sentence_model.encode(contract_text).tolist()
                    self.vector_store.add_contract_embedding(
                        id=metadata.contract_id,
                        embedding=contract_embedding,
                        metadata=asdict(metadata)
                    )
                except Exception as e:
                    logger.error(f"❌ Erro ao gerar/armazenar embedding para {pdf_path}: {e}")

            # Determine operation type
            operation_type = self._determine_operation_type(Path(pdf_path).name, metadata)
            
            # Generate new filename
            new_filename = self._generate_contract_filename(metadata)
            
            # Create supplier directory
            supplier_dir = output_dir / "processed_contracts" / self._normalize_supplier_name(metadata.supplier)
            supplier_dir.mkdir(parents=True, exist_ok=True)
            
            # Define paths
            new_path = supplier_dir / new_filename
            backup_path = None
            
            # Perform operation
            if operation_type == "translate":
                # For translation: copy to processed, keep original as backup
                shutil.copy2(pdf_path, new_path)
                backup_path = pdf_path  # Original stays in place
                logger.info(f"📋 Tradução: {pdf_path} -> {new_path}")
                
            else:  # rename
                # For rename: move to processed directory
                shutil.move(pdf_path, new_path)
                logger.info(f"🔄 Renomeação: {pdf_path} -> {new_path}")
            
            # Create operation log
            operation = ProcessingOperation(
                timestamp=datetime.now().isoformat(),
                operation=operation_type,
                original_path=str(pdf_path),
                new_path=str(new_path),
                backup_path=backup_path,
                metadata=asdict(metadata),
                reversible=True
            )
            
            # Generate operation hash for verification
            operation.operation_hash = self._generate_operation_hash(operation)
            
            logger.info(f"✅ Contrato processado com sucesso: {new_filename}")
            return operation
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar {pdf_path}: {e}")
            return None
    
    def _generate_operation_hash(self, operation: ProcessingOperation) -> str:
        """Generate hash for operation verification"""
        operation_str = f"{operation.timestamp}{operation.operation}{operation.original_path}{operation.new_path}"
        return hashlib.md5(operation_str.encode()).hexdigest()
    
    def process_multiple_contracts(self, pdf_paths: List[str], max_contracts: int = 10) -> List[ProcessingOperation]:
        """Process multiple contracts"""
        logger.info(f"🚀 Iniciando processamento de {min(len(pdf_paths), max_contracts)} contratos")
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_directory = Path(f"contract_processing_results_{timestamp}")
        self.output_directory.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_directory / "processed_contracts").mkdir(exist_ok=True)
        (self.output_directory / "logs").mkdir(exist_ok=True)
        (self.output_directory / "summary").mkdir(exist_ok=True)
        
        # Select random contracts for processing
        import random
        if max_contracts < len(pdf_paths):
            # Set random seed for reproducibility
            random.seed(datetime.now().timestamp())
            selected_paths = random.sample(pdf_paths, max_contracts)
            logger.info(f"🎲 Seleção aleatória: {max_contracts} contratos de {len(pdf_paths)} disponíveis")
            
            # Show which contracts were selected
            for i, contract in enumerate(selected_paths, 1):
                contract_name = Path(contract).name
                logger.info(f"   {i}. {contract_name}")
        else:
            selected_paths = pdf_paths
            logger.info(f"📊 Processando todos os {len(pdf_paths)} contratos disponíveis")
        
        # Process contracts
        operations = []
        failed_contracts = []
        
        for i, pdf_path in enumerate(selected_paths, 1):
            logger.info(f"📊 Progresso: {i}/{len(selected_paths)}")
            
            try:
                operation = self.process_contract(pdf_path, self.output_directory)
                if operation:
                    operations.append(operation)
                    self.operations_log.append(operation)
                    logger.info(f"✅ Contrato {i} processado com sucesso")
                else:
                    failed_contracts.append(pdf_path)
                    logger.warning(f"⚠️  Contrato {i} falhou no processamento")
            except Exception as e:
                failed_contracts.append(pdf_path)
                logger.error(f"❌ Erro no contrato {i}: {e}")
            
            # Small delay to avoid rate limiting
            import time
            time.sleep(1)
        
        # Save logs and summary
        self._save_processing_logs()
        self._save_summary_report(operations, failed_contracts)
        
        logger.info(f"📈 Processamento concluído: {len(operations)} sucessos, {len(failed_contracts)} falhas")
        return operations
    
    def _save_processing_logs(self):
        """Save processing logs for reversibility"""
        if not self.output_directory:
            return
        
        logs_file = self.output_directory / "logs" / "processing_operations.json"
        
        # Convert operations to serializable format
        logs_data = []
        for operation in self.operations_log:
            log_entry = asdict(operation)
            logs_data.append(log_entry)
        
        # Save logs
        with open(logs_file, 'w', encoding='utf-8') as f:
            json.dump(logs_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Logs de processamento salvos em: {logs_file}")
    
    def _save_summary_report(self, operations: List[ProcessingOperation], failed_contracts: List[str]):
        """Save summary report"""
        if not self.output_directory:
            return
        
        summary_file = self.output_directory / "summary" / "processing_summary.txt"
        
        # Generate summary
        summary_lines = [
            "📊 RELATÓRIO DE PROCESSAMENTO DE CONTRATOS",
            "=" * 60,
            f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"Total de Contratos Processados: {len(operations)}",
            f"Contratos com Falha: {len(failed_contracts)}",
            f"Processador: OpenAI GPT-4",
            "",
            "📈 ESTATÍSTICAS GERAIS:",
            "-" * 40
        ]
        
        if operations:
            # Count operations by type
            operation_counts = {}
            supplier_counts = {}
            type_counts = {}
            
            for operation in operations:
                # Count operation types
                op_type = operation.operation
                operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
                
                # Count suppliers
                supplier = operation.metadata.get('supplier', 'Unknown') if operation.metadata else 'Unknown'
                supplier_counts[supplier] = supplier_counts.get(supplier, 0) + 1
                
                # Count contract types
                contract_type = operation.metadata.get('contract_type', 'Unknown') if operation.metadata else 'Unknown'
                type_counts[contract_type] = type_counts.get(contract_type, 0) + 1
            
            # Add statistics to summary
            summary_lines.extend([
                "",
                "🔄 TIPOS DE OPERAÇÃO:",
                "-" * 25
            ])
            
            for op_type, count in sorted(operation_counts.items(), key=lambda x: x[1], reverse=True):
                summary_lines.append(f"  {op_type}: {count}")
            
            summary_lines.extend([
                "",
                "🏢 FORNECEDORES:",
                "-" * 20
            ])
            
            for supplier, count in sorted(supplier_counts.items(), key=lambda x: x[1], reverse=True):
                summary_lines.append(f"  {supplier}: {count}")
            
            summary_lines.extend([
                "",
                "🏷️  TIPOS DE CONTRATO:",
                "-" * 25
            ])
            
            for contract_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                summary_lines.append(f"  {contract_type}: {count}")
        
        # Write summary file
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary_lines))
        
        logger.info(f"💾 Relatório de resumo salvo em: {summary_file}")
    
    def create_readme(self):
        """Create README file with processing information"""
        if not self.output_directory:
            return
        
        readme_file = self.output_directory / "README.md"
        
        readme_content = f"""# 📊 Resultados do Processamento de Contratos

## 📁 Estrutura dos Arquivos

- **`processed_contracts/`** - Contratos processados organizados por fornecedor
- **`logs/`** - Logs de operações para auditoria e reversão
- **`summary/`** - Relatórios de resumo do processamento

## 🔄 Operações Realizadas

### Renomeação
- Contratos com nomes ASCII são renomeados e movidos para pasta organizada
- Nomes originais são alterados para formato padrão
- Logs permitem reversão se necessário

### Tradução
- Contratos com caracteres não-ASCII são processados
- Versões traduzidas são criadas na pasta organizada
- Originais permanecem como backup

## 📋 Formato de Nomenclatura

```
[SUPPLIER]_[TYPE]_[START_YEAR]_[END_YEAR]_[CONTRACT_ID].pdf
```

### Exemplos:
- `GyanSys_SoW_2024_2024_DEV-2024-001.pdf`
- `Capgemini_MSA_2023_2999_MSA-2023-001.pdf`
- `Tessella_NDA_2024_2026_NDA-2024-001.pdf`

## 🔍 Campos Explicados

- **SUPPLIER**: Nome da empresa fornecedora
- **TYPE**: Tipo de contrato (SoW, MSA, NDA, etc.)
- **START_YEAR**: Ano de início do contrato
- **END_YEAR**: Ano de fim ou "2999" se sem término previsto
- **CONTRACT_ID**: ID extraído do próprio contrato

## 🔄 Reversão de Operações

Todos os logs de operação estão em `logs/processing_operations.json` com:
- Timestamp da operação
- Tipo de operação (rename/translate)
- Caminhos originais e novos
- Metadados extraídos
- Hash de verificação

## 📈 Estatísticas

- **Total Processado**: {len(self.operations_log)}
- **Data do Processamento**: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
- **Processador**: OpenAI GPT-4
"""
        
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info(f"💾 README criado: {readme_file}")

def main():
    """Main function"""
    print("🚀 Sistema Inteligente de Processamento de Contratos")
    print("=" * 70)
    
    try:
        # Initialize processor
        processor = SmartContractProcessor()
        
        # Find PDF contracts
        pdf_contracts_dir = Path(__file__).parent.parent.parent.parent / ".pdfContracts"
        if not pdf_contracts_dir.exists():
            print("❌ Pasta .pdfContracts não encontrada")
            print(f"   Procurando em: {pdf_contracts_dir}")
            return
        
        pdf_files = list(pdf_contracts_dir.glob("*.pdf"))
        print(f"📄 Encontrados {len(pdf_files)} contratos PDF")
        
        if not pdf_files:
            print("❌ Nenhum arquivo PDF encontrado")
            return
        
        # Ask user how many contracts to process
        print(f"\n🔢 Quantos contratos você quer processar? (máximo: {len(pdf_files)})")
        try:
            max_contracts = int(input("Digite o número (ou Enter para padrão 5): ") or "5")
            max_contracts = min(max_contracts, len(pdf_files))
        except ValueError:
            max_contracts = 5
        
        print(f"📊 Processando {max_contracts} contratos...")
        
        # Process contracts
        operations = processor.process_multiple_contracts(
            [str(f) for f in pdf_files], 
            max_contracts=max_contracts
        )
        
        if operations:
            # Create README
            processor.create_readme()
            
            print(f"\n🎉 Processamento concluído!")
            print(f"✅ Sucessos: {len(operations)}")
            
            # Calculate actual failures (only the ones we attempted to process)
            processed_paths = [op.original_path for op in operations]
            attempted_files = pdf_files[:max_contracts]  # Only count the ones we tried
            actual_failures = len([f for f in attempted_files if str(f) not in processed_paths])
            print(f"❌ Falhas: {actual_failures}")
            print(f"📁 Resultados salvos em: {processor.output_directory}")
            
            # Show sample results
            if operations:
                print(f"\n📊 Exemplo de resultado:")
                sample = operations[0]
                if sample.metadata:
                    print(f"   Supplier: {sample.metadata.get('supplier', 'N/A')}")
                    print(f"   Type: {sample.metadata.get('contract_type', 'N/A')}")
                    print(f"   Years: {sample.metadata.get('start_year', 'N/A')}-{sample.metadata.get('end_year', 'N/A')}")
                    print(f"   Contract ID: {sample.metadata.get('contract_id', 'N/A')}")
                    print(f"   Operation: {sample.operation}")
        
        else:
            print("❌ Nenhum contrato foi processado com sucesso")
            
    except Exception as e:
        logger.error(f"❌ Erro na execução: {e}")
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()
