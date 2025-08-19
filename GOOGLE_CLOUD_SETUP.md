# ☁️ Configuração Google Cloud - Rate Limiting e Custos

Este documento explica como configurar o Google Cloud para controlar custos e rate limiting da API de tradução.

## 🎯 **Por que Rate Limiting no Google Cloud?**

- ✅ **Mais seguro** - Limites aplicados no servidor
- ✅ **Mais eficiente** - Não consome recursos do projeto
- ✅ **Mais confiável** - Funciona mesmo se o projeto falhar
- ✅ **Mais barato** - Evita custos inesperados

## 🔧 **Configuração de Rate Limiting**

### **1. Acessar Console do Google Cloud:**
```
https://console.cloud.google.com/apis/credentials
```

### **2. Configurar Quotas para Translation API:**

#### **📍 Caminho Correto:**
```
APIs & Services → Enabled APIs & Services
→ Cloud Translation API
→ Quotas (aba)
```

**OU**

```
APIs & Services → Service Usage
→ Cloud Translation API
→ Quotas & Limits
```

#### **📊 Quotas Recomendadas:**
```
Requests per day: 1.000
Requests per 100 seconds: 100
Characters per day: 50.000
Characters per 100 seconds: 5.000
```

#### **🔍 Como Configurar:**
1. Vá para **APIs & Services** → **Service Usage**
2. Clique em **Cloud Translation API**
3. Vá para a aba **Quotas & Limits**
4. Clique em **"Edit Quotas"** para cada limite
5. Configure os valores recomendados acima

### **3. Configuração via gcloud CLI:**

```bash
# Instalar gcloud CLI
brew install google-cloud-sdk

# Autenticar
gcloud auth login

# Configurar projeto
gcloud config set project SEU_PROJECT_ID

# Ver quotas atuais
gcloud compute quotas list --filter="name:translate"

# Configurar quotas (exemplo)
gcloud compute quotas update translate-requests-per-day \
  --limit=1000 \
  --region=global
```

## 💰 **Configuração de Budget e Alertas**

### **1. Criar Budget de Custos:**

```bash
# Criar budget de $5/mês para Translation API
gcloud billing budgets create \
  --billing-account=SEU_BILLING_ACCOUNT \
  --display-name="Translation API Budget" \
  --budget-amount=5.00USD \
  --threshold-rule=threshold-amount=1.00USD \
  --threshold-rule=threshold-amount=3.00USD \
  --threshold-rule=threshold-amount=4.50USD
```

### **2. Configurar Alertas:**
- **$1.00** - Primeiro alerta (20% do budget)
- **$3.00** - Segundo alerta (60% do budget)  
- **$4.50** - Alerta crítico (90% do budget)

### **3. Monitoramento via Console:**
```
https://console.cloud.google.com/billing/SEU_BILLING_ACCOUNT/budgets
```

## 📊 **Cálculo de Custos para Nomes de Arquivos**

### **Estimativa Conservadora:**
```
1 nome de arquivo = ~50 caracteres
1.000 nomes/dia = 50.000 caracteres
Custo: $0.001 por 1.000 caracteres

Custo diário: $0.05
Custo mensal: $1.50
```

### **Com Rate Limiting Configurado:**
```
Limite: 1.000 requests/dia
Custo máximo diário: $0.05
Custo máximo mensal: $1.50
```

## 🚨 **Alertas e Notificações**

### **1. Email Alerts:**
- Configure seu email para receber alertas
- Receba notificação quando atingir 20%, 60%, 90% do budget

### **2. Slack/Teams Integration:**
```bash
# Configurar webhook para Slack
gcloud functions deploy budget-alert \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated
```

### **3. SMS Alerts:**
- Configure alertas SMS para valores críticos
- Receba notificação imediata em emergências

## 🔒 **Segurança e Controle de Acesso**

### **1. Restringir API Key:**
```
Console → APIs & Services → Credentials
→ Selecionar sua API key
→ API restrictions → Restrict key
→ Selecionar apenas "Cloud Translation API"
```

### **2. Restringir por IP (Opcional):**
```
→ Application restrictions → HTTP referrers
→ Adicionar domínios/IPs permitidos
```

### **3. Rotação de Chaves:**
```bash
# Criar nova chave
gcloud iam service-accounts keys create nova-chave.json \
  --iam-account=SEU_SERVICE_ACCOUNT

# Revogar chave antiga
gcloud iam service-accounts keys delete CHAVE_ANTIGA_ID \
  --iam-account=SEU_SERVICE_ACCOUNT
```

## 📈 **Monitoramento e Analytics**

### **1. Cloud Monitoring:**
```
https://console.cloud.google.com/monitoring
```

### **2. Métricas Importantes:**
- **Requests per second**
- **Error rate**
- **Latency**
- **Cost per request**

### **3. Dashboards Personalizados:**
```bash
# Criar dashboard de monitoramento
gcloud monitoring dashboards create \
  --config-from-file=dashboard-config.yaml
```

## 🧪 **Teste de Rate Limiting**

### **1. Teste de Limites:**
```bash
# Script para testar rate limits
poetry run python test_rate_limits.py
```

### **2. Verificar Quotas:**
```bash
# Ver uso atual
gcloud compute quotas list --filter="name:translate"

# Ver histórico de uso
gcloud compute quotas list --filter="name:translate" --format="table(name,limit,usage)"
```

## 🚀 **Configuração Rápida**

### **Script de Setup Automático:**
```bash
#!/bin/bash
# setup_google_cloud.sh

echo "🔧 Configurando Google Cloud para PapperMate..."

# Configurar projeto
gcloud config set project SEU_PROJECT_ID

# Configurar quotas
gcloud compute quotas update translate-requests-per-day --limit=1000 --region=global
gcloud compute quotas update translate-characters-per-day --limit=50000 --region=global

# Criar budget
gcloud billing budgets create \
  --billing-account=SEU_BILLING_ACCOUNT \
  --display-name="PapperMate Translation Budget" \
  --budget-amount=5.00USD

echo "✅ Configuração concluída!"
```

## 📚 **Recursos Adicionais**

- [Google Cloud Quotas Documentation](https://cloud.google.com/compute/quotas)
- [Budget Management](https://cloud.google.com/billing/docs/how-to/budgets)
- [API Restrictions](https://cloud.google.com/apis/docs/restricting-api-access)
- [Cost Optimization](https://cloud.google.com/translate/pricing)

## 🤝 **Suporte**

Para problemas com configuração do Google Cloud:
1. [Google Cloud Support](https://cloud.google.com/support)
2. [Community Forums](https://cloud.google.com/community)
3. [Documentation](https://cloud.google.com/docs)
