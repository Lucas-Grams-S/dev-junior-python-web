# Módulo 2 — Como a web funciona

> ⏱️ 6 sessões · 9 h · Pré-requisitos: Módulo 1 concluído (checkpoint aprovado).
> 🏷️ Marco no Git: `v0.2-http-minimo`

## 🎯 Objetivos
- Descrever o caminho de uma requisição (DNS → TCP → TLS → HTTP)
- Ler e montar requisições/respostas HTTP (métodos, status, headers, corpo)
- Explicar cookies e sessões
- Usar DevTools, `curl` e Bruno/HTTPie
- Construir um servidor HTTP mínimo com a biblioteca padrão

## 📖 Aulas

| # | Aula | Tempo |
|---|------|-------|
| 01 | [Cliente-servidor, IP, DNS, portas e TCP](01-cliente-servidor-dns-tcp.md) | 1h30 |
| 02 | [HTTP: métodos, status codes, headers e corpo](02-http-metodos-status-headers.md) | 1h30 |
| 03 | [HTTPS/TLS, cookies, sessões, JSON, URLs e query strings](03-tls-cookies-sessoes-json-urls.md) | 1h30 |
| 04 | [DevTools, `curl` e Bruno/HTTPie](04-devtools-curl-bruno.md) | 1h30 |
| 05 | [Mini-projeto: servidor HTTP mínimo com a stdlib](05-servidor-http-minimo.md) | 1h30 |
| 06 | [Checkpoint](checkpoint.md) (quiz de 10 questões, entrega prática, autoavaliação) | 1h30 |

> Se uma aula pedir mais de uma sessão, ela é dividida em parte 1 e parte 2 na geração do módulo.

## 📦 Entrega do projeto
**Servidor HTTP mínimo** em Python puro servindo o catálogo do CLI de estoque em JSON (`GET /produtos`).

## 🔗 Conexão com o próximo módulo
Próximo: [Módulo 3 — Bancos de dados relacionais](../03-banco-de-dados/README.md).

> ✅ Status: conteúdo gerado; exemplos, servidores e testes executados em 2026-11-07 (Python 3.13, curl 8.18). Passos de interface gráfica (DevTools, Bruno) não foram executados e estão marcados nas aulas.
