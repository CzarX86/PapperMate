#!/usr/bin/env python3
"""
Sample contracts for testing OpenAI analysis
Realistic contract examples to test the system
"""

SAMPLE_CONTRACTS = {
    "service_agreement": """
    CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE DESENVOLVIMENTO DE SOFTWARE
    
    CONTRATO Nº: DEV-2024-001
    REFERÊNCIA: Emenda ao Contrato Principal Nº MAIN-2023-001
    
    ENTRE:
    TechCorp Ltda, pessoa jurídica de direito privado, inscrita no CNPJ sob o nº 12.345.678/0001-90,
    com sede na Rua das Tecnologias, 123, Centro, São Paulo/SP, doravante denominada CONTRATANTE;
    
    E:
    DataSoft Solutions Ltda, pessoa jurídica de direito privado, inscrita no CNPJ sob o nº 98.765.432/0001-10,
    com sede na Av. da Inovação, 456, Vila Madalena, São Paulo/SP, doravante denominada CONTRATADA.
    
    TIPO DE CONTRATO: Emenda ao Contrato de Desenvolvimento de Software
    
    OBJETO: Desenvolvimento de sistema de gestão de contratos com funcionalidades de IA
    
    VIGÊNCIA: 01/01/2024 a 31/12/2024
    
    VALOR: R$ 150.000,00 (cento e cinquenta mil reais)
    
    REFERÊNCIAS A OUTROS CONTRATOS:
    - Contrato Principal: MAIN-2023-001 (Contrato de Serviços Gerais)
    - Contrato de Suporte: SUP-2024-002 (Contrato de Suporte Técnico)
    - Contrato de Infraestrutura: INF-2024-003 (Contrato de Cloud Computing)
    
    CLÁUSULAS ESPECIAIS:
    1. O presente contrato é uma emenda ao contrato principal MAIN-2023-001
    2. Todas as cláusulas do contrato principal permanecem em vigor
    3. Este contrato está sujeito às condições do contrato de infraestrutura INF-2024-003
    """,
    
    "nda_agreement": """
    ACORDO DE CONFIDENCIALIDADE (NDA)
    
    CONTRATO Nº: NDA-2024-001
    REFERÊNCIA: Acordo de Confidencialidade para Projeto PapperMate
    
    ENTRE:
    PapperMate Technologies Inc., pessoa jurídica de direito privado,
    com sede em San Francisco, CA, Estados Unidos, doravante denominada DISCLOSING PARTY;
    
    E:
    TechCorp Ltda, pessoa jurídica de direito privado,
    inscrita no CNPJ sob o nº 12.345.678/0001-90, doravante denominada RECEIVING PARTY.
    
    TIPO DE CONTRATO: Non-Disclosure Agreement (NDA)
    
    OBJETO: Proteção de informações confidenciais relacionadas ao projeto PapperMate
    
    VIGÊNCIA: 01/01/2024 a 31/12/2026 (2 anos)
    
    REFERÊNCIAS A OUTROS CONTRATOS:
    - Contrato de Desenvolvimento: DEV-2024-001
    - Contrato de Licenciamento: LIC-2024-001
    
    OBRIGAÇÕES DE CONFIDENCIALIDADE:
    1. A RECEIVING PARTY se compromete a manter sigilo sobre todas as informações recebidas
    2. Este NDA é pré-requisito para o contrato de desenvolvimento DEV-2024-001
    3. As obrigações de confidencialidade sobrevivem à terminação deste acordo
    """,
    
    "licensing_agreement": """
    CONTRATO DE LICENCIAMENTO DE SOFTWARE
    
    CONTRATO Nº: LIC-2024-001
    REFERÊNCIA: Licenciamento do Sistema PapperMate
    
    ENTRE:
    PapperMate Technologies Inc., pessoa jurídica de direito privado,
    com sede em San Francisco, CA, Estados Unidos, doravante denominada LICENCIANTE;
    
    E:
    TechCorp Ltda, pessoa jurídica de direito privado,
    inscrita no CNPJ sob o nº 12.345.678/0001-90, doravante denominada LICENCIADA.
    
    TIPO DE CONTRATO: Software Licensing Agreement
    
    OBJETO: Licenciamento de uso do sistema PapperMate para processamento de contratos
    
    VIGÊNCIA: 01/01/2024 a 31/12/2025 (2 anos)
    
    VALOR: US$ 50.000,00 (cinquenta mil dólares americanos) por ano
    
    REFERÊNCIAS A OUTROS CONTRATOS:
    - Contrato de Desenvolvimento: DEV-2024-001
    - Acordo de Confidencialidade: NDA-2024-001
    
    LICENÇA:
    1. O LICENCIANTE concede licença não-exclusiva para uso do software PapperMate
    2. Esta licença está sujeita aos termos do contrato de desenvolvimento DEV-2024-001
    3. O uso do software requer a assinatura do NDA NDA-2024-001
    """
}

def get_sample_contract(contract_type: str = "service_agreement") -> str:
    """Get a sample contract by type"""
    return SAMPLE_CONTRACTS.get(contract_type, SAMPLE_CONTRACTS["service_agreement"])

def list_available_contracts() -> list:
    """List available sample contract types"""
    return list(SAMPLE_CONTRACTS.keys())

def get_contract_summary(contract_type: str) -> dict:
    """Get a summary of contract relationships"""
    summaries = {
        "service_agreement": {
            "contract_id": "DEV-2024-001",
            "contract_name": "Contrato de Prestação de Serviços de Desenvolvimento de Software",
            "contract_type": "Service Agreement Amendment",
            "parent_contracts": ["MAIN-2023-001"],
            "child_contracts": ["SUP-2024-002", "INF-2024-003"],
            "parties": ["TechCorp Ltda", "DataSoft Solutions Ltda"],
            "effective_date": "01/01/2024",
            "expiration_date": "31/12/2024"
        },
        "nda_agreement": {
            "contract_id": "NDA-2024-001",
            "contract_name": "Acordo de Confidencialidade (NDA)",
            "contract_type": "Non-Disclosure Agreement",
            "parent_contracts": [],
            "child_contracts": ["DEV-2024-001", "LIC-2024-001"],
            "parties": ["PapperMate Technologies Inc.", "TechCorp Ltda"],
            "effective_date": "01/01/2024",
            "expiration_date": "31/12/2026"
        },
        "licensing_agreement": {
            "contract_id": "LIC-2024-001",
            "contract_name": "Contrato de Licenciamento de Software",
            "contract_type": "Software Licensing Agreement",
            "parent_contracts": ["DEV-2024-001", "NDA-2024-001"],
            "child_contracts": [],
            "parties": ["PapperMate Technologies Inc.", "TechCorp Ltda"],
            "effective_date": "01/01/2024",
            "expiration_date": "31/12/2025"
        }
    }
    
    return summaries.get(contract_type, {})

if __name__ == "__main__":
    print("📄 Contratos de Exemplo Disponíveis:")
    print("=" * 50)
    
    for contract_type in list_available_contracts():
        summary = get_contract_summary(contract_type)
        print(f"\n🔹 {contract_type.upper().replace('_', ' ')}:")
        print(f"   ID: {summary['contract_id']}")
        print(f"   Nome: {summary['contract_name']}")
        print(f"   Parent: {summary['parent_contracts']}")
        print(f"   Child: {summary['child_contracts']}")
        print(f"   Partes: {', '.join(summary['parties'])}")
        print(f"   Vigência: {summary['effective_date']} a {summary['expiration_date']}")
