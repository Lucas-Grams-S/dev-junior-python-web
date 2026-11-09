# Mapa do módulo 12 (material do curso)

Laboratório do módulo 12: o projeto do módulo 11 com a **integração contínua**. Os workflows foram validados com o **actionlint**, os **mesmos comandos** de cada job foram executados num `git clone` limpo em containers, **e tudo foi executado no GitHub** (repositório privado, 2026-11-09; veja `docs/ci.md`).

| Onde | Aula |
|---|---|
| `.github/workflows/ci.yml` (lint, test em matriz SQLite/PostgreSQL, docker), `.github/dependabot.yml` | 12.01 e 12.02 |
| `.github/workflows/cd.yml` (publicar no GHCR, `staging`, `production`) | 12.02 |
| `scripts/smoke_docker.sh` (agora cria `nginx/certs` se faltar: achado do clone limpo) | 12.02 |
