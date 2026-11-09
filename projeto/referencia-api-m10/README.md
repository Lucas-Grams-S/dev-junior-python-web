# MiniShop

API de uma loja virtual feita em **Django + Django REST Framework**: catálogo, carrinho, pedidos com controle de estoque, pagamento por gateway (com *adapter*), e-mails assíncronos, notificações em tempo real e um conjunto de garantias de **qualidade** e **segurança** verificadas por testes e ferramentas.

> Projeto do treinamento *Dev Júnior Python Web*. É um laboratório de estudo: o gateway de pagamento é simulado e nenhum dado é real.

## Principais recursos
- **Catálogo** com busca, filtros, ordenação e paginação · **carrinho** · **pedidos** com idempotência (`Idempotency-Key`) e baixa de estoque transacional
- **Pagamento** atrás de uma porta (`PaymentGateway`) com adaptadores intercambiáveis e **webhooks** assinados (HMAC, anti-*replay*, idempotentes)
- **Autenticação JWT** (access de 15 min + refresh com rotação), permissões por papel e **por objeto**, limite de taxa
- **Tarefas assíncronas** (Celery + Redis) com retentativas e idempotência; **WebSocket** para acompanhar o pedido
- **LGPD básica:** exportar e anonimizar os dados de um titular
- **OpenAPI** gerado (drf-spectacular), com o contrato verificado em teste

## Começando
Pré-requisitos: [uv](https://docs.astral.sh/uv/) e Python 3.13 (o `uv` instala).

```bash
git clone <url-do-repositorio> minishop && cd minishop
uv sync                                          # dependências travadas em uv.lock
export DEBUG=1                                   # desenvolvimento (em produção: veja "Configuração")
uv run python manage.py migrate
uv run python manage.py seed                     # 64 produtos + usuários gerente, estoquista e cliente
uv run python manage.py runserver
```
A API fica em `http://127.0.0.1:8000/api/v1/` e a documentação interativa em `/api/docs/` (só em desenvolvimento, ou com `EXPOSE_DOCS=1`).
Usuários de desenvolvimento: `gerente`, `estoquista`, `cliente`; senha `dev-somente-local-123` (o comando `seed` **recusa rodar** fora de desenvolvimento).

```bash
# exemplo: login e listagem de produtos
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/token/ -H 'Content-Type: application/json' \
        -d '{"username":"cliente","password":"dev-somente-local-123"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access"])')
curl -s -H "Authorization: Bearer $TOKEN" localhost:8000/api/v1/products/ | head -c 300
```

## Testes e qualidade
```bash
uv run pytest                          # toda a suíte (ordem aleatória, independente)
uv run pytest -m unidade               # só os testes de unidade (rápidos)
uv run pytest -n 4                     # em paralelo
bash scripts/cobertura_negocio.sh      # porta de cobertura: >= 80% nas camadas de negócio
uv run ruff check && uv run ruff format --check
uv run mypy
uv run lint-imports                    # contratos de arquitetura
```
Instale os *hooks* para que o `ruff`, o `mypy`, a busca de segredos e a validação da mensagem de commit rodem antes de cada commit:
```bash
uv run pre-commit install --install-hooks
uv run pre-commit install --hook-type commit-msg --hook-type pre-push
```
Veja [CONTRIBUTING.md](CONTRIBUTING.md) para o fluxo de trabalho e o padrão de commits.

## Arquitetura
```
apps/<app>/
  api.py, serializers.py   interface (HTTP): traduz requisições em casos de uso
  services.py, selectors.py, tasks.py   casos de uso e consultas (regras de negócio e transações)
  domain.py                regras PURAS, sem banco (fáceis de testar)
  repositories.py          acesso a dados atrás de uma interface (Django e em memória)
  models.py                persistência
config/                    configurações, URLs, erros, cabeçalhos de segurança
```
Os limites entre camadas e entre *apps* são **impostos pelo CI** (`import-linter`). Decisões registradas em [`docs/adr/`](docs/adr/README.md); segurança em [`docs/seguranca.md`](docs/seguranca.md); privacidade em [`docs/privacidade.md`](docs/privacidade.md).

## Configuração (variáveis de ambiente)
| Variável | Padrão | Para quê |
|---|---|---|
| `DEBUG` | `0` | `1` só em desenvolvimento |
| `SECRET_KEY` | — | **obrigatória** quando `DEBUG=0` (o processo recusa subir sem ela) |
| `ALLOWED_HOSTS` | vazio (`*` em `DEBUG`) | hosts aceitos, separados por vírgula |
| `DATABASE_URL` | SQLite local | `postgres://usuario:senha@host:5432/banco` em produção |
| `PAYMENT_GATEWAY` | `fake` | `fake` ou `acme` |
| `ORDER_EMAIL_MODE` | `async` | `sync`, `async` ou `off` |
| `CELERY_BROKER_URL` | Redis local | broker das tarefas |
| `REDIS_CACHE_URL` | cache local | cache **compartilhado** (necessário para o limite de taxa com vários workers) |
| `EXPOSE_DOCS`, `ADMIN_URL`, `NUM_PROXIES` | `DEBUG`, `admin/`, `0` | superfície exposta e IP real atrás de proxy |

Copie `.env.example` e **nunca** versione segredos.

## Licença
Uso educacional.
