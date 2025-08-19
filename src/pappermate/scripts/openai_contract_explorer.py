#!/usr/bin/env python3
"""
Real Contract Analysis using OpenAI
Analyzes real PDF contracts from .pdfContracts folder with RANDOM selection
Generates structured outputs in JSON and CSV formats
"""

import os
import sys
import json
import logging
import random
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import openai
    from pappermate.services.pdf_converter import PDFConverter
    from pappermate.services.marker_wrapper import MarkerWrapper
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("Tentando importar módulos alternativos...")
    
    # Fallback imports
    try:
        import openai
    except ImportError:
        print("❌ OpenAI SDK não encontrado. Execute: pip3 install openai")
        sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealContractAnalyzer:
    """Analyzer for real PDF contracts using OpenAI with random selection"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the analyzer"""
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            raise ValueError("OpenAI API key não configurada")
        
        try:
            self.client = openai.OpenAI(api_key=self.api_key)
            # Test connection
            models = self.client.models.list()
            logger.info(f"✅ Conectado à OpenAI. Modelos disponíveis: {len(models.data)}")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar à OpenAI: {e}")
            raise
        
        # Initialize PDF processing
        try:
            self.pdf_converter = PDFConverter()
            logger.info("✅ PDF Converter inicializado")
        except Exception as e:
            logger.warning(f"⚠️  PDF Converter não disponível: {e}")
            self.pdf_converter = None
        
        try:
            self.marker_wrapper = MarkerWrapper()
            logger.info("✅ Marker Wrapper inicializado")
        except Exception as e:
            logger.warning(f"⚠️  Marker Wrapper não disponível: {e}")
            self.marker_wrapper = None
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using available methods"""
        try:
            # Try PDF converter first
            if self.pdf_converter:
                document = self.pdf_converter.convert_pdf(pdf_path)
                return document.get_text_content()
        except Exception as e:
            logger.warning(f"PDF Converter falhou para {pdf_path}: {e}")
        
        try:
            # Fallback to marker wrapper
            if self.marker_wrapper:
                result = self.marker_wrapper.extract_text(pdf_path)
                return result.get("text", "")
        except Exception as e:
            logger.warning(f"Marker Wrapper falhou para {pdf_path}: {e}")
        
        # Final fallback - try basic text extraction
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"Todas as tentativas de extração falharam para {pdf_path}: {e}")
            return ""
    
    def analyze_contract_with_openai(self, contract_text: str, pdf_path: str) -> Optional[Dict[str, Any]]:
        """Analyze contract text using OpenAI"""
        
        # Enhanced prompt for real contracts
        prompt = f"""
        Analise o seguinte contrato real e extraia informações estruturadas em JSON.
        
        Este é um contrato real de negócios. Procure por:
        1. Contract ID (identificador único, número de contrato)
        2. Contract Name/Title (nome/título do contrato)
        3. Parent contracts (referências a outros contratos)
        4. Child contracts (contratos que referenciam este)
        5. Contract type (tipo de contrato: SoW, MSA, NDA, etc.)
        6. Parties involved (partes envolvidas, empresas)
        7. Effective date (data de vigência)
        8. Expiration date (data de expiração)
        9. Contract value (valor do contrato)
        10. Key terms (termos importantes)
        11. Relationship type (tipo de relacionamento)
        12. Business area (área de negócio)
        13. Project scope (escopo do projeto)
        14. Confidence score (confiança na extração)
        
        Retorne APENAS JSON válido com esta estrutura:
        {{
            "contract_id": "string ou null",
            "contract_name": "string ou null",
            "parent_contracts": ["lista de contract IDs"],
            "child_contracts": ["lista de contract IDs"],
            "contract_type": "string ou null",
            "parties": ["lista de nomes das partes"],
            "effective_date": "string ou null",
            "expiration_date": "string ou null",
            "contract_value": "string ou null",
            "key_terms": ["lista de termos importantes"],
            "relationship_type": "string ou null",
            "business_area": "string ou null",
            "project_scope": "string ou null",
            "confidence": 0.95,
            "analysis_notes": "observações da análise",
            "extraction_method": "openai"
        }}
        
        Texto do contrato:
        {contract_text[:5000]}  # Limitar para eficiência da API
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um especialista em análise de contratos de negócios reais. Extraia informações estruturadas em JSON válido com alta precisão. Foque em identificar relacionamentos entre contratos e informações comerciais importantes."
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
                
                # Add metadata
                data['pdf_path'] = pdf_path
                data['pdf_filename'] = Path(pdf_path).name
                data['analysis_timestamp'] = datetime.now().isoformat()
                data['text_length'] = len(contract_text)
                
                return data
                
            except json.JSONDecodeError as e:
                logger.error(f"⚠️  Erro ao parsear JSON: {e}")
                logger.error(f"Resposta recebida: {content}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro na API OpenAI: {e}")
            return None
    
    def analyze_single_contract(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """Analyze a single contract"""
        logger.info(f"🔍 Analisando contrato: {pdf_path}")
        
        try:
            # Extract text
            contract_text = self.extract_text_from_pdf(pdf_path)
            
            if not contract_text.strip():
                logger.warning(f"⚠️  Nenhum texto extraído de {pdf_path}")
                return None
            
            logger.info(f"📄 Texto extraído: {len(contract_text)} caracteres")
            
            # Analyze with OpenAI
            analysis_result = self.analyze_contract_with_openai(contract_text, pdf_path)
            
            if analysis_result:
                logger.info(f"✅ Análise concluída para {pdf_path}")
                return analysis_result
            else:
                logger.error(f"❌ Falha na análise de {pdf_path}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao analisar {pdf_path}: {e}")
            return None
    
    def select_stratified_contracts(self, pdf_paths: List[str], num_contracts: int) -> List[str]:
        """Select contracts with stratified sampling by supplier/type patterns"""
        if num_contracts >= len(pdf_paths):
            logger.info(f"📊 Selecionando todos os {len(pdf_paths)} contratos disponíveis")
            return pdf_paths
        
        # Set random seed for reproducibility
        random.seed(datetime.now().timestamp())
        
        # Analyze filename patterns to identify suppliers and types
        supplier_groups = {}
        type_groups = {}
        
        for pdf_path in pdf_paths:
            filename = Path(pdf_path).name.lower()
            
            # Detect supplier patterns
            if 'born' in filename:
                supplier = 'BORN'
            elif 'ernst' in filename or 'ey' in filename:
                supplier = 'Ernst & Young'
            elif 'cognizant' in filename:
                supplier = 'Cognizant'
            elif 'accenture' in filename:
                supplier = 'Accenture'
            elif 'ukcr' in filename:
                supplier = 'UKCR'
            else:
                supplier = 'Other'
            
            # Detect contract type patterns
            if 'sow' in filename:
                contract_type = 'SoW'
            elif 'msa' in filename:
                contract_type = 'MSA'
            elif 'nda' in filename:
                contract_type = 'NDA'
            else:
                contract_type = 'Other'
            
            # Group by supplier
            if supplier not in supplier_groups:
                supplier_groups[supplier] = []
            supplier_groups[supplier].append(pdf_path)
            
            # Group by type
            if contract_type not in type_groups:
                type_groups[contract_type] = []
            type_groups[contract_type].append(pdf_path)
        
        # Calculate target per group (stratified)
        selected_contracts = []
        
        # Distribute contracts across suppliers
        for supplier, paths in supplier_groups.items():
            target_count = max(1, int(num_contracts * len(paths) / len(pdf_paths)))
            if paths and len(selected_contracts) < num_contracts:
                sample_size = min(target_count, len(paths), num_contracts - len(selected_contracts))
                sample = random.sample(paths, sample_size)
                selected_contracts.extend(sample)
        
        # If we still need more contracts, add from any group
        if len(selected_contracts) < num_contracts:
            remaining_paths = [p for p in pdf_paths if p not in selected_contracts]
            if remaining_paths:
                additional_needed = num_contracts - len(selected_contracts)
                additional_sample = random.sample(remaining_paths, min(additional_needed, len(remaining_paths)))
                selected_contracts.extend(additional_sample)
        
        # Ensure we don't exceed the requested number
        selected_contracts = selected_contracts[:num_contracts]
        
        logger.info(f"🎯 Seleção estratificada: {len(selected_contracts)} contratos de {len(pdf_paths)} disponíveis")
        logger.info(f"🏢 Grupos de fornecedores: {list(supplier_groups.keys())}")
        logger.info(f"🏷️  Grupos de tipos: {list(type_groups.keys())}")
        
        # Show which contracts were selected
        for i, contract in enumerate(selected_contracts, 1):
            contract_name = Path(contract).name
            logger.info(f"   {i}. {contract_name}")
        
        return selected_contracts
    
    def analyze_multiple_contracts(self, pdf_paths: List[str], max_contracts: int = 10) -> List[Dict[str, Any]]:
        """Analyze multiple contracts with stratified selection"""
        logger.info(f"🚀 Iniciando análise de {max_contracts} contratos (seleção estratificada)")
        
        # Select stratified contracts
        selected_contracts = self.select_stratified_contracts(pdf_paths, max_contracts)
        
        results = []
        failed_contracts = []
        
        for i, pdf_path in enumerate(selected_contracts, 1):
            logger.info(f"📊 Progresso: {i}/{len(selected_contracts)}")
            
            try:
                result = self.analyze_single_contract(pdf_path)
                if result:
                    results.append(result)
                    logger.info(f"✅ Contrato {i} analisado com sucesso")
                else:
                    failed_contracts.append(pdf_path)
                    logger.warning(f"⚠️  Contrato {i} falhou na análise")
            except Exception as e:
                failed_contracts.append(pdf_path)
                logger.error(f"❌ Erro no contrato {i}: {e}")
            
            # Small delay to avoid rate limiting
            import time
            time.sleep(1)
        
        logger.info(f"📈 Análise concluída: {len(results)} sucessos, {len(failed_contracts)} falhas")
        
        return results, failed_contracts
    
    def create_output_directory(self) -> Path:
        """Create structured output directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(f"contract_analysis_results_{timestamp}")
        
        # Create main directory
        output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (output_dir / "json").mkdir(exist_ok=True)
        (output_dir / "csv").mkdir(exist_ok=True)
        (output_dir / "jsonl").mkdir(exist_ok=True)  # For training data
        (output_dir / "summary").mkdir(exist_ok=True)
        (output_dir / "logs").mkdir(exist_ok=True)
        
        logger.info(f"📁 Diretório de saída criado: {output_dir}")
        return output_dir
    
    def save_json_results(self, results: List[Dict[str, Any]], output_dir: Path) -> str:
        """Save analysis results to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = output_dir / "json" / f"contracts_analysis_{timestamp}.json"
        
        output_data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_contracts': len(results),
                'analyzer': 'OpenAI GPT-4',
                'extraction_method': 'PDF + OpenAI',
                'selection_method': 'STRATIFIED'
            },
            'results': results,
            'summary': {
                'contract_types': {},
                'business_areas': {},
                'parties': {},
                'relationship_types': {}
            }
        }
        
        # Generate summary statistics
        for result in results:
            # Contract types
            contract_type = result.get('contract_type', 'Unknown')
            output_data['summary']['contract_types'][contract_type] = output_data['summary']['contract_types'].get(contract_type, 0) + 1
            
            # Business areas
            business_area = result.get('business_area', 'Unknown')
            output_data['summary']['business_areas'][business_area] = output_data['summary']['business_areas'].get(business_area, 0) + 1
            
            # Parties
            parties = result.get('parties', [])
            for party in parties:
                output_data['summary']['parties'][party] = output_data['summary']['parties'].get(party, 0) + 1
            
            # Relationship types
            relationship_type = result.get('relationship_type', 'Unknown')
            output_data['summary']['relationship_types'][relationship_type] = output_data['summary']['relationship_types'].get(relationship_type, 0) + 1
        
        # Save to file
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Resultados JSON salvos em: {json_file}")
        return str(json_file)
    
    def save_csv_results(self, results: List[Dict[str, Any]], output_dir: Path) -> str:
        """Save analysis results to CSV for easy reading"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = output_dir / "csv" / f"contracts_analysis_{timestamp}.csv"
        
        if not results:
            logger.warning("⚠️  Nenhum resultado para salvar em CSV")
            return ""
        
        # Define CSV fields
        csv_fields = [
            'pdf_filename', 'contract_id', 'contract_name', 'contract_type',
            'parties', 'effective_date', 'expiration_date', 'contract_value',
            'business_area', 'project_scope', 'relationship_type',
            'parent_contracts', 'child_contracts', 'key_terms',
            'confidence', 'analysis_notes', 'text_length', 'analysis_timestamp'
        ]
        
        # Prepare data for CSV
        csv_data = []
        for result in results:
            row = {}
            for field in csv_fields:
                value = result.get(field, '')
                
                # Handle list fields
                if isinstance(value, list):
                    value = '; '.join(str(item) for item in value)
                
                # Handle None values
                if value is None:
                    value = ''
                
                row[field] = str(value)
            
            csv_data.append(row)
        
        # Write CSV file
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=csv_fields)
            writer.writeheader()
            writer.writerows(csv_data)
        
        logger.info(f"💾 Resultados CSV salvos em: {csv_file}")
        return str(csv_file)
    
    def save_jsonl_results(self, results: List[Dict[str, Any]], output_dir: Path) -> str:
        """Save results in JSONL format for training data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        jsonl_file = output_dir / "jsonl" / f"contracts_training_data_{timestamp}.jsonl"
        
        # Convert to training format (one JSON per line)
        training_data = []
        for result in results:
            # Create training example
            training_example = {
                "text": result.get("extracted_text", ""),  # Raw text for training
                "labels": {
                    "contract_id": result.get("contract_id", ""),
                    "contract_name": result.get("contract_name", ""),
                    "contract_type": result.get("contract_type", ""),
                    "supplier": result.get("parties", [])[0] if result.get("parties") else "",
                    "customer": result.get("parties", [])[1] if len(result.get("parties", [])) > 1 else "",
                    "start_date": result.get("effective_date", ""),
                    "end_date": result.get("expiration_date", ""),
                    "business_area": result.get("business_area", ""),
                    "project_scope": result.get("project_scope", ""),
                    "confidence": result.get("confidence", 0.0)
                },
                "metadata": {
                    "filename": result.get("pdf_filename", ""),
                    "text_length": result.get("text_length", 0),
                    "analysis_timestamp": result.get("analysis_timestamp", ""),
                    "openai_model": "gpt-4",
                    "extraction_method": "openai_analysis"
                }
            }
            training_data.append(training_example)
        
        # Write JSONL file (one JSON per line)
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            for example in training_data:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        logger.info(f"💾 Dados de treino JSONL salvos em: {jsonl_file}")
        return str(jsonl_file)
    
    def save_summary_report(self, results: List[Dict[str, Any]], output_dir: Path) -> str:
        """Save summary report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = output_dir / "summary" / f"analysis_summary_{timestamp}.txt"
        
        # Generate summary
        summary_lines = [
            "📊 RELATÓRIO DE ANÁLISE DE CONTRATOS",
            "=" * 50,
            f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"Total de Contratos Analisados: {len(results)}",
            f"Analisador: OpenAI GPT-4",
            f"Método de Seleção: ESTRATIFICADO",
            "",
            "📈 ESTATÍSTICAS GERAIS:",
            "-" * 30
        ]
        
        if results:
            # Contract types
            contract_types = {}
            business_areas = {}
            parties = {}
            
            for result in results:
                # Count contract types
                contract_type = result.get('contract_type', 'Unknown')
                contract_types[contract_type] = contract_types.get(contract_type, 0) + 1
                
                # Count business areas
                business_area = result.get('business_area', 'Unknown')
                business_areas[business_area] = business_areas.get(business_area, 0) + 1
                
                # Count parties
                for party in result.get('parties', []):
                    parties[party] = parties.get(party, 0) + 1
            
            # Add statistics to summary
            summary_lines.extend([
                "",
                "🏷️  TIPOS DE CONTRATO:",
                "-" * 20
            ])
            
            for contract_type, count in sorted(contract_types.items(), key=lambda x: x[1], reverse=True):
                summary_lines.append(f"  {contract_type}: {count}")
            
            summary_lines.extend([
                "",
                "🏢 ÁREAS DE NEGÓCIO:",
                "-" * 20
            ])
            
            for business_area, count in sorted(business_areas.items(), key=lambda x: x[1], reverse=True):
                summary_lines.append(f"  {business_area}: {count}")
            
            summary_lines.extend([
                "",
                "👥 PARTES ENVOLVIDAS:",
                "-" * 20
            ])
            
            for party, count in sorted(parties.items(), key=lambda x: x[1], reverse=True):
                summary_lines.append(f"  {party}: {count}")
        
        # Write summary file
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary_lines))
        
        logger.info(f"💾 Relatório de resumo salvo em: {summary_file}")
        return str(summary_file)
    
    def save_results(self, results: List[Dict[str, Any]]) -> Dict[str, str]:
        """Save analysis results in multiple formats"""
        # Create output directory
        output_dir = self.create_output_directory()
        
        # Save in different formats
        json_file = self.save_json_results(results, output_dir)
        csv_file = self.save_csv_results(results, output_dir)
        jsonl_file = self.save_jsonl_results(results, output_dir)  # Training data
        summary_file = self.save_summary_report(results, output_dir)
        
        # Create README file
        readme_file = output_dir / "README.md"
        readme_content = f"""# 📊 Resultados da Análise de Contratos

## 📁 Estrutura dos Arquivos

- **`json/`** - Resultados completos em formato JSON
- **`csv/** - Resultados em formato CSV para fácil leitura
- **`jsonl/`** - Dados de treino em formato JSONL (uma linha por contrato)
- **`summary/`** - Relatórios de resumo
- **`logs/`** - Logs de execução

## 📈 Estatísticas

- **Total de Contratos Analisados**: {len(results)}
- **Data da Análise**: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
- **Analisador**: OpenAI GPT-4
- **Método de Seleção**: Aleatório

## 🔍 Como Usar

### Para Análise Detalhada
Abra o arquivo JSON para ver todos os detalhes de cada contrato.

### Para Análise Rápida
Use o arquivo CSV no Excel ou Google Sheets para análise visual.

### Para Resumo Executivo
Leia o arquivo de resumo para estatísticas gerais.

## 📋 Campos Disponíveis

- **Contract ID**: Identificador único do contrato
- **Contract Name**: Nome/título do contrato
- **Contract Type**: Tipo de contrato (SoW, MSA, NDA, etc.)
- **Parties**: Partes envolvidas
- **Business Area**: Área de negócio
- **Project Scope**: Escopo do projeto
- **Relationship Type**: Tipo de relacionamento
- **Parent/Child Contracts**: Contratos relacionados
"""
        
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info(f"💾 README criado: {readme_file}")
        
        return {
            'output_directory': str(output_dir),
            'json_file': json_file,
            'csv_file': csv_file,
            'jsonl_file': jsonl_file,  # Training data
            'summary_file': summary_file,
            'readme_file': str(readme_file)
        }

def main():
    """Main function"""
    print("🚀 Análise de Contratos Reais com OpenAI (SELEÇÃO ESTRATIFICADA)")
    print("=" * 70)
    
    try:
        # Initialize analyzer
        analyzer = RealContractAnalyzer()
        
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
        
        # Ask user how many contracts to analyze
        print(f"\n🔢 Quantos contratos você quer analisar? (máximo: {len(pdf_files)})")
        try:
            max_contracts = int(input("Digite o número (ou Enter para padrão 5): ") or "5")
            max_contracts = min(max_contracts, len(pdf_files))
        except ValueError:
            max_contracts = 5
        
        print(f"📊 Analisando {max_contracts} contratos (seleção ESTRATIFICADA)...")
        
        # Analyze contracts
        results, failed = analyzer.analyze_multiple_contracts(
            [str(f) for f in pdf_files], 
            max_contracts=max_contracts
        )
        
        if results:
            # Save results in multiple formats
            output_files = analyzer.save_results(results)
            
            print(f"\n🎉 Análise concluída!")
            print(f"✅ Sucessos: {len(results)}")
            print(f"❌ Falhas: {len(failed)}")
            print(f"📁 Resultados salvos em: {output_files['output_directory']}")
            
            print(f"\n📋 Arquivos Gerados:")
            print(f"   📊 JSON: {Path(output_files['json_file']).name}")
            print(f"   📈 CSV: {Path(output_files['csv_file']).name}")
            print(f"   🧠 JSONL: {Path(output_files['jsonl_file']).name} (dados de treino)")
            print(f"   📋 Resumo: {Path(output_files['summary_file']).name}")
            print(f"   📖 README: {Path(output_files['readme_file']).name}")
            
            # Show sample results
            if results:
                print(f"\n📊 Exemplo de resultado:")
                sample = results[0]
                print(f"   Contract ID: {sample.get('contract_id', 'N/A')}")
                print(f"   Contract Type: {sample.get('contract_type', 'N/A')}")
                print(f"   Parties: {', '.join(sample.get('parties', []))}")
                print(f"   Business Area: {sample.get('business_area', 'N/A')}")
        
        else:
            print("❌ Nenhum contrato foi analisado com sucesso")
            
    except Exception as e:
        logger.error(f"❌ Erro na execução: {e}")
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()
