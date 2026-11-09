# Cheatsheet: segurança de aplicações web (módulo 9)

> Aulas 9.01 a 9.07. Tudo foi executado no laboratório [`projeto/referencia-api-m9`](../../projeto/referencia-api-m9/README.md). **Só teste o que é seu.**

## OWASP Top 10:2025 em uma linha
A01 Controle de acesso quebrado · A02 Configuração insegura · A03 Cadeia de suprimentos · A04 Falhas criptográficas · A05 Injeção · A06 Design inseguro · A07 Falhas de autenticação · A08 Integridade de software/dados · A09 Falhas de log e alerta · A10 Condições excepcionais mal tratadas

## Regras que evitam a maioria dos problemas
| Risco | Regra |
|---|---|
| SQL injection | parâmetros (`execute(sql, [x])`) ou ORM; *allowlist* para colunas; nunca f-string em SQL |
| XSS | autoescape; sem `\|safe`/`mark_safe` com dado de usuário; `json_script`; `textContent` no front; CSP |
| CSRF | token CSRF + `SameSite`; cabeçalho `Authorization` não é enviado sozinho |
| CORS | lista explícita de origens; nunca `*` com credenciais; não é autenticação |
| Senhas | Argon2id (ou bcrypt/scrypt/PBKDF2), salt, validadores (≥ 12), sem enumeração |
| IDOR | consulta base já restrita ao dono; `404` para o alheio; matriz de testes + mutação |
| Segredos | ambiente/cofre; `.env` fora do Git; rotacionar se vazou |
| Dependências | `uv.lock`, `pip-audit` no CI, atualizar com frequência |
| Cabeçalhos | CSP, HSTS (crescente), `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy` |
| Logs | eventos (login falho, acesso negado, limite); sem senhas/tokens; sanitizar entrada |
| Limite de taxa | cache **compartilhado** (Redis) e `NUM_PROXIES` correto |
| HTTPS | TLS ≥ 1.2; proxy sobrescreve `X-Forwarded-Proto`; app só na rede interna |
| Banco | papéis: dono (migrações), aplicação (DML), leitura; `ALTER DEFAULT PRIVILEGES` |
| LGPD | inventário, mínimo necessário, base legal, retenção, exportar/anonimizar |

## Códigos HTTP de acesso
`401` não autenticado · `403` autenticado sem permissão · `404` não revelar que existe · `409` conflito de estado · `429` limite de taxa

## Comandos
```bash
uv run ruff check --select S .                         # regras do bandit no linter
uv run bandit -r apps config -q
uv export --no-hashes --no-emit-project -o req.txt && uv run pip-audit -r req.txt --no-deps --disable-pip
uv run detect-secrets scan --all-files --exclude-files '(\.venv|uv\.lock|\.git/)' .
DEBUG=0 SECRET_KEY=... ALLOWED_HOSTS=... uv run python manage.py check --deploy
```

## Armadilhas
- ferramenta "limpa" que não lê o que devia (validar com um caso conhecido!)
- teste de segurança que nunca falhou (validar por mutação)
- desligar a verificação de certificado "para funcionar"
- `X-Forwarded-Proto`/`X-Forwarded-For` confiados sem proxy
- IP e e-mail em logs: também são dados pessoais
