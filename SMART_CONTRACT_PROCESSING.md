# Smart Contract Processing — Visão Técnica

## Objetivo
Organizar contratos de forma inteligente e reversível, padronizando nomes, lidando com caracteres especiais e mantendo trilha de auditoria.

## Funcionalidades
- Renomeação inteligente de arquivos
- Tradução/determinação de nomes legíveis quando há caracteres asiáticos
- Organização em pastas por fornecedor
- Log reversível de operações (rename/translate)
- Backup apenas quando há tradução (cópia); renomeações não geram backup

## Convenção de nomes
`[SUPPLIER]_[TYPE]_[START_YEAR]_[END_YEAR]_[CONTRACT_ID].pdf`
- END_YEAR = 2999 quando indeterminado
- `supplier` usa o nome do fornecedor (Unilever/UKCR não é fornecedor)
- `contract_id` extraído do documento

## Fluxo
1. Descoberta de arquivos
2. Decisão: rename vs translate (ASCII vs não-ASCII)
3. Aplicação da convenção
4. Registro em ledger/logs (reversível)

## Logs e Reversão
- Cada operação registra: timestamp, tipo, caminhos original/novo, hash, metadados
- Reversão possível reexecutando mapping de operações

## Próximos passos
- Integração com NLP (Milestone 3): tradução automática, extração de entidades, indexação vetorial
- Interface de anotação (Milestone 4)
