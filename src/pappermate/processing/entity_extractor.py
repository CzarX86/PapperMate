"""
Sistema de extração de entidades usando BERT/RoBERTa
Sem regex - apenas ML e NLP
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class Entity:
    """Entidade extraída do contrato"""
    text: str
    entity_type: str
    start_pos: int
    end_pos: int
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class ContractEntities:
    """Entidades extraídas de um contrato"""
    contract_id: str
    entities: List[Entity]
    extraction_method: str
    confidence_score: float
    processing_time: float

class ContractEntityExtractor:
    """Extrator de entidades usando BERT/RoBERTa"""
    
    def __init__(self, use_bert: bool = True, use_roberta: bool = True):
        self.use_bert = use_bert
        self.use_roberta = use_roberta
        self.models = {}
        self.entity_types = [
            'SUPPLIER', 'CUSTOMER', 'CONTRACT_ID', 'CONTRACT_TYPE',
            'START_DATE', 'END_DATE', 'AMOUNT', 'CURRENCY',
            'SERVICE_TYPE', 'BUSINESS_AREA', 'PROJECT_SCOPE',
            'SIGNATURE_DATE', 'EFFECTIVE_DATE', 'EXPIRATION_DATE'
        ]
        
        self._load_models()
    
    def _load_models(self):
        """Carrega modelos de NLP"""
        try:
            # Load BERT for NER
            from transformers import AutoTokenizer, AutoModelForTokenClassification
            from transformers import pipeline
            
            # Contract-specific NER model (fine-tuned)
            try:
                self.bert_ner = pipeline(
                    "ner",
                    model="microsoft/layoutlm-base-uncased",  # Good for documents
                    aggregation_strategy="simple"
                )
                logger.info("✅ BERT NER carregado: microsoft/layoutlm-base-uncased")
            except Exception as e:
                logger.warning(f"BERT NER não disponível: {e}")
                self.bert_ner = None
            
            # RoBERTa for classification
            try:
                self.roberta_classifier = pipeline(
                    "text-classification",
                    model="roberta-base"
                )
                logger.info("✅ RoBERTa classifier carregado")
            except Exception as e:
                logger.warning(f"RoBERTa não disponível: {e}")
                self.roberta_classifier = None
            
            # Sentence transformers for similarity
            try:
                from sentence_transformers import SentenceTransformer
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ Sentence Transformer carregado")
            except Exception as e:
                logger.warning(f"Sentence Transformer não disponível: {e}")
                self.sentence_model = None
                
        except ImportError as e:
            logger.error(f"❌ Dependências não disponíveis: {e}")
            logger.info("Instale: pip install transformers torch sentence-transformers")
    
    def extract_entities(self, text: str, contract_id: str = "unknown") -> ContractEntities:
        """Extrai entidades do texto usando múltiplos modelos"""
        import time
        start_time = time.time()
        
        entities = []
        
        # 1. BERT NER for entity recognition
        if self.bert_ner:
            try:
                bert_entities = self._extract_with_bert(text)
                entities.extend(bert_entities)
                logger.info(f"🧠 BERT extraiu {len(bert_entities)} entidades")
            except Exception as e:
                logger.warning(f"BERT NER falhou: {e}")
        
        # 2. RoBERTa for classification
        if self.roberta_classifier:
            try:
                roberta_entities = self._extract_with_roberta(text)
                entities.extend(roberta_entities)
                logger.info(f"🤖 RoBERTa extraiu {len(roberta_entities)} entidades")
            except Exception as e:
                logger.warning(f"RoBERTa falhou: {e}")
        
        # 3. Domain-specific entity detection
        domain_entities = self._extract_domain_entities(text)
        entities.extend(domain_entities)
        logger.info(f"🎯 Domain knowledge extraiu {len(domain_entities)} entidades")
        
        # 4. Deduplicate and merge entities
        final_entities = self._deduplicate_entities(entities)
        
        # 5. Calculate confidence
        confidence_score = self._calculate_confidence(final_entities)
        
        processing_time = time.time() - start_time
        
        return ContractEntities(
            contract_id=contract_id,
            entities=final_entities,
            extraction_method="bert_roberta_domain",
            confidence_score=confidence_score,
            processing_time=processing_time
        )
    
    def _extract_with_bert(self, text: str) -> List[Entity]:
        """Extrai entidades usando BERT NER"""
        entities = []
        
        try:
            # Process text in chunks (BERT has token limits)
            chunks = self._chunk_text(text, max_length=512)
            
            for chunk_start, chunk_text in chunks:
                results = self.bert_ner(chunk_text)
                
                for result in results:
                    entity_type = self._map_bert_entity(result['entity_group'])
                    if entity_type:
                        entity = Entity(
                            text=result['word'],
                            entity_type=entity_type,
                            start_pos=chunk_start + result['start'],
                            end_pos=chunk_start + result['end'],
                            confidence=result['score'],
                            metadata={'model': 'bert', 'chunk': True}
                        )
                        entities.append(entity)
                        
        except Exception as e:
            logger.error(f"Erro no BERT NER: {e}")
        
        return entities
    
    def _extract_with_roberta(self, text: str) -> List[Entity]:
        """Extrai entidades usando RoBERTa classification"""
        entities = []
        
        try:
            # Classify text segments for contract-specific patterns
            segments = self._segment_contract_text(text)
            
            for segment, segment_type in segments:
                if segment_type in ['amount', 'date', 'identifier']:
                    # Use RoBERTa to classify the segment
                    classification = self.roberta_classifier(segment)
                    
                    if classification and classification[0]['score'] > 0.7:
                        entity_type = self._map_roberta_entity(segment_type, classification[0]['label'])
                        if entity_type:
                            entity = Entity(
                                text=segment,
                                entity_type=entity_type,
                                start_pos=text.find(segment),
                                end_pos=text.find(segment) + len(segment),
                                confidence=classification[0]['score'],
                                metadata={'model': 'roberta', 'segment_type': segment_type}
                            )
                            entities.append(entity)
                            
        except Exception as e:
            logger.error(f"Erro no RoBERTa: {e}")
        
        return entities
    
    def _extract_domain_entities(self, text: str) -> List[Entity]:
        """Extrai entidades usando conhecimento de domínio"""
        entities = []
        
        # Use sentence transformers for semantic search
        if self.sentence_model:
            try:
                # Pre-defined contract patterns
                patterns = self._get_contract_patterns()
                
                for pattern_type, pattern_texts in patterns.items():
                    for pattern_text in pattern_texts:
                        # Find similar text in contract
                        similar_texts = self._find_similar_texts(text, pattern_text, threshold=0.8)
                        
                        for similar_text in similar_texts:
                            entity = Entity(
                                text=similar_text,
                                entity_type=pattern_type,
                                start_pos=text.find(similar_text),
                                end_pos=text.find(similar_text) + len(similar_text),
                                confidence=0.85,  # Domain knowledge confidence
                                metadata={'model': 'domain_knowledge', 'pattern': pattern_text}
                            )
                            entities.append(entity)
                            
            except Exception as e:
                logger.error(f"Erro no domain knowledge: {e}")
        
        return entities
    
    def _get_contract_patterns(self) -> Dict[str, List[str]]:
        """Retorna padrões conhecidos de contratos"""
        return {
            'CONTRACT_TYPE': [
                'Statement of Work', 'Master Service Agreement', 'Non-Disclosure Agreement',
                'Sales Contract', 'Framework Agreement', 'Service Agreement'
            ],
            'SERVICE_TYPE': [
                'Information Technology', 'Marketing Services', 'Supply Chain',
                'Consulting Services', 'Professional Services', 'Technical Support'
            ],
            'BUSINESS_AREA': [
                'Data Management', 'Cloud Services', 'Digital Transformation',
                'Business Process', 'Technology Infrastructure', 'Customer Experience'
            ]
        }
    
    def _find_similar_texts(self, contract_text: str, pattern_text: str, threshold: float = 0.8) -> List[str]:
        """Encontra textos similares usando embeddings"""
        try:
            # Generate embeddings
            contract_embedding = self.sentence_model.encode(contract_text)
            pattern_embedding = self.sentence_model.encode(pattern_text)
            
            # Calculate similarity
            from sklearn.metrics.pairwise import cosine_similarity
            similarity = cosine_similarity([contract_embedding], [pattern_embedding])[0][0]
            
            if similarity > threshold:
                # Find the most similar text segment
                segments = contract_text.split('.')
                best_segment = max(segments, key=lambda x: self._calculate_text_similarity(x, pattern_text))
                return [best_segment.strip()]
            
        except Exception as e:
            logger.warning(f"Erro no cálculo de similaridade: {e}")
        
        return []
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade entre dois textos"""
        try:
            if self.sentence_model:
                emb1 = self.sentence_model.encode(text1)
                emb2 = self.sentence_model.encode(text2)
                from sklearn.metrics.pairwise import cosine_similarity
                return cosine_similarity([emb1], [emb2])[0][0]
        except Exception:
            pass
        return 0.0
    
    def _map_bert_entity(self, bert_entity: str) -> Optional[str]:
        """Mapeia entidade BERT para tipo de contrato"""
        mapping = {
            'PERSON': 'SUPPLIER',
            'ORG': 'SUPPLIER',
            'DATE': 'START_DATE',
            'MONEY': 'AMOUNT',
            'CARDINAL': 'CONTRACT_ID'
        }
        return mapping.get(bert_entity)
    
    def _map_roberta_entity(self, segment_type: str, label: str) -> Optional[str]:
        """Mapeia entidade RoBERTa para tipo de contrato"""
        mapping = {
            'amount': 'AMOUNT',
            'date': 'START_DATE',
            'identifier': 'CONTRACT_ID'
        }
        return mapping.get(segment_type)
    
    def _chunk_text(self, text: str, max_length: int = 512) -> List[tuple]:
        """Divide texto em chunks para BERT"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + max_length
            if end < len(text):
                # Try to break at sentence boundary
                last_period = text.rfind('.', start, end)
                if last_period > start:
                    end = last_period + 1
            
            chunks.append((start, text[start:end]))
            start = end
        
        return chunks
    
    def _segment_contract_text(self, text: str) -> List[tuple]:
        """Segmenta texto de contrato em partes relevantes"""
        segments = []
        
        # Split by sentences
        sentences = text.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            # Classify segment type
            if any(word in sentence.lower() for word in ['$', '€', '£', 'amount', 'value', 'cost']):
                segments.append((sentence, 'amount'))
            elif any(word in sentence.lower() for word in ['date', 'effective', 'expiration', 'valid']):
                segments.append((sentence, 'date'))
            elif any(word in sentence.lower() for word in ['contract', 'agreement', 'sow', 'msa']):
                segments.append((sentence, 'identifier'))
        
        return segments
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove entidades duplicadas e mescla similares"""
        if not entities:
            return []
        
        # Sort by confidence
        entities.sort(key=lambda x: x.confidence, reverse=True)
        
        # Remove duplicates based on text and type
        seen = set()
        unique_entities = []
        
        for entity in entities:
            key = (entity.text.lower(), entity.entity_type)
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def _calculate_confidence(self, entities: List[Entity]) -> float:
        """Calcula confiança geral da extração"""
        if not entities:
            return 0.0
        
        total_confidence = sum(entity.confidence for entity in entities)
        return total_confidence / len(entities)
