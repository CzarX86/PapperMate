# PapperMate - Manual do Sistema

## 1. Introdução

Bem-vindo ao manual do sistema PapperMate! Este documento tem como objetivo fornecer um guia abrangente sobre como utilizar as funcionalidades do PapperMate, um sistema inteligente de processamento e análise de contratos.

O PapperMate é projetado para automatizar a conversão de documentos (PDFs, EPUBs) para Markdown, extrair entidades-chave, realizar traduções e permitir a busca por similaridade em contratos.

## 2. Funcionalidades Principais

### 2.1. Conversão de Documentos (PDF/EPUB para Markdown)

O PapperMate utiliza o módulo `Marker` para converter documentos PDF e EPUB em Markdown de alta qualidade.

**Scripts Relacionados:**
*   `Marker_PapperMate/convert.py`
*   `Marker_PapperMate/convert_single.py`
*   `Marker_PapperMate/chunk_convert.py`

**Como Usar `convert.py` (Múltiplos Arquivos):**

O script `convert.py` é utilizado para converter múltiplos documentos (PDFs/EPUBs) localizados em uma pasta.

```bash
python -m Marker_PapperMate.convert IN_FOLDER [OPÇÕES]
```

**Argumentos:**
*   `IN_FOLDER`: O caminho para a pasta que contém os documentos a serem convertidos.

**Opções Comuns:**
*   `--output_dir CAMINHO`: Especifica o diretório de saída para os arquivos convertidos. Se não for fornecido, os arquivos serão salvos em um subdiretório `output` dentro da pasta de entrada.
*   `--max_files INTEIRO`: Limita o número de arquivos a serem convertidos. Útil para testes ou processamento parcial.
*   `--skip_existing`: Ignora arquivos que já foram convertidos e cujas saídas já existem no diretório de saída.
*   `--workers INTEIRO`: Define o número de processos de trabalho a serem usados para a conversão paralela. Por padrão, é definido automaticamente.

**Exemplo:**

Para converter todos os PDFs na pasta `meus_documentos` e salvar a saída em `saida_markdown`:

```bash
python -m Marker_PapperMate.convert meus_documentos --output_dir saida_markdown
```

Para converter apenas 5 arquivos e pular os já existentes:

```bash
python -m Marker_PapperMate.convert meus_documentos --max_files 5 --skip_existing
```

**Como Usar `convert_single.py` (Arquivo Único):**

O script `convert_single.py` é utilizado para converter um único documento (PDF/EPUB).

```bash
python -m Marker_PapperMate.convert_single FPATH [OPÇÕES]
```

**Argumentos:**
*   `FPATH`: O caminho completo para o arquivo (PDF ou EPUB) a ser convertido.

**Opções Comuns:**
*   `--output_dir CAMINHO`: Especifica o diretório de saída para o arquivo convertido. Se não for fornecido, o arquivo será salvo em um subdiretório `output` no mesmo diretório do arquivo de entrada.

**Exemplo:**

Para converter um arquivo `documento.pdf` e salvar a saída em `saida_markdown`:

```bash
python -m Marker_PapperMate.convert_single documento.pdf --output_dir saida_markdown
```

**Como Usar `chunk_convert.py` (Conversão em Chunks):**

O script `chunk_convert.py` é utilizado para converter uma pasta de PDFs em chunks, o que é útil para processamento paralelo de grandes volumes de documentos.

```bash
python -m Marker_PapperMate.chunk_convert IN_FOLDER OUT_FOLDER
```

**Argumentos:**
*   `IN_FOLDER`: O caminho para a pasta que contém os PDFs a serem convertidos.
*   `OUT_FOLDER`: O caminho para a pasta onde os arquivos Markdown convertidos serão salvos.

**Exemplo:**

Para converter os PDFs da pasta `documentos_grandes` em chunks e salvar em `saida_chunks`:

```bash
python -m Marker_PapperMate.chunk_convert documentos_grandes saida_chunks
```

**Nota:** Este script utiliza um script shell (`chunk_convert.sh`) internamente para gerenciar o processo de chunking e conversão. Para detalhes avançados ou opções adicionais, consulte o conteúdo de `Marker_PapperMate/marker/scripts/chunk_convert.sh`.



### 2.2. Processamento e Organização de Contratos

O sistema organiza e processa contratos, incluindo renomeação inteligente e gerenciamento de logs.

**Scripts Relacionados:**
*   `src/pappermate/scripts/system_contract_organizer.py`

**Como Usar:**
### 2.2. Processamento e Organização de Contratos

O sistema `system_contract_organizer.py` é a peça central para o processamento inteligente e organização de contratos. Ele automatiza a extração de metadados, renomeação, tradução e organização de arquivos PDF, mantendo um registro completo para auditoria e reversibilidade.

**Scripts Relacionados:**
*   `src/pappermate/scripts/system_contract_organizer.py`

**Funcionalidades Principais:**
*   **Extração de Metadados**: Utiliza a API da OpenAI (GPT-4) para analisar o texto do contrato e extrair informações como ID do contrato, nome, tipo, fornecedor, datas, partes envolvidas, área de negócio e escopo do projeto.
*   **Renomeação Inteligente**: Renomeia os arquivos PDF processados para um formato padronizado (`[FORNECEDOR]_[TIPO]_[ANO_INICIO]_[ANO_FIM]_[ID_CONTRATO].pdf`).
*   **Tradução de Nomes de Arquivos**: Detecta e traduz nomes de arquivos com caracteres não-ASCII para facilitar a organização.
*   **Organização de Pastas**: Move os contratos processados para uma estrutura de pastas organizada por fornecedor.
*   **Logs Reversíveis**: Registra todas as operações realizadas em logs JSON, permitindo a auditoria e a reversão de operações, se necessário.
*   **Relatórios de Resumo**: Gera relatórios de resumo do processamento e um `README.md` na pasta de saída com a estrutura dos arquivos e informações sobre as operações.

**Como Usar:**

Este script é executado diretamente e interage com o usuário via linha de comando.

```bash
python src/pappermate/scripts/system_contract_organizer.py
```

**Passos de Execução:**
1.  **Preparação**: Certifique-se de que seus contratos PDF estejam localizados na pasta `.pdfContracts` (no diretório raiz do projeto).
2.  **Chave de API OpenAI**: O script requer uma chave de API da OpenAI configurada como variável de ambiente (`OPENAI_API_KEY`).
3.  **Execução**: Ao executar o script, ele detectará os PDFs na pasta `.pdfContracts` e perguntará quantos contratos você deseja processar.
4.  **Resultados**: Os contratos processados, logs e relatórios de resumo serão salvos em um novo diretório (`contract_processing_results_YYYYMMDD_HHMMSS`) criado no diretório onde o script foi executado.

**Exemplo de Interação:**

```
🚀 Sistema Inteligente de Processamento de Contratos
======================================================================
📄 Encontrados 5 contratos PDF

🔢 Quantos contratos você quer processar? (máximo: 5)
Digite o número (ou Enter para padrão 5): 3
📊 Processando 3 contratos...
...
🎉 Processamento concluído!
✅ Sucessos: 3
❌ Falhas: 0
📁 Resultados salvos em: contract_processing_results_20231027_103000
```


### 2.3. Tradução Automática

O PapperMate pode traduzir o conteúdo de contratos e nomes de arquivos para o inglês, utilizando APIs de tradução. O sistema é configurável para usar a Google Cloud Translation API e/ou a biblioteca `googletrans` como fallback.

**Módulos Relacionados:**
*   `src/pappermate/processing/translator.py`
*   `src/pappermate/services/file_handler.py` (para tradução de nomes de arquivos)
*   `src/pappermate/config/translation.py` (configuração)

**Configuração:**

As configurações do serviço de tradução são definidas através de variáveis de ambiente:

*   `GOOGLE_TRANSLATE_API_KEY`: Sua chave de API da Google Cloud Translation. **Essencial para usar a API oficial do Google.**
*   `PAPPERMATE_PREFER_GOOGLE_API`: (`true` ou `false`, padrão `true`) Define se o sistema deve preferir a Google Cloud Translation API. Se `false`, tentará `googletrans` primeiro.
*   `PAPPERMATE_ENABLE_GOOGLETRANS_FALLBACK`: (`true` ou `false`, padrão `true`) Se `true`, `googletrans` será usado como fallback caso a Google Cloud Translation API não esteja disponível ou falhe.
*   `PAPPERMATE_ENABLE_CACHING`: (`true` ou `false`, padrão `true`) Ativa ou desativa o cache de traduções para evitar chamadas repetidas à API.
*   `PAPPERMATE_CACHE_DURATION_HOURS`: (inteiro, padrão `24`) Duração em horas para o cache de traduções.

**Como Configurar (Exemplo no Terminal):**

```bash
export GOOGLE_TRANSLATE_API_KEY="sua_chave_aqui"
export PAPPERMATE_PREFER_GOOGLE_API="true"
export PAPPERMATE_ENABLE_CACHING="true"
```

**Como Usar:**

1.  **Tradução de Conteúdo de Contratos (`src/pappermate/processing/translator.py`)**:

    Você pode usar a classe `ContractTranslator` para traduzir o texto de contratos ou arquivos completos para o inglês. Isso é útil para padronizar o idioma antes de outras etapas de processamento de NLP.

    ```python
    from pappermate.processing.translator import ContractTranslator

    # Inicializa o tradutor
    translator = ContractTranslator()

    # Exemplo de tradução de texto
    texto_original = "Este é um exemplo de texto em português."
    resultado_traducao = translator.translate_to_english(texto_original)
    print(f"Texto Original: {resultado_traducao['original_text']}")
    print(f"Texto Traduzido: {resultado_traducao['translated_text']}")
    print(f"Idioma Fonte: {resultado_traducao['source_language']}")

    # Exemplo de tradução de um arquivo completo
    # Certifique-se de que 'caminho/para/seu/contrato.txt' existe
    # resultado_arquivo = translator.translate_contract_file('caminho/para/seu/contrato.txt')
    # print(f"Conteúdo Traduzido do Arquivo: {resultado_arquivo['translated_text'][:200]}...")
    ```

2.  **Tradução de Nomes de Arquivos (Integrado no `system_contract_organizer.py`)**:

    A tradução de nomes de arquivos é automaticamente gerenciada pelo script `system_contract_organizer.py` (descrito na Seção 2.2). Ele utiliza o módulo `src/pappermate/services/file_handler.py` para detectar e traduzir nomes de arquivos com caracteres não-ASCII, garantindo que os arquivos sejam organizados com nomes padronizados e legíveis em inglês.

    Não é necessário chamar diretamente as funções de tradução de nomes de arquivos, pois elas são parte integrante do fluxo de processamento do organizador de contratos.


### 2.4. Extração de Entidades

O sistema PapperMate é capaz de extrair entidades-chave de contratos utilizando modelos avançados de Processamento de Linguagem Natural (NLP), como BERT e RoBERTa, combinados com conhecimento de domínio.

**Módulos Relacionados:**
*   `src/pappermate/processing/entity_extractor.py`

**Como Usar:**

A extração de entidades é realizada pela classe `ContractEntityExtractor`. Esta classe carrega modelos de NLP pré-treinados e aplica diferentes estratégias para identificar informações relevantes em textos de contratos, como fornecedores, datas, tipos de contrato, valores, etc.

```python
from pappermate.processing.entity_extractor import ContractEntityExtractor

# Inicializa o extrator de entidades
# Pode-se desativar BERT ou RoBERTa se não forem necessários
extractor = ContractEntityExtractor(use_bert=True, use_roberta=True)

# Exemplo de texto de contrato
texto_contrato = "Este contrato de serviço com a Empresa X, com início em 01/01/2023 e término em 31/12/2025, no valor de R$ 100.000,00, para o projeto de Transformação Digital."

# Extrai as entidades
resultado_extracao = extractor.extract_entities(texto_contrato, contract_id="CONTRATO_EXEMPLO_001")

print(f"Contrato ID: {resultado_extracao.contract_id}")
print(f"Método de Extração: {resultado_extracao.extraction_method}")
print(f"Confiança Geral: {resultado_extracao.confidence_score:.2f}")
print("\nEntidades Extraídas:")
for entity in resultado_extracao.entities:
    print(f"- Tipo: {entity.entity_type}, Texto: '{entity.text}', Confiança: {entity.confidence:.2f}")
```

**Entidades Suportadas (Exemplos):**
*   `SUPPLIER` (Fornecedor)
*   `CUSTOMER` (Cliente)
*   `CONTRACT_ID` (ID do Contrato)
*   `CONTRACT_TYPE` (Tipo de Contrato)
*   `START_DATE` (Data de Início)
*   `END_DATE` (Data de Término)
*   `AMOUNT` (Valor)
*   `CURRENCY` (Moeda)
*   `SERVICE_TYPE` (Tipo de Serviço)
*   `BUSINESS_AREA` (Área de Negócio)
*   `PROJECT_SCOPE` (Escopo do Projeto)

**Nota:** A eficácia da extração depende da qualidade dos modelos carregados e da clareza do texto do contrato. Certifique-se de ter as dependências de `transformers` e `sentence-transformers` instaladas (`pip install transformers torch sentence-transformers`).

### 2.5. Busca por Similaridade

O PapperMate é capaz de realizar buscas por similaridade em textos de contratos, utilizando embeddings de sentenças. Esta funcionalidade é integrada ao processo de extração de entidades, especificamente na detecção de entidades baseada em conhecimento de domínio.

**Módulos Relacionados:**
*   `src/pappermate/processing/entity_extractor.py` (para geração de embeddings e cálculo de similaridade)

**Como Funciona:**

A classe `ContractEntityExtractor` (descrita na Seção 2.4) utiliza internamente modelos de `sentence-transformers` para converter textos em representações numéricas (embeddings). Esses embeddings permitem que o sistema compare a semelhança semântica entre diferentes trechos de texto.

Durante a extração de entidades, o extrator busca por padrões de contrato predefinidos (como tipos de contrato ou áreas de negócio) e utiliza a busca por similaridade para encontrar trechos no documento que se assemelham a esses padrões. Isso ajuda a identificar entidades mesmo que não sejam explicitamente reconhecidas pelos modelos BERT/RoBERTa.

**Como Usar (Integrado à Extração de Entidades):**

Você não chama diretamente a função de busca por similaridade. Ela é ativada automaticamente quando você utiliza o `ContractEntityExtractor` para processar um texto. O extrator tentará identificar entidades baseadas em conhecimento de domínio, que por sua vez utilizam a busca por similaridade.

```python
from pappermate.processing.entity_extractor import ContractEntityExtractor

# Inicializa o extrator de entidades (que inclui a funcionalidade de busca por similaridade)
extractor = ContractEntityExtractor()

# Texto do contrato para análise
texto_contrato = "Este é um acordo de serviço mestre para consultoria em tecnologia da informação."

# Extrai as entidades - a busca por similaridade ocorre internamente aqui
resultado_extracao = extractor.extract_entities(texto_contrato)

print("Entidades Extraídas (incluindo as encontradas por similaridade):")
for entity in resultado_extracao.entities:
    print(f"- Tipo: {entity.entity_type}, Texto: '{entity.text}', Fonte: {entity.metadata.get('model', 'N/A')}")
```

**Benefícios:**
*   **Robustez**: Ajuda a identificar entidades mesmo em variações textuais ou quando os modelos de NER não as reconhecem diretamente.
*   **Conhecimento de Domínio**: Permite incorporar padrões específicos de contratos para uma extração mais precisa.


## 3. Configuração

Para o funcionamento adequado do PapperMate, algumas configurações são necessárias, principalmente relacionadas a chaves de API e variáveis de ambiente. É altamente recomendável configurar essas variáveis no seu ambiente de desenvolvimento (por exemplo, no seu arquivo `.bashrc`, `.zshrc` ou `.env`).

### 3.1. Chave de API OpenAI

O PapperMate utiliza a API da OpenAI para análise e extração de metadados de contratos. Você precisa de uma chave de API válida.

*   **Variável de Ambiente**: `OPENAI_API_KEY`
*   **Como Obter**: Acesse o site da OpenAI e gere sua chave de API.
*   **Exemplo de Configuração (Terminal)**:

    ```bash
    export OPENAI_API_KEY="sua_chave_openai_aqui"
    ```

### 3.2. Configurações do Serviço de Tradução

Conforme detalhado na Seção 2.3, o serviço de tradução pode ser configurado através das seguintes variáveis de ambiente:

*   `GOOGLE_TRANSLATE_API_KEY`: Sua chave de API da Google Cloud Translation. **Essencial para usar a API oficial do Google.**
*   `PAPPERMATE_PREFER_GOOGLE_API`: (`true` ou `false`, padrão `true`) Define se o sistema deve preferir a Google Cloud Translation API.
*   `PAPPERMATE_ENABLE_GOOGLETRANS_FALLBACK`: (`true` ou `false`, padrão `true`) Se `true`, `googletrans` será usado como fallback.
*   `PAPPERMATE_ENABLE_CACHING`: (`true` ou `false`, padrão `true`) Ativa ou desativa o cache de traduções.
*   `PAPPERMATE_CACHE_DURATION_HOURS`: (inteiro, padrão `24`) Duração em horas para o cache de traduções.

**Exemplo de Configuração (Terminal)**:

```bash
export GOOGLE_TRANSLATE_API_KEY="sua_chave_google_translate_aqui"
export PAPPERMATE_PREFER_GOOGLE_API="true"
export PAPPERMATE_ENABLE_CACHING="true"
```

### 3.3. Instalação de Dependências

Para garantir que todas as funcionalidades do PapperMate funcionem corretamente, você precisará instalar as dependências Python necessárias. O projeto utiliza `Poetry` para gerenciamento de dependências.

No diretório raiz do projeto (`/Users/juliocezar/Dev/work/PapperMate`), execute:

```bash
poetry install
```

Além disso, para os modelos de NLP e Sentence Transformers, certifique-se de que as bibliotecas `transformers`, `torch` e `sentence-transformers` estejam instaladas:

```bash
pip install transformers torch sentence-transformers
```

Para a funcionalidade de tradução, se você planeja usar `googletrans` (mesmo como fallback), pode ser necessário instalá-lo:

```bash
pip install googletrans==4.0.0rc1
```


## 4. Solução de Problemas

(Esta seção será preenchida com problemas comuns e suas soluções.)

## 5. Contribuição

(Esta seção conterá informações sobre como contribuir para o projeto.)

---
*Este manual está em constante atualização. Última atualização: 20 de agosto de 2025*
