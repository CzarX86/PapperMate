"""
Sistema de tradução automática para inglês
"""
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class ContractTranslator:
    """Traduz contratos para inglês antes do processamento NLP"""
    
    def __init__(self, use_google_translate: bool = True):
        self.use_google_translate = use_google_translate
        self.translation_cache = {}
        
        # Try to import Google Translate
        try:
            from googletrans import Translator
            self.translator = Translator()
            self.google_available = True
        except ImportError:
            self.google_available = False
            logger.warning("Google Translate não disponível. Instale: pip install googletrans==4.0.0rc1")
    
    def detect_language(self, text: str) -> str:
        """Detecta idioma do texto"""
        if not self.google_available:
            return "unknown"
        
        try:
            detection = self.translator.detect(text[:1000])  # Primeiros 1000 chars
            return detection.lang
        except Exception as e:
            logger.warning(f"Erro na detecção de idioma: {e}")
            return "unknown"
    
    def translate_to_english(self, text: str, source_lang: Optional[str] = None) -> Dict[str, Any]:
        """Traduz texto para inglês"""
        
        # Check cache
        text_hash = hash(text)
        if text_hash in self.translation_cache:
            logger.info("📋 Usando tradução em cache")
            return self.translation_cache[text_hash]
        
        # Detect language if not provided
        if not source_lang:
            source_lang = self.detect_language(text)
        
        # If already English, return as is
        if source_lang in ['en', 'english']:
            result = {
                'original_text': text,
                'translated_text': text,
                'source_language': source_lang,
                'target_language': 'en',
                'translation_needed': False,
                'confidence': 1.0
            }
            self.translation_cache[text_hash] = result
            return result
        
        # Translate if Google Translate available
        if self.google_available and source_lang != 'en':
            try:
                translation = self.translator.translate(text, dest='en')
                
                result = {
                    'original_text': text,
                    'translated_text': translation.text,
                    'source_language': source_lang,
                    'target_language': 'en',
                    'translation_needed': True,
                    'confidence': translation.confidence / 100.0,
                    'extra': {
                        'pronunciation': getattr(translation, 'pronunciation', None),
                        'src': getattr(translation, 'src', source_lang)
                    }
                }
                
                logger.info(f"🌍 Traduzido de {source_lang} para inglês (confiança: {result['confidence']:.2f})")
                
            except Exception as e:
                logger.error(f"❌ Erro na tradução: {e}")
                result = {
                    'original_text': text,
                    'translated_text': text,  # Fallback to original
                    'source_language': source_lang,
                    'target_language': 'en',
                    'translation_needed': True,
                    'confidence': 0.0,
                    'error': str(e)
                }
        else:
            # No translation available
            result = {
                'original_text': text,
                'translated_text': text,
                'source_language': source_lang,
                'target_language': 'en',
                'translation_needed': True,
                'confidence': 0.0,
                'error': 'Translation service not available'
            }
        
        # Cache result
        self.translation_cache[text_hash] = result
        return result
    
    def translate_contract_file(self, file_path: str) -> Dict[str, Any]:
        """Traduz arquivo de contrato completo"""
        file_path = Path(file_path)
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                logger.error(f"❌ Não foi possível ler o arquivo: {file_path}")
                return {}
        
        # Translate content
        translation_result = self.translate_to_english(content)
        
        # Add file metadata
        translation_result['file_path'] = str(file_path)
        translation_result['file_size'] = len(content)
        translation_result['file_encoding'] = 'utf-8'
        
        return translation_result
    
    def get_translation_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de tradução"""
        total_translations = len(self.translation_cache)
        translations_needed = sum(1 for r in self.translation_cache.values() if r.get('translation_needed', False))
        avg_confidence = sum(r.get('confidence', 0) for r in self.translation_cache.values()) / total_translations if total_translations > 0 else 0
        
        return {
            'total_translations': total_translations,
            'translations_needed': translations_needed,
            'translations_skipped': total_translations - translations_needed,
            'average_confidence': avg_confidence,
            'cache_hit_rate': 1.0  # All translations are cached
        }
