# 🚀 OpenAI Python SDK - Guia de Uso

## 📋 **O que foi configurado**

1. ✅ **OpenAI Python SDK** instalado via pip
2. ✅ **Script de teste** para análise de contratos
3. ✅ **Configuração centralizada** para API
4. ✅ **Integração** com seu projeto PapperMate

## 🔧 **Configuração Inicial**

### **1. Configurar API Key**
```bash
# Adicionar ao seu ~/.zshrc
export OPENAI_API_KEY="sua-chave-api-aqui"
export OPENAI_ORG_ID="seu-org-id-aqui"  # opcional

# Recarregar configurações
source ~/.zshrc
```

### **2. Verificar Instalação**
```bash
# Testar se o SDK está funcionando
python3 src/pappermate/scripts/test_openai_sdk.py
```

## 🎯 **Como Usar**

### **Análise Simples de Contrato**
```python
from pappermate.config.openai_config import get_openai_config
import openai

# Configurar cliente
config = get_openai_config()
client = openai.OpenAI(**config.get_client_config())

# Analisar contrato
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "Analise este contrato..."},
        {"role": "user", "content": "Texto do contrato..."}
    ]
)
```

### **Usar o Serviço Integrado**
```python
from pappermate.services.contract_analyzer import ContractAnalyzer

# Criar analisador
analyzer = ContractAnalyzer(openai_api_key="sua-chave")

# Analisar contrato
analysis = analyzer.analyze_contract("caminho/para/contrato.pdf")
print(f"Contract ID: {analysis.contract_id}")
```

## 📊 **Funcionalidades Disponíveis**

### **Extração Automática de:**
- ✅ Contract ID
- ✅ Contract Name
- ✅ Parent/Child relationships
- ✅ Contract type
- ✅ Parties involved
- ✅ Effective/Expiration dates
- ✅ Confidence scores

### **Formato de Saída:**
```json
{
  "contract_id": "SRV-2024-001",
  "contract_name": "Contrato de Prestação de Serviços",
  "parent_contracts": ["MAIN-2023-001"],
  "child_contracts": ["SUP-2024-002"],
  "contract_type": "Service Agreement Amendment",
  "parties": ["TechCorp Ltda", "DataSoft Solutions"],
  "effective_date": "01/01/2024",
  "expiration_date": "31/12/2024",
  "confidence": 0.95
}
```

## 🧪 **Testes e Validação**

### **Teste com Contrato de Exemplo**
```bash
cd src/pappermate/scripts
python3 test_openai_sdk.py
```

### **Teste com Seu Contrato**
```python
# Modificar o script para usar seu PDF
from pappermate.services.pdf_converter import PDFConverter

converter = PDFConverter()
text = converter.convert_pdf("seu_contrato.pdf").get_text_content()
result = analyze_contract_text(client, text)
```

## 🔍 **Debugging e Troubleshooting**

### **Problemas Comuns:**

1. **API Key não configurada**
   ```bash
   echo $OPENAI_API_KEY  # Deve mostrar sua chave
   ```

2. **Erro de conexão**
   - Verificar internet
   - Verificar se a API key é válida

3. **Limite de tokens**
   - Ajustar `max_tokens` na configuração
   - Truncar texto muito longo

### **Logs e Monitoramento**
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

## 🚀 **Próximos Passos**

1. **Configure sua API Key** da OpenAI
2. **Teste com o script** de exemplo
3. **Integre no seu sistema** de processamento
4. **Refine os prompts** baseado nos resultados
5. **Implemente fallbacks** para casos de erro

## 💡 **Dicas de Uso**

- **Temperature baixa (0.1)** para resultados consistentes
- **Limite o texto** para economizar tokens
- **Use prompts específicos** para seu domínio
- **Valide sempre** os resultados JSON
- **Implemente retry logic** para falhas de API

## 🔗 **Links Úteis**

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [MCP Documentation](https://platform.openai.com/docs/mcp)
