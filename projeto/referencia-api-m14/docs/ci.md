# CI/CD do MiniShop

```
PR / push ─► lint ─┐
           ├► test (sqlite) ─┼─► docker (build + smoke) ─► [merge na main] ─► publish (GHCR) ─► staging ─► [tag v*] ─► produção (aprovação)
           └► test (postgres)┘
```

## Configurações que NÃO estão no YAML (faça no GitHub)
- **Branch `main` protegida:** exigir PR e os checks `Lint, tipos e arquitetura`, `Testes (sqlite)`, `Testes (postgres)`, `Imagem Docker e smoke test`; branch atualizada; 1 aprovação.
- **Environments:** `staging` (sem restrição) e `production` (Required reviewers; só tags `v*`).
- **Packages:** o `GITHUB_TOKEN` publica no GHCR; nenhum segredo cadastrado.

## Decisões
- Actions fixadas por SHA (Dependabot atualiza). `permissions: contents: read` por padrão; `packages: write` só no job `publish`.
- Imagens identificadas por commit (`sha-…`) e versão (`1.2.3`); `latest` não é usada para implantar.
- Estratégia de deploy (módulo 13): *recreate* com Compose num servidor; rollback = reimplantar a tag anterior.

## Rollback
1. Identifique a última versão boa (`gh run list`, tags `v*`).
2. Reimplante a imagem dela (módulo 13: `docker compose pull && up -d` com a tag antiga).
3. Se houve migração destrutiva, restaure o backup (módulo 14). Migrações devem seguir *expandir e contrair*.

## Achados da validação em clone limpo
- `nginx/certs/` não existe num clone (está no `.gitignore`): `scripts/smoke_docker.sh` agora cria a pasta.
- PostgreSQL: 4 testes pulados (SQL específico do SQLite no código legado) e um aviso de teardown (`database "test_minishop" is being accessed by other users`): conexão deixada aberta por algum teste de concorrência. Pendente.

## Execução real (2026-11-09, repositório privado, plano gratuito)
- 1º push: lint e testes (SQLite) **reprovaram** (scripts sem `ruff format`; `DATABASE_URL` vazia). Corrigido; depois, tudo verde.
- Proteção de branch e revisores de `environment` **indisponíveis** (403/422): produção rodou sem aprovação. Mitigação: só tags `v*` chegam lá.
- Dependabot abriu PR de Django 6.1 (reprovado pelo CI); `ignore` para `>=5.3` no `dependabot.yml`.
