#!/usr/bin/env python3
"""
Advanced contract analysis test using OpenAI
Tests the system with multiple realistic contract examples
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import openai
    from sample_contracts import get_sample_contract, list_available_contracts, get_contract_summary
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
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

def analyze_contract_advanced(client, contract_text, contract_type, model="gpt-4"):
    """Advanced contract analysis using OpenAI"""
    
    prompt = f"""
    Analise o seguinte contrato de {contract_type} e extraia informações estruturadas em JSON.
    
    Procure por:
    1. Contract ID (identificador único)
    2. Contract Name/Title
    3. Parent contracts (referências a outros contratos)
    4. Child contracts (contratos que referenciam este)
    5. Contract type (tipo de contrato)
    6. Parties involved (partes envolvidas)
    7. Effective date (data de vigência)
    8. Expiration date (data de expiração)
    9. Contract value (valor do contrato)
    10. Key terms (termos importantes)
    11. Relationship type (tipo de relacionamento)
    12. Confidence score (confiança na extração)
    
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
        "confidence": 0.95,
        "analysis_notes": "observações da análise"
    }}
    
    Texto do contrato:
    {contract_text[:4000]}
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Você é um especialista em análise de contratos jurídicos. Extraia informações estruturadas em JSON válido com alta precisão."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content
        print(f"✅ Resposta recebida ({len(content)} caracteres)")
        
        # Parse JSON response
        try:
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content.strip()
            
            data = json.loads(json_str)
            return data
            
        except json.JSONDecodeError as e:
            print(f"⚠️  Erro ao parsear JSON: {e}")
            print(f"Resposta recebida: {content}")
            return None
            
    except Exception as e:
        print(f"❌ Erro na API: {e}")
        return None

def compare_analysis_with_expected(analysis_result, expected_summary):
    """Compare OpenAI analysis with expected results"""
    print("\n🔍 Comparando Análise com Resultados Esperados:")
    print("-" * 50)
    
    comparison = {}
    
    # Key fields to compare
    key_fields = [
        'contract_id', 'contract_name', 'contract_type', 
        'parent_contracts', 'child_contracts', 'parties'
    ]
    
    for field in key_fields:
        expected = expected_summary.get(field, [])
        actual = analysis_result.get(field, [])
        
        if field in ['parent_contracts', 'child_contracts', 'parties']:
            # For list fields, check if all expected items are present
            if isinstance(expected, list) and isinstance(actual, list):
                matches = all(item in actual for item in expected)
                comparison[field] = {
                    'expected': expected,
                    'actual': actual,
                    'match': matches,
                    'score': len([x for x in expected if x in actual]) / len(expected) if expected else 1.0
                }
        else:
            # For string fields, check exact match
            comparison[field] = {
                'expected': expected,
                'actual': actual,
                'match': expected == actual,
                'score': 1.0 if expected == actual else 0.0
            }
    
    # Print comparison results
    total_score = 0
    total_fields = len(key_fields)
    
    for field, result in comparison.items():
        status = "✅" if result['match'] else "❌"
        score = result['score']
        total_score += score
        
        print(f"{status} {field}:")
        print(f"   Esperado: {result['expected']}")
        print(f"   Obtido:   {result['actual']}")
        print(f"   Score:    {score:.2f}")
        print()
    
    overall_score = total_score / total_fields
    print(f"📊 Score Geral: {overall_score:.2f} ({overall_score*100:.1f}%)")
    
    return overall_score

def run_comprehensive_test():
    """Run comprehensive test with all sample contracts"""
    print("🚀 Teste Avançado de Análise de Contratos com OpenAI")
    print("=" * 70)
    
    # Setup OpenAI client
    client = setup_openai_client()
    if not client:
        return
    
    # Get available contract types
    contract_types = list_available_contracts()
    print(f"\n📄 Contratos disponíveis para teste: {len(contract_types)}")
    
    # Results storage
    all_results = {}
    overall_scores = []
    
    # Test each contract type
    for contract_type in contract_types:
        print(f"\n{'='*60}")
        print(f"🔍 Analisando: {contract_type.upper().replace('_', ' ')}")
        print(f"{'='*60}")
        
        # Get sample contract
        contract_text = get_sample_contract(contract_type)
        expected_summary = get_contract_summary(contract_type)
        
        print(f"📋 Contrato ID esperado: {expected_summary.get('contract_id', 'N/A')}")
        print(f"📋 Tipo esperado: {expected_summary.get('contract_type', 'N/A')}")
        
        # Analyze with OpenAI
        print("\n🤖 Analisando com OpenAI...")
        analysis_result = analyze_contract_advanced(client, contract_text, contract_type)
        
        if analysis_result:
            print("\n📊 Resultados da Análise:")
            print(json.dumps(analysis_result, indent=2, ensure_ascii=False))
            
            # Compare with expected results
            score = compare_analysis_with_expected(analysis_result, expected_summary)
            overall_scores.append(score)
            
            # Store results
            all_results[contract_type] = {
                'analysis': analysis_result,
                'expected': expected_summary,
                'score': score
            }
            
        else:
            print("❌ Falha na análise")
            overall_scores.append(0.0)
    
    # Generate comprehensive report
    print(f"\n{'='*70}")
    print("📈 RELATÓRIO COMPLETO DE TESTES")
    print(f"{'='*70}")
    
    print(f"\n📊 Estatísticas Gerais:")
    print(f"   Total de contratos testados: {len(contract_types)}")
    print(f"   Score médio: {sum(overall_scores)/len(overall_scores):.2f}")
    print(f"   Melhor score: {max(overall_scores):.2f}")
    print(f"   Pior score: {min(overall_scores):.2f}")
    
    print(f"\n🏆 Ranking por Performance:")
    sorted_results = sorted(all_results.items(), key=lambda x: x[1]['score'], reverse=True)
    
    for i, (contract_type, result) in enumerate(sorted_results, 1):
        score = result['score']
        status = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}º"
        print(f"   {status} {contract_type}: {score:.2f} ({score*100:.1f}%)")
    
    # Save comprehensive results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"comprehensive_analysis_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'overall_score': sum(overall_scores)/len(overall_scores),
            'contract_results': all_results,
            'summary': {
                'total_contracts': len(contract_types),
                'average_score': sum(overall_scores)/len(overall_scores),
                'best_score': max(overall_scores),
                'worst_score': min(overall_scores)
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Relatório completo salvo em: {output_file}")
    
    return all_results

if __name__ == "__main__":
    run_comprehensive_test()
