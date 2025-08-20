# PapperMate — Roadmap

## Milestones
1. Infraestrutura Base — concluído
2. Exploração de Dados — concluído
3. NLP Infrastructure — em andamento
   - Tradução automática (cache)
   - NER com BERT/RoBERTa
   - Vetor semântico (ChromaDB/FAISS)
4. Human Interface & Validation — planejado
5. Custom Model Development — planejado
6. Production Integration — planejado

## Próximos Sprints (M3)
- Sprint 7: Translation & Language Processing
- Sprint 8: Entity Recognition Foundation
- Sprint 9: Vector Storage & Similarity

## Entregáveis de M3
- Pipeline unificado (translate → extract → embed → index)
- JSON/CSV/JSONL rotulável
- Índice vetorial persistente
- Testes unitários e integração (>=80% cobertura M3)

## Observações
- Evitar versionar segredos; push protection ativo
- `.pdfContracts` necessária para alguns testes de integração
