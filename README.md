# 🚀 PapperMate

**AI-powered contract entity extraction system using Marker PDF conversion and local NLP processing**

## 🎯 **MILESTONE 1 COMPLETADO** ✅

**Status:** Conversor de documentos funcional com conversão estável de PDF para Markdown/JSON

### **🔧 Funcionalidades do MS1:**
- ✅ **Conversão PDF → Markdown** usando Marker
- ✅ **Conversão PDF → JSON** usando Marker  
- ✅ **Conversão PDF → Ambos formatos** simultaneamente
- ✅ **Tratamento robusto de erros** com fallbacks
- ✅ **Configuração `skip_tables`** para estabilidade
- ✅ **Logging detalhado** e métricas de conversão
- ✅ **Testes de integração** com PDFs reais

---

## 🚀 **INSTALAÇÃO E CONFIGURAÇÃO**

### **Pré-requisitos:**
- Python 3.12+
- Poetry (gerenciador de dependências)

### **Instalação:**
```bash
# Clone o repositório
git clone <repository-url>
cd PapperMate

# Instale as dependências
poetry install

# Ative o ambiente virtual
poetry shell
```

---

## 📖 **COMO USAR**

### **Conversão Básica:**
```python
from pappermate.services.pdf_converter import PDFConverterService

# Criar serviço (skip_tables=True por padrão para estabilidade)
converter = PDFConverterService()

# Converter PDF para Markdown
result = converter.convert_pdf_to_markdown("documento.pdf")
if result.success:
    print(f"✅ Conversão bem-sucedida: {len(result.markdown_content)} caracteres")
    print(f"⏱️ Tempo: {result.processing_time:.2f}s")
else:
    print(f"❌ Falha: {result.error_message}")
```

### **Conversão para JSON:**
```python
# Converter PDF para JSON
result = converter.convert_pdf_to_json("documento.pdf")
if result.success:
    print(f"✅ JSON gerado: {len(str(result.json_content))} caracteres")
```

### **Conversão para Ambos Formatos:**
```python
# Converter para ambos formatos
result = converter.convert_pdf_to_both("documento.pdf")
if result.success:
    print(f"✅ Markdown: {len(result.markdown_content)} caracteres")
    print(f"✅ JSON: {len(str(result.json_content))} caracteres")
```

---

## ⚙️ **CONFIGURAÇÃO `skip_tables`**

### **Por que `skip_tables`?**
- **MS1:** `skip_tables=True` por padrão para estabilidade
- **Problema:** Bug no Marker com tabelas vazias (`stack expects a non-empty TensorList`)
- **Solução:** Pular processamento de tabelas até correção upstream

### **Como configurar:**

#### **1. Via Construtor (maior prioridade):**
```python
# Forçar processamento de tabelas (pode falhar)
converter = PDFConverterService(skip_tables=False)

# Desabilitar processamento de tabelas (padrão, estável)
converter = PDFConverterService(skip_tables=True)
```

#### **2. Via Variável de Ambiente:**
```bash
# Habilitar tabelas (pode falhar)
export PAPPERMATE_SKIP_TABLES=0

# Desabilitar tabelas (padrão, estável)
export PAPPERMATE_SKIP_TABLES=1

# Ou
export PAPPERMATE_SKIP_TABLES=true
```

#### **3. Valores aceitos:**
- **`1`, `true`, `yes`** → Desabilita tabelas (padrão, estável)
- **`0`, `false`, `no`** → Habilita tabelas (pode falhar)

---

## 🧪 **TESTES**

### **Testes Unitários (rápidos):**
```bash
# Executar todos os testes unitários
poetry run pytest tests/ -v

# Executar testes específicos
poetry run pytest tests/test_models.py -v
poetry run pytest tests/test_pdf_converter.py -v
```

### **Testes de Integração (lentos, com PDFs reais):**
```bash
# Executar testes de integração (usam PDFs de pdfContracts/)
poetry run pytest tests/test_integration_pdf.py -v -m slow

# Executar apenas testes de integração
poetry run pytest -m slow -v
```

### **Cobertura de Testes:**
```bash
# Executar com cobertura
poetry run pytest --cov=src/pappermate tests/ -v

# Gerar relatório HTML
poetry run pytest --cov=src/pappermate --cov-report=html tests/
# Abrir htmlcov/index.html no navegador
```

---

## 📁 **ESTRUTURA DO PROJETO**

```
PapperMate/
├── src/pappermate/           # Código fonte principal
│   ├── models/               # Modelos de dados (Document, Contract, etc.)
│   ├── services/             # Serviços (PDFConverter, etc.)
│   ├── api/                  # API REST (futuro)
│   ├── core/                 # Lógica de negócio (futuro)
│   └── utils/                # Utilitários (futuro)
├── tests/                    # Testes
│   ├── test_models.py        # Testes dos modelos
│   ├── test_pdf_converter.py # Testes do conversor
│   └── test_integration_pdf.py # Testes de integração
├── pdfContracts/             # PDFs de teste
├── Marker_PapperMate/        # Fork do Marker (submódulo)
└── pyproject.toml           # Configuração Poetry
```

---

## 🔧 **CONFIGURAÇÃO AVANÇADA**

### **Variáveis de Ambiente:**
```bash
# Configuração de tabelas
export PAPPERMATE_SKIP_TABLES=1

# Configuração do Marker (GPU/CPU)
export PYTORCH_ENABLE_MPS_FALLBACK=1
export CUDA_VISIBLE_DEVICES=""
export USE_MPS=0
```

### **Diretórios de Saída:**
```python
# Personalizar diretório de saída
converter = PDFConverterService(output_dir="meus_documentos")

# Estrutura criada automaticamente:
# meus_documentos/
# ├── markdown/               # Arquivos .md
# └── json/                   # Arquivos .json
```

---

## 📊 **MÉTRICAS E LOGS**

### **Estatísticas de Conversão:**
```python
stats = converter.get_conversion_stats()
print(f"📊 Total Markdown: {stats['total_markdown_files']}")
print(f"📊 Total JSON: {stats['total_json_files']}")
print(f"🔧 Skip Tables: {stats['skip_tables']}")
print(f"✅ Marker Inicializado: {stats['marker_initialized']}")
```

### **Logs Detalhados:**
- ✅ Inicialização do Marker
- 🔄 Progresso da conversão
- ⚠️ Fallbacks e warnings
- ❌ Erros detalhados
- ⏱️ Tempos de processamento

---

## 🚨 **PROBLEMAS CONHECIDOS**

### **1. Bug do Marker com Tabelas Vazias:**
- **Erro:** `stack expects a non-empty TensorList`
- **Causa:** Tabelas sem linhas de texto quebram o modelo Surya
- **Solução MS1:** `skip_tables=True` (padrão)
- **Solução Futura:** Correção upstream no Marker

### **2. Performance MPS (GPU Apple):**
- **Problema:** Uso automático de GPU MPS pode causar travamentos
- **Solução:** Forçamos uso de CPU via variáveis de ambiente

---

## 🔮 **ROADMAP**

### **MS1 (ATUAL):** ✅
- [x] Conversor de documentos funcional
- [x] Estrutura de dados básica
- [x] Pipeline de processamento inicial

### **MS2 (PRÓXIMO):**
- [ ] Correção upstream do bug de tabelas no Marker
- [ ] Reativação de `skip_tables=False` por padrão
- [ ] Extração de entidades contratuais
- [ ] Interface de anotação

### **MS3:**
- [ ] Gerenciamento de hierarquias entre contratos
- [ ] Detecção de duplicatas
- [ ] Aprendizado incremental

---

## 🤝 **CONTRIBUIÇÃO**

### **Para o PapperMate:**
1. Fork o repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Abra um Pull Request

### **Para o Marker (correção de tabelas):**
1. Fork do `datalab-to/marker`
2. Aplique correções para tabelas vazias
3. Abra PR upstream
4. Atualize submódulo no PapperMate

---

## 📄 **LICENÇA**

MIT License - veja [LICENSE](LICENSE) para detalhes.

---

## 🆘 **SUPORTE**

### **Problemas Comuns:**
1. **Marker não inicializa:** Verifique dependências Python
2. **Conversão falha:** Verifique se `skip_tables=True`
3. **Testes lentos:** Use `-m slow` apenas quando necessário

### **Logs de Debug:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

**🎉 MS1 Completo! Sistema estável de conversão PDF funcionando!**




