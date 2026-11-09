# Módulo 9 — Segurança

> ⏱️ 8 sessões · 12 h · Pré-requisitos: Módulo 8 concluído (checkpoint aprovado).
> 🏷️ Marco no Git: `v2.3-seguranca`

## 🎯 Objetivos
- Explicar e demonstrar os principais itens do OWASP Top 10 localmente
- Corrigir SQL injection, XSS, CSRF e IDOR no MiniShop
- Armazenar senhas com Argon2/bcrypt e justificar a escolha
- Gerenciar segredos e auditar dependências com `pip-audit`
- Aplicar noções de LGPD no dia a dia do dev

## 📖 Aulas

| # | Aula | Tempo |
|---|------|-------|
| 01 | [OWASP Top 10 e modelagem de ameaças](01-owasp-ameacas.md) | 1h30 |
| 02 | [SQL injection e XSS: vulnerável vs corrigido](02-injection-xss.md) | 1h30 |
| 03 | [CSRF, CORS e sessão vs JWT](03-csrf-cors-sessao-jwt.md) | 1h30 |
| 04 | [Hash de senhas, autenticação vs autorização](04-senhas-autenticacao.md) | 1h30 |
| 05 | [Quebra de controle de acesso (IDOR)](05-controle-acesso-idor.md) | 1h30 |
| 06 | [Segredos, dependências, cabeçalhos e rate limiting](06-segredos-dependencias-headers-rate-limit.md) | 1h30 |
| 07 | [HTTPS, menor privilégio e LGPD básica](07-https-lgpd.md) | 1h30 |
| 08 | [Checkpoint](checkpoint.md) (quiz de 10 questões, entrega prática, autoavaliação) | 1h30 |

> Se uma aula pedir mais de uma sessão, ela é dividida em parte 1 e parte 2 na geração do módulo.

## 📦 Entrega do projeto
Relatório `docs/seguranca.md` com cada vulnerabilidade demonstrada e corrigida, `pip-audit` limpo e cabeçalhos de segurança ativos.

## 🔗 Conexão com o próximo módulo
Próximo: [Módulo 10 — Qualidade, testes e boas práticas](../10-qualidade-testes/README.md).

> ✅ Status: as 7 aulas e o checkpoint estão gerados. **Todo o código foi executado** no laboratório local (Python 3.13, Django 5.2.19; Gunicorn com TLS, Redis 8, PostgreSQL 18.6, CA de laboratório; 235 testes em SQLite e 232 em PostgreSQL), reproduzido em [`projeto/referencia-api-m9/`](../projeto/referencia-api-m9/README.md). Lista de referência: OWASP Top 10:2025. Links de “Para ir além” conferidos com HTTP 200 em 2026-11-08 (exceto o do Planalto, lido por outra ferramenta). Não executado: sistemas de terceiros, MFA, CA pública/Nginx reais, plano de incidentes.
