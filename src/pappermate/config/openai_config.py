"""
OpenAI Configuration
Centralized configuration for OpenAI API integration
"""

import os
from typing import Optional

class OpenAIConfig:
    """OpenAI configuration class"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.org_id = os.getenv('OPENAI_ORG_ID')
        self.default_model = os.getenv('OPENAI_DEFAULT_MODEL', 'gpt-4')
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
        self.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.1'))
    
    def is_configured(self) -> bool:
        """Check if OpenAI is properly configured"""
        return bool(self.api_key)
    
    def get_client_config(self) -> dict:
        """Get client configuration"""
        config = {
            'api_key': self.api_key
        }
        
        if self.org_id:
            config['organization'] = self.org_id
            
        return config
    
    def get_completion_config(self) -> dict:
        """Get completion configuration"""
        return {
            'model': self.default_model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }
    
    def print_status(self):
        """Print configuration status"""
        print("🔧 Configuração OpenAI:")
        print(f"  API Key: {'✅ Configurada' if self.api_key else '❌ Não configurada'}")
        print(f"  Org ID: {'✅ Configurado' if self.org_id else '❌ Não configurado'}")
        print(f"  Modelo padrão: {self.default_model}")
        print(f"  Max tokens: {self.max_tokens}")
        print(f"  Temperature: {self.temperature}")

# Global configuration instance
config = OpenAIConfig()

def get_openai_config() -> OpenAIConfig:
    """Get global OpenAI configuration"""
    return config

def setup_environment():
    """Setup environment variables for OpenAI"""
    print("🚀 Configurando ambiente OpenAI...")
    
    # Check if API key is set
    if not config.api_key:
        print("❌ OPENAI_API_KEY não configurada")
        print("Configure com:")
        print("  export OPENAI_API_KEY='sua-chave-api-aqui'")
        print("  export OPENAI_ORG_ID='seu-org-id-aqui' (opcional)")
        print("  export OPENAI_DEFAULT_MODEL='gpt-4' (opcional)")
        print("  export OPENAI_MAX_TOKENS='2000' (opcional)")
        print("  export OPENAI_TEMPERATURE='0.1' (opcional)")
        return False
    
    print("✅ OpenAI configurado com sucesso!")
    config.print_status()
    return True
