#!/usr/bin/env bash
# Cria um ORÇAMENTO mensal com alertas por e-mail (aula 13.01). FAÇA ISTO ANTES de criar qualquer recurso.
# Uso: bash scripts/aws/budget.sh seu@email.com [LIMITE_EM_USD]     (padrão: 10)
set -euo pipefail
EMAIL="${1:?uso: budget.sh seu@email.com [limite_usd]}"
LIMITE="${2:-10}"
export AWS_PAGER=""
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

aws budgets create-budget --account-id "$ACCOUNT" \
  --budget "{\"BudgetName\":\"minishop-mensal\",\"BudgetType\":\"COST\",\"TimeUnit\":\"MONTHLY\",\"BudgetLimit\":{\"Amount\":\"$LIMITE\",\"Unit\":\"USD\"}}" \
  --notifications-with-subscribers "[
    {\"Notification\":{\"NotificationType\":\"ACTUAL\",\"ComparisonOperator\":\"GREATER_THAN\",\"Threshold\":50,\"ThresholdType\":\"PERCENTAGE\"},
     \"Subscribers\":[{\"SubscriptionType\":\"EMAIL\",\"Address\":\"$EMAIL\"}]},
    {\"Notification\":{\"NotificationType\":\"ACTUAL\",\"ComparisonOperator\":\"GREATER_THAN\",\"Threshold\":80,\"ThresholdType\":\"PERCENTAGE\"},
     \"Subscribers\":[{\"SubscriptionType\":\"EMAIL\",\"Address\":\"$EMAIL\"}]},
    {\"Notification\":{\"NotificationType\":\"FORECASTED\",\"ComparisonOperator\":\"GREATER_THAN\",\"Threshold\":100,\"ThresholdType\":\"PERCENTAGE\"},
     \"Subscribers\":[{\"SubscriptionType\":\"EMAIL\",\"Address\":\"$EMAIL\"}]}
  ]"
aws budgets describe-budgets --account-id "$ACCOUNT" --query 'Budgets[].[BudgetName,BudgetLimit.Amount,BudgetLimit.Unit]' --output text
