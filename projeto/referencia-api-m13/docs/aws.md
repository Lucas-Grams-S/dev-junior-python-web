# MiniShop na AWS

```
Internet ─► EC2 (Nginx :80 ─► Uvicorn/Django, Celery, Redis)  ─► RDS PostgreSQL (privado, só aceita o SG do web)
                   │                                              
                   ├─► S3 (mídia, privado, URLs assinadas)        Parameter Store (segredos) ◄─ papel IAM da instância
                   └─► CloudWatch Logs (/minishop/app)            ECR (imagem)
```
Tudo criado por `scripts/aws/provision.sh` com a tag `Project=minishop-curso`; tudo apagado por `scripts/aws/destroy.sh`, e conferido por `scripts/aws/verify_clean.sh`.

## Antes de criar qualquer coisa (checklist)
- [ ] MFA no usuário raiz; usuário/papel de administração sem a raiz no dia a dia
- [ ] `bash scripts/aws/budget.sh seu@email.com 10` (orçamento + alertas)
- [ ] Região escolhida e anotada (`sa-east-1`), e `aws sts get-caller-identity` mostrando a conta certa
- [ ] Data/hora marcada para DESTRUIR (no mesmo dia)

## Depois
- [ ] `bash scripts/aws/destroy.sh` e `bash scripts/aws/verify_clean.sh` → `TUDO LIMPO`
- [ ] Painel de Billing no dia seguinte: custo do dia anterior
