#!/usr/bin/env python3
"""
Test script for OpenAI Python SDK
Demonstrates how to analyze contracts using OpenAI API directly
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import openai
except ImportError:
    print("❌ OpenAI SDK não está instalado. Execute: pip3 install openai")
    sys.exit(1)

def setup_openai_client():
    """Setup OpenAI client with API key"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ OPENAI_API_KEY não configurada")
        print("Configure com: export OPENAI_API_KEY='sua-chave-api'")
        return None
    
    try:
        client = openai.OpenAI(api_key=api_key)
        # Test connection
        models = client.models.list()
        print(f"✅ Conectado à OpenAI. Modelos disponíveis: {len(models.data)}")
        return client
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return None

def analyze_contract_text(client, text, model="gpt-4"):
    """Analyze contract text using OpenAI"""
    
    prompt = f"""
    Analise o seguinte texto de contrato e extraia informações estruturadas em JSON.
    
    Procure por:
    1. Contract ID (identificador único)
    2. Contract Name/Title
    3. Parent contracts (referências a outros contratos)
    4. Child contracts (contratos que referenciam este)
    5. Contract type (tipo de contrato)
    6. Parties involved (partes envolvidas)
    7. Effective date (data de vigência)
    8. Expiration date (data de expiração)
    
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
        "confidence": 0.95
    }}
    
    Texto do contrato:
    {text[:3000]}  # Limitar para eficiência da API
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Você é um especialista em análise de contratos. Extraia informações estruturadas em JSON válido."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Baixa temperatura para resultados consistentes
            max_tokens=1000
        )
        
        content = response.choices[0].message.content
        print(f"✅ Resposta da OpenAI recebida ({len(content)} caracteres)")
        
        # Tentar extrair JSON da resposta
        try:
            # Procurar por JSON na resposta
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content.strip()
            
            # Parse do JSON
            data = json.loads(json_str)
            return data
            
        except json.JSONDecodeError as e:
            print(f"⚠️  Erro ao parsear JSON: {e}")
            print(f"Resposta recebida: {content}")
            return None
            
    except Exception as e:
        print(f"❌ Erro na API: {e}")
        return None

def test_with_sample_contract():
    """Test with a sample contract text"""
    
    sample_contract = """
    CONTRATO DE PRESTAÇÃO DE SERVIÇOS
    
    Contrato Nº: SRV-2024-001
    
    Este contrato é uma emenda ao Contrato Principal Nº MAIN-2023-001 
    entre TechCorp Ltda e DataSoft Solutions, efetivo a partir de 01/01/2024.
    
    TIPO: Emenda ao Contrato de Serviços
    
    PARTES:
    - TechCorp Ltda (Contratante)
    - DataSoft Solutions (Contratada)
    
    VIGÊNCIA: 01/01/2024 a 31/12/2024
    
    REFERÊNCIAS:
    - Contrato Principal: MAIN-2023-001
    - Contrato de Suporte: SUP-2024-002
    """
    
    print("📄 Analisando contrato de exemplo...")
    return sample_contract

def main():
    """Main function"""
    print("🚀 Teste do OpenAI Python SDK para Análise de Contratos")
    print("=" * 60)
    
    # Setup OpenAI client
    client = setup_openai_client()
    if not client:
        return
    
    # Test with sample contract
    sample_text = test_with_sample_contract()
    
    # Analyze contract
    print("\n🔍 Analisando contrato...")
    result = analyze_contract_text(client, sample_text)
    
    if result:
        print("\n✅ Análise concluída!")
        print("📊 Resultados:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Save results
        output_file = "contract_analysis_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Resultados salvos em: {output_file}")
        
    else:
        print("\n❌ Falha na análise")

if __name__ == "__main__":
    main()
