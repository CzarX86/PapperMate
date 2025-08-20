"""
Teste mínimo de regressão do sistema de tradução: garante fallback controlado
quando o provedor não está disponível, sem dependências externas.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pappermate.services.file_handler import FileHandler, TranslationStatus  # type: ignore


def test_translation_fallback_mapping_for_asian_terms():
    fh = FileHandler()
    # Força cenário sem cliente de tradução
    fh.client = None

    result, status, error = fh.sanitize_filename("【御見積書】_システム運用サポート.pdf")

    # Deve aplicar mapeamento determinístico
    assert any(k in result for k in ["Quotation", "System", "Support"])  # legibilidade
    assert status == TranslationStatus.FAILED  # sem provedor
    assert error is None or "Translation failed" in str(error)
