# 🌐 Configuração de Tradução - PapperMate

Este documento explica como configurar os serviços de tradução para nomes de arquivos com caracteres asiáticos.

## 🚀 **Sistema Inteligente de Fallback**

O PapperMate implementa um sistema robusto de tradução com:

### **1. Google Translate API (Recomendado)**
- ✅ **Mais preciso** e confiável
- ✅ **Suporte oficial** do Google
- ✅ **Rate limits** altos
- ❌ **Custo** por 1M de caracteres

### **2. Googletrans (Fallback Gratuito)**
- ✅ **Sem custo** de API
- ✅ **Funciona offline** (quando disponível)
- ❌ **Menos confiável** e pode quebrar

### **3. Sistema de Fila de Reprocessamento**
- ✅ **Arquivos problemáticos** são reservados automaticamente
- ✅ **Tentativas automáticas** de retry com delay configurável
- ✅ **Status tracking** completo para cada arquivo
- ✅ **Relatórios detalhados** de problemas e soluções

## 🔑 **Configuração do Google Translate API**

### **Passo 1: Obter API Key**
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative a API "Cloud Translation API"
4. Vá para "Credentials" → "Create Credentials" → "API Key"
5. Copie a chave gerada

### **Passo 2: Configurar Variável de Ambiente**
```bash
# Temporário (apenas para esta sessão)
export GOOGLE_TRANSLATE_API_KEY="sua-chave-aqui"

# Permanente (adicionar ao ~/.zshrc)
echo 'export GOOGLE_TRANSLATE_API_KEY="sua-chave-aqui"' >> ~/.zshrc
source ~/.zshrc
```

### **Passo 3: Verificar Configuração**
```bash
poetry run python -c "
from src.pappermate.config.translation import setup_translation_environment
config = setup_translation_environment()
print('Config loaded:', config.google_translate_api_key is not None)
"
```

## 💰 **Custos do Google Translate API**

### **Tier Gratuito:**
- **500K caracteres/mês** gratuitos
- **$20 por 1M** caracteres adicionais

### **Para Nomes de Arquivos:**
- **1 nome típico** = ~50 caracteres
- **Tier gratuito** = ~10.000 nomes/mês
- **Custo real** = praticamente zero para uso pessoal

## 🔧 **Configurações Avançadas**

### **Variáveis de Ambiente Disponíveis:**
```bash
# Configuração principal
export GOOGLE_TRANSLATE_API_KEY="sua-chave"

# Preferências de serviço
export PAPPERMATE_PREFER_GOOGLE_API="true"
export PAPPERMATE_ENABLE_GOOGLETRANS_FALLBACK="true"

# Cache e performance
export PAPPERMATE_ENABLE_CACHING="true"
export PAPPERMATE_CACHE_DURATION_HOURS="24"
```

### **Exemplo de Uso:**
```python
from src.pappermate.services.file_handler import FileHandler

# Com Google API
handler = FileHandler(use_google_api=True)

# Sem Google API (apenas fallback)
handler = FileHandler(use_google_api=False)

# Com chave personalizada
handler = FileHandler(google_api_key="minha-chave")

# Configuração de retry
handler = FileHandler(
    max_retries=3,           # Máximo de tentativas
    retry_delay_hours=24     # Delay entre tentativas
)
```

## 📊 **Sistema de Status e Reprocessamento**

### **Status dos Arquivos:**
- **`pending`** - Aguardando processamento
- **`success`** - Traduzido com sucesso
- **`failed`** - Falhou na tradução
- **`retry_ready`** - Pronto para nova tentativa
- **`skipped`** - Máximo de tentativas atingido

### **Monitoramento de Status:**
```python
# Ver status geral
status = handler.get_reprocessing_status()
print(f"Total: {status['total_items']}")
print(f"Falharam: {status['failed']}")
print(f"Prontos para retry: {status['retry_ready']}")

# Ver detalhes de cada arquivo
for item in status['items']:
    print(f"Arquivo: {item['original_filename']}")
    print(f"Status: {item['status']}")
    print(f"Erro: {item['error_message']}")
    print(f"Próximo retry: {item['retry_after']}")
```

### **Reprocessamento Automático:**
```python
# Tentar reprocessar arquivos falhados
results = handler.retry_failed_translations()
print(f"Sucessos: {results['successful']}")
print(f"Ainda falharam: {results['still_failed']}")
```

### **Relatório de Status:**
```python
# Imprimir resumo completo
handler.print_reprocessing_summary()
```

## 🧪 **Testando a Tradução**

### **Teste Básico:**
```bash
poetry run python -c "
from src.pappermate.services.file_handler import FileHandler
fh = FileHandler()
result, status, error = fh.sanitize_filename('【御見積書】_システム運用サポート.pdf')
print('Original: 【御見積書】_システム運用サポート.pdf')
print('Translated:', result)
print('Status:', status)
if error: print('Error:', error)
"
```

### **Teste Completo do Sistema:**
```bash
# Executar teste completo
poetry run python test_translation_system.py
```

### **Teste com Diferentes Idiomas:**
```bash
# Japonês
poetry run python -c "
from src.pappermate.services.file_handler import FileHandler
fh = FileHandler()
result, status, error = fh.sanitize_filename('見積書_システム.pdf')
print('Result:', result, 'Status:', status)
"

# Chinês
poetry run python -c "
from src.pappermate.services.file_handler import FileHandler
fh = FileHandler()
result, status, error = fh.sanitize_filename('框架合同_发票.pdf')
print('Result:', result, 'Status:', status)
"

# Coreano
poetry run python -c "
from src.pappermate.services.file_handler import FileHandler
fh = FileHandler()
result, status, error = fh.sanitize_filename('서비스_계약서.pdf')
print('Result:', result, 'Status:', status)
"
```

## 📋 **Estrutura de Diretórios**

```
reprocessing_queue/
├── pending/           # Arquivos aguardando processamento
├── failed/            # Arquivos que falharam
├── retry_ready/       # Arquivos prontos para retry
└── translation_queue.json  # Status completo em JSON
```

## 🚨 **Solução de Problemas**

### **Erro: "Google Translate API failed"**
- ✅ Verifique se a API key está configurada
- ✅ Verifique se a API está ativada no Google Cloud
- ✅ Verifique se há créditos disponíveis
- ✅ **Arquivo será reservado** para reprocessamento futuro

### **Erro: "No translation service available"**
- ✅ Instale as dependências: `poetry install`
- ✅ Configure uma API key ou use o fallback
- ✅ Verifique as variáveis de ambiente
- ✅ **Arquivo será reservado** para reprocessamento futuro

### **Arquivos na Fila de Reprocessamento:**
```bash
# Ver status da fila
poetry run python -c "
from src.pappermate.services.file_handler import FileHandler
fh = FileHandler()
fh.print_reprocessing_summary()
"

# Tentar reprocessar
poetry run python -c "
from src.pappermate.services.file_handler import FileHandler
fh = FileHandler()
results = fh.retry_failed_translations()
print('Retry results:', results)
"
```

### **Fallback para Mapeamento Manual:**
Se todos os serviços falharem, o sistema usa mapeamento manual básico:
```python
fallback_mappings = {
    '【': '[', '】': ']', '（': '(', '）': ')',
    '：': ':', '　': ' ', '、': ',', '。': '.',
    'ー': '-', '・': '.', '～': '~',
}
```

## 🔄 **Fluxo de Tradução Inteligente**

```
1. Arquivo com caracteres especiais
   ↓
2. Tentar Google Translate API
   ↓
3. Se falhar → Tentar Googletrans
   ↓
4. Se falhar → Aplicar mapeamento manual
   ↓
5. Adicionar à fila de reprocessamento
   ↓
6. Agendar retry automático
   ↓
7. Notificar usuário do status
```

## 📚 **Recursos Adicionais**

- [Google Cloud Translation API Docs](https://cloud.google.com/translate/docs)
- [Googletrans Library](https://pypi.org/project/googletrans/)
- [PapperMate Documentation](../README.md)

## 🤝 **Suporte**

Para problemas ou dúvidas:
1. Verifique este documento
2. Consulte os logs de erro
3. Verifique a fila de reprocessamento
4. Abra uma issue no repositório
5. Entre em contato com a equipe
