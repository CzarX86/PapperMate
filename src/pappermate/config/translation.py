"""
Translation service configuration for PapperMate.
Handles API keys and service configuration for filename translation.
"""

import os
from typing import Optional
from pydantic import BaseModel


class TranslationConfig(BaseModel):
    """Configuration for translation services."""
    
    # Google Translate API
    google_translate_api_key: Optional[str] = None
    
    # Service preferences
    prefer_google_api: bool = True
    enable_googletrans_fallback: bool = True
    
    # Rate limiting and caching
    enable_caching: bool = True
    cache_duration_hours: int = 24
    
    class Config:
        env_prefix = "PAPPERMATE_"


def get_translation_config() -> TranslationConfig:
    """Get translation configuration from environment variables."""
    return TranslationConfig(
        google_translate_api_key=os.environ.get('GOOGLE_TRANSLATE_API_KEY'),
        prefer_google_api=os.environ.get('PAPPERMATE_PREFER_GOOGLE_API', 'true').lower() == 'true',
        enable_googletrans_fallback=os.environ.get('PAPPERMATE_ENABLE_GOOGLETRANS_FALLBACK', 'true').lower() == 'true',
        enable_caching=os.environ.get('PAPPERMATE_ENABLE_CACHING', 'true').lower() == 'true',
        cache_duration_hours=int(os.environ.get('PAPPERMATE_CACHE_DURATION_HOURS', '24'))
    )


def setup_translation_environment():
    """Setup translation environment variables and configuration."""
    config = get_translation_config()
    
    print("🔧 Translation Configuration:")
    print(f"   Google Translate API: {'✅ Available' if config.google_translate_api_key else '❌ Not configured'}")
    print(f"   Prefer Google API: {'✅ Yes' if config.prefer_google_api else '❌ No'}")
    print(f"   Googletrans Fallback: {'✅ Enabled' if config.enable_googletrans_fallback else '❌ Disabled'}")
    print(f"   Caching: {'✅ Enabled' if config.enable_caching else '❌ Disabled'}")
    
    if not config.google_translate_api_key:
        print("\n📝 To use Google Translate API:")
        print("   1. Get API key from: https://console.cloud.google.com/apis/credentials")
        print("   2. Set environment variable: export GOOGLE_TRANSLATE_API_KEY='your-key-here'")
        print("   3. Or add to ~/.zshrc for persistence")
    
    return config
