#!/bin/bash
# Script para configurar quotas do Google Translate API
# Uso: ./setup_google_quotas.sh

set -e

echo "🔧 Configurando Quotas do Google Translate API para PapperMate..."
echo "================================================================"

# Verificar se gcloud está instalado
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI não está instalado."
    echo "📥 Instale com: brew install google-cloud-sdk"
    exit 1
fi

# Verificar se está autenticado
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Não está autenticado no Google Cloud."
    echo "🔐 Execute: gcloud auth login"
    exit 1
fi

# Mostrar projeto atual
CURRENT_PROJECT=$(gcloud config get-value project)
echo "📍 Projeto atual: $CURRENT_PROJECT"

# Perguntar se quer continuar
read -p "🤔 Continuar com este projeto? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Configuração cancelada."
    exit 1
fi

echo ""
echo "📊 Configurando quotas recomendadas..."

# Listar quotas atuais
echo "🔍 Quotas atuais do Translation API:"
gcloud compute quotas list --filter="name:translate" --format="table(name,limit,usage)" || echo "⚠️ Não foi possível listar quotas atuais"

echo ""
echo "⚙️ Configurando quotas..."

# Configurar quotas (se disponíveis)
echo "   📝 Requests per day: 1.000"
gcloud compute quotas update translate-requests-per-day --limit=1000 --region=global 2>/dev/null || echo "     ⚠️ Quota não encontrada ou não configurável"

echo "   📝 Characters per day: 50.000"
gcloud compute quotas update translate-characters-per-day --limit=50000 --region=global 2>/dev/null || echo "     ⚠️ Quota não encontrada ou não configurável"

echo "   📝 Requests per 100 seconds: 100"
gcloud compute quotas update translate-requests-per-100-seconds --limit=100 --region=global 2>/dev/null || echo "     ⚠️ Quota não encontrada ou não configurável"

echo "   📝 Characters per 100 seconds: 5.000"
gcloud compute quotas update translate-characters-per-100-seconds --limit=5000 --region=global 2>/dev/null || echo "     ⚠️ Quota não encontrada ou não configurável"

echo ""
echo "🔍 Verificando quotas configuradas..."

# Listar quotas após configuração
gcloud compute quotas list --filter="name:translate" --format="table(name,limit,usage)" || echo "⚠️ Não foi possível listar quotas"

echo ""
echo "📋 Configuração via Console do Google Cloud:"
echo "============================================="
echo "1. Acesse: https://console.cloud.google.com/apis/serviceusage"
echo "2. Clique em 'Cloud Translation API'"
echo "3. Vá para a aba 'Quotas & Limits'"
echo "4. Configure manualmente:"
echo "   - Requests per day: 1.000"
echo "   - Characters per day: 50.000"
echo "   - Requests per 100 seconds: 100"
echo "   - Characters per 100 seconds: 5.000"

echo ""
echo "💰 Cálculo de Custos:"
echo "====================="
echo "Com estas quotas:"
echo "- Máximo: 1.000 requests/dia"
echo "- Custo máximo diário: ~$0.05"
echo "- Custo máximo mensal: ~$1.50"
echo ""
echo "✅ Configuração concluída!"
echo ""
echo "💡 Dica: Configure também um budget de $5/mês para alertas:"
echo "   https://console.cloud.google.com/billing/budgets"
