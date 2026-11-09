# 6. Os doze fatores e configuração por ambiente

> ⏱️ ~1h30 · Módulo 8 · Pré-requisitos: [5.14 (config, env, logging)](../05-django/14-config-env-logging.md), [7.05 (Gunicorn)](../07-sincrono-assincrono/05-wsgi-asgi.md), [8.05](05-monolito-vs-microsservicos.md)

> ✅ **Verificação.** Tudo executado em 2026-11-08: o laboratório do MiniShop foi **auditado**, corrigido e rodado em **dois bancos** (SQLite e **PostgreSQL 18.6** num container meu, porta 5499), com Gunicorn 26.2 em modo produção. **As saídas são reais.** A suíte tem agora **147 testes**: **146 passam no SQLite** (1 pulado) e **143 no PostgreSQL** (4 pulados), sem falhas. Esta aula também fecha duas pendências do módulo 5 (ILIKE e concorrência em PostgreSQL), que antes estavam sem verificação.

## 🎯 Objetivos
- Explicar os **12 fatores** com exemplos do MiniShop e **auditar** um projeto contra eles
- Mover configuração e segredos para o **ambiente**, com **falha cedo** quando faltam (`SECRET_KEY`, `DATABASE_URL`)
- Mandar logs para **stdout** e encerrar processos com **SIGTERM gracioso**
- Rodar a mesma suíte em **SQLite e PostgreSQL** e interpretar as diferenças (paridade dev/produção)
- Usar `manage.py check --deploy` como lista de verificação

## 🤔 Por que isso importa
“Funciona na minha máquina” quase sempre é uma diferença de **configuração** ou de **ambiente**: outro banco, outra variável, uma chave no repositório. Os doze fatores são um conjunto de práticas para que a **mesma aplicação** rode igual em desenvolvimento, teste e produção, em qualquer plataforma. Em entrevistas e em code review, “onde ficam os segredos?” e “como você encerra o processo sem perder requisições?” são perguntas clássicas.

## 💡 Intuição (explicação simples)
Pense em um **eletrodoméstico**: o mesmo aparelho funciona em qualquer casa porque a **tomada** (configuração) fica **fora** dele. Você não abre o aparelho e solda fios para mudar de casa. A aplicação dos doze fatores é igual: o código é o aparelho; banco, chaves e endereços são a tomada, e vêm **de fora**, pelo ambiente.

## 🔬 Como funciona por dentro
| # | Fator | No MiniShop |
|---|---|---|
| I | **Base de código**: um repositório, vários deploys | um repo; dev/CI/produção são deploys do mesmo commit |
| II | **Dependências** declaradas e isoladas | `pyproject.toml` + `uv.lock` |
| III | **Configuração no ambiente** | `SECRET_KEY`, `DEBUG`, `DATABASE_URL`, `ALLOWED_HOSTS`… |
| IV | **Serviços de apoio** como recursos anexados | banco, Redis, RabbitMQ, gateway: trocados por URL |
| V | **Build, release, run** separados | imagem construída uma vez; a config entra na execução |
| VI | **Processos** sem estado | sem arquivos locais como memória (estado em banco/Redis) |
| VII | **Vínculo de porta** | Gunicorn escuta uma porta |
| VIII | **Concorrência** escalando por processos | mais workers/instâncias |
| IX | **Descartabilidade**: subir rápido, sair com graça | `SIGTERM` termina o que está em andamento |
| X | **Paridade dev/produção** | mesmo banco nos dois (PostgreSQL) |
| XI | **Logs** como fluxo de eventos | tudo em stdout |
| XII | **Processos administrativos** pontuais | `manage.py migrate`, comandos de manutenção |

- **Configuração é o que muda entre deploys** (credenciais, hosts, URLs). Constantes do código (`QUANTIDADE_MAXIMA`) **não** são configuração. Um teste: “posso abrir o código-fonte agora sem vazar nada?”.
- **Falhar cedo.** Se a `SECRET_KEY` falta em produção, o processo deve **recusar subir**, e não rodar com uma chave padrão.
- **Padrão seguro.** `DEBUG` só liga se a variável disser; o esquecimento cai no lado seguro.
- **Paridade dev/produção não é detalhe.** SQLite e PostgreSQL diferem em travas de linha, sequências, tipos, e em como a biblioteca do OpenAPI deduz limites (veja abaixo).

## 🛠️ Exemplo prático
**1. Auditoria do laboratório (antes).** Um `grep` honesto no `settings.py` revelou:
```python
SECRET_KEY = "lab-only-not-secret"      # fator III: segredo no código
DEBUG = True                            # padrão INSEGURO
ALLOWED_HOSTS = ["*"]
DATABASES = {... "sqlite3" ...}          # fator X: dev ≠ produção; fator IV: banco fixo no código
# (sem LOGGING: o fator XI dependia do padrão do Django)
```
E o `check --deploy` do Django confirmou: **7 avisos**.
```text
avisos de segurança: 7
security.W002 security.W004 security.W008 security.W009 security.W012 security.W016 security.W018 
```

**2. A correção: leitura do ambiente, sem dependências extras** (`config/envconf.py`)
```python
"""Leitura de configuração do ambiente (Fator III), sem dependências externas."""
import os
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

_VERDADE = {"1", "true", "yes", "on"}


def env_bool(nome: str, padrao: bool = False) -> bool:
    valor = os.environ.get(nome)
    return padrao if valor is None else valor.strip().lower() in _VERDADE


def env_list(nome: str, padrao: list[str]) -> list[str]:
    valor = os.environ.get(nome)
    return padrao if valor is None else [v.strip() for v in valor.split(",") if v.strip()]


def database_from_url(url: str) -> dict:
    """sqlite:///caminho  |  postgres://usuario:senha@host:porta/banco"""
    u = urlparse(url)
    if u.scheme == "sqlite":
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": unquote(u.path[1:])}
    if u.scheme in ("postgres", "postgresql"):
        return {"ENGINE": "django.db.backends.postgresql", "NAME": u.path.lstrip("/"), "USER": unquote(u.username or ""),
                "PASSWORD": unquote(u.password or ""), "HOST": u.hostname or "", "PORT": str(u.port or ""), "CONN_MAX_AGE": 60}
    raise ImproperlyConfigured(f"DATABASE_URL com esquema não suportado: {u.scheme!r}")
```
```python
# config/settings.py (trechos)
DEBUG = env_bool("DEBUG", False)                                   # padrão seguro
SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-nao-use-em-producao"
    else:
        raise ImproperlyConfigured("SECRET_KEY é obrigatória quando DEBUG=False (defina a variável de ambiente).")
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", ["*"] if DEBUG else [])
DATABASES = {"default": database_from_url(os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"))}

LOGGING = {...  "handlers": {"stdout": {"class": "logging.StreamHandler", "stream": "ext://sys.stdout", ...}}, ...}

if not DEBUG:                                                      # produção (atrás de proxy TLS)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "3600"))
    MIDDLEWARE.insert(1, "django.middleware.clickjacking.XFrameOptionsMiddleware")
```
Sem `SECRET_KEY` e sem `DEBUG`, o processo **recusa subir**:
```text
django.core.exceptions.ImproperlyConfigured: SECRET_KEY é obrigatória quando DEBUG=False (defina a variável de ambiente).
```
Em “produção” (chave aleatória longa, host definido), o `check --deploy` cai de **7 avisos para 2**:
```text
System check identified some issues:

WARNINGS:
?: (security.W005) You have not set the SECURE_HSTS_INCLUDE_SUBDOMAINS setting to True. Without this, your site is potentially vulnerable to attack via an insecure connection to a subdomain. Only set this to True if you are certain that all subdomains of your domain should be served exclusively via SSL.
?: (security.W021) You have not set the SECURE_HSTS_PRELOAD setting to True. Without this, your site cannot be submitted to the browser preload list.

System check identified 2 issues (0 silenced).
```
Os 2 restantes (HSTS para subdomínios e *preload*) são decisões que exigem conhecer o domínio (um erro aqui é difícil de desfazer), então ficam como **decisão consciente**, não como esquecimento. A suíte ganhou `tests/test_envconf.py` (o parser de `DATABASE_URL`, inclusive senha com `@` e `/`, o falhar-cedo e os booleanos) e o `pytest.ini` define `DEBUG=1` para os testes (via `pytest-env`).

**3. Paridade: a mesma suíte em PostgreSQL 18.** Subi um container só para isto (porta 5499; o seu `minishop-pg` não foi tocado):
```bash
docker run -d --name m8-pg18 -e POSTGRES_PASSWORD=lab -e POSTGRES_DB=minishop_m8 -p 127.0.0.1:5499:5432 postgres:18
export DATABASE_URL=postgres://postgres:lab@127.0.0.1:5499/minishop_m8
uv run python manage.py migrate && uv run pytest -q
```
A **primeira execução falhou**: `19 failed, 104 passed, 10 errors`. Isso é o valor da paridade. Duas causas reais:

| Achado | Causa | Correção |
|---|---|---|
| 29 testes (19 falhas + 10 erros) quebraram (“Produto indisponível”, `KeyError: 'id'`) | Os testes assumem **ids previsíveis** (produto 1, 2…). No SQLite, o *rollback* do teste reinicia o contador. No PostgreSQL, **sequences não são revertidas** por transação | `conftest.py` zera as sequences antes do seed. **Dívida honesta:** o ideal é os testes buscarem o produto em vez de assumir o id |
| `test_schema_commitado_esta_em_dia` falhou | O `drf-spectacular` deduz `maximum`/`format: int64` de campos inteiros positivos **a partir do banco** (SQLite: 64 bits; PostgreSQL: 32). O **contrato OpenAPI mudava conforme o banco**, sem ninguém tocar na API | O teste compara o schema **sem** esses limites acidentais |

Depois das correções, o resultado nos dois bancos:
```text
PostgreSQL 18.6: 133 passed   (os 133 testes que existiam nesse ponto da aula)
SQLite:          133 passed
```
O teste `test_busca_ignora_maiusculas_e_acha_por_sku` (busca sem diferenciar maiúsculas, pendente do módulo 5) **passa em PostgreSQL**, onde o `icontains` vira `UPPER(...) LIKE UPPER(...)`.

**4. Concorrência real (pendência da aula 5.17).** Oito compradores disputam a **última unidade** (`tests/test_concorrencia.py`, só roda em PostgreSQL):
```python
"""Várias pessoas compram a ÚLTIMA unidade ao mesmo tempo. Só faz sentido em PostgreSQL (SQLite ignora select_for_update)."""
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.db import connection

from apps.cart import services as carrinho
from apps.catalog.models import Product
from apps.orders import services as pedidos

pytestmark = [
    pytest.mark.django_db(transaction=True),      # commits reais: as threads precisam enxergar os dados
    pytest.mark.skipif(connection.vendor != "postgresql", reason="concorrência real exige PostgreSQL"),
]


def test_oito_compradores_uma_unidade_so_um_vence(seed, django_user_model):
    produto = Product.objects.filter(is_active=True).first()
    Product.objects.filter(pk=produto.pk).update(stock=1)
    usuarios = [django_user_model.objects.create_user(username=f"c{i}", password="x" * 12) for i in range(8)]
    for u in usuarios:
        carrinho.add_item(u, produto.pk, 1)

    def comprar(u):
        try:
            pedidos.create_order(u)
            return "ok"
        except pedidos.StockError:
            return "sem_estoque"
        finally:
            connection.close()                    # cada thread tem a própria conexão

    with ThreadPoolExecutor(max_workers=8) as pool:
        resultados = list(pool.map(comprar, usuarios))

    produto.refresh_from_db()
    assert resultados.count("ok") == 1 and resultados.count("sem_estoque") == 7
    assert produto.stock == 0
```
```text
1 passed  (3 execuções seguidas)
```
Para provar que o teste enxerga o bug, desfiz temporariamente as proteções (código restaurado depois):
```text
A) sem select_for_update, UPDATE condicional mantido:   passou 3 de 3
B) sem select_for_update E sem a condição stock__gte:
1 passed in 1.89s 
E           django.db.utils.IntegrityError: new row for relation "catalog_product" violates check constraint "catalog_product_stock_check" 1 failed in 1.98s 
E           django.db.utils.IntegrityError: new row for relation "catalog_product" violates check constraint "catalog_product_stock_check" 1 failed in 1.99s 
```
Duas lições: (1) **defesa em profundidade**: o `UPDATE ... WHERE stock >= n` sozinho já impede a venda negativa (o `select_for_update` evita trabalho inútil e serializa o duplo clique); (2) remover as duas proteções produz uma falha **intermitente** (1 de 3 execuções passou), a assinatura dos bugs de concorrência, e a `CHECK constraint` do banco foi a última rede de segurança.

> 🔎 **Um achado a mais.** Ao rodar a suíte inteira em PostgreSQL com esse teste, **3 testes seguintes deram erro** (`duplicate key ... django_content_type`). Um teste com `transaction=True` (commits reais) **limpa as tabelas** no fim, inclusive os *content types* criados pelas migrações. A correção é `@pytest.mark.django_db(transaction=True, serialized_rollback=True)`, que restaura o estado. Contagem final: **PostgreSQL 143 passed, 4 skipped** (os 4 do legado, que só rodam em SQLite) · **SQLite 146 passed, 1 skipped** (a concorrência).

> 🛠️ **Correção feita depois, no módulo 9.** A primeira versão desse `conftest.py` usava `sequence_reset_by_name_sql`, que zera **todas** as sequences para 1 (é a função certa **depois de um `TRUNCATE`**). Isso é errado para tabelas que já têm linhas vindas de migrações (grupos, permissões): a próxima inserção colidia com um id existente. Só não apareceu aqui porque nenhum teste criava linhas nessas tabelas; no módulo 9, um teste que cria um grupo falhou no PostgreSQL com `duplicate key value violates unique constraint "auth_group_pkey"`. A função correta é `sequence_reset_sql(no_style(), modelos)`, que parte do **maior id existente**. O arquivo `conftest.py` de `projeto/referencia-api-m8/` já está corrigido, e a suíte continua em **146 passed (SQLite)** e **143 passed, 4 skipped (PostgreSQL)**.

**5. Descartabilidade (fator IX) e logs (fator XI).** Um Gunicorn em modo produção, com uma requisição lenta (3 s) em andamento quando chega o `SIGTERM`:
```bash
bash sigterm.sh
```
```text
== requisição normal (HSTS/HTTPS atrás de proxy):
categories -> 200
== requisição lenta em andamento + SIGTERM após 1 s:
terminei o trabalho
resposta da lenta: 200 em 3.000859s
processo encerrou depois de 2.3s do SIGTERM
== curl após encerrar:
000
conexão recusada (já saiu)
== o que o gunicorn escreveu em stdout:
[287167] [INFO] Starting gunicorn 26.2.0
[287167] [INFO] Listening at: http://127.0.0.1:8161 (287167)
[287167] [INFO] Using worker: sync
[287168] [INFO] Booting worker with pid: 287168
[287167] [INFO] Control socket listening at /run/user/1000/gunicorn.ctl
127.0.0.1 - - [08/Nov/2026:19:09:18 +0000] "GET /api/v1/categories/ HTTP/1.1" 200 52 "-" "curl/8.18.0"
[287167] [INFO] Handling signal: term
127.0.0.1 - - [08/Nov/2026:19:09:21 +0000] "GET /lenta HTTP/1.1" 200 20 "-" "curl/8.18.0"
[287168] [INFO] Worker exiting (pid: 287168)
[287167] [INFO] Shutting down: Master
```
O processo **terminou o trabalho em andamento** (resposta 200 em 3 s) e só então saiu; depois disso, a porta recusa conexões. Os logs do Gunicorn e da aplicação saíram em **stdout**, uma linha por evento, prontos para o coletor da plataforma (nada de arquivo `.log` para rotacionar dentro do contêiner). Em orquestradores (Docker, Kubernetes) lembre que o prazo entre `SIGTERM` e `SIGKILL` precisa ser **maior** que o `--graceful-timeout`.

**6. Os 12 fatores, depois da aula**
| Fator | Estado |
|---|---|
| III Config | ✅ ambiente, com falha cedo |
| IV Serviços de apoio | ✅ banco por `DATABASE_URL` (Redis/Rabbit/gateway já eram por variável) |
| IX Descartabilidade | ✅ verificado com `SIGTERM` |
| X Paridade | ✅ suíte nos dois bancos; ✔ achados corrigidos |
| XI Logs | ✅ stdout |
| VI Processos sem estado | ⚠️ o `outbox.jsonl` (arquivo local do e-mail simulado) viola o fator; em produção seria um serviço de e-mail |

## 🧠 Pausa para lógica
**Problema.** A variável `ALLOWED_HOSTS="a.com, b.com ,,"` precisa virar a lista `["a.com", "b.com"]`, e a ausência da variável deve cair em `["*"]` só em modo `DEBUG`. Escreva a função, liste 3 entradas de teste e diga por que o padrão fora do `DEBUG` é `[]`.

<details><summary>Dica</summary>Separe por vírgula, tire espaços e descarte vazios; diferencie “variável ausente” de “variável vazia”.</details>

<details><summary>Solução comentada</summary>

É o `env_list` do exemplo 2: `[v.strip() for v in valor.split(",") if v.strip()]`. Casos: `"a.com, b.com ,,"` → `["a.com","b.com"]`; ausente → padrão; `""` (vazia, mas definida) → `[]`. O padrão fora do `DEBUG` é `[]` porque o Django então **recusa qualquer host** (`DisallowedHost`): esquecer a variável **falha fechado**, em vez de aceitar qualquer cabeçalho `Host` (que habilita ataques de *host header*).
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| Chave secreta no repositório | `SECRET_KEY = "..."` no código | Variável de ambiente; **rotacione** se vazou (o histórico do git guarda) |
| `DEBUG=True` em produção | Padrão inseguro | Padrão `False` e `check --deploy` no CI |
| Processo sobe sem a chave e “funciona” | Valor padrão para segredo | Falhar cedo (`ImproperlyConfigured`) |
| Funciona em SQLite e quebra em PostgreSQL | Paridade ignorada | Rodar a suíte no banco de produção, no CI |
| Testes dependem de `id=1` | Assumem o contador reiniciado | Buscar o objeto no teste/fixture |
| Requisições perdidas a cada deploy | Processo morto com `SIGKILL` | `SIGTERM` + `--graceful-timeout` + prazo do orquestrador maior |
| Logs em arquivo dentro do contêiner | Fator XI ignorado | stdout; a plataforma coleta |
| `.env` com segredos commitado | Falta de `.gitignore` | `.env` no `.gitignore`, `.env.example` sem valores reais |
| Senha de `DATABASE_URL` com `@` quebra o parse | Falta de codificação | Codificar em URL (`%40`); o parser decodifica |

- **Segredos nunca vão para o repositório**; um `.env.example` documenta os nomes, não os valores.
- **Um mesmo artefato** (imagem) vai para todos os ambientes; só a configuração muda.
- **`check --deploy` no CI** com as variáveis de produção simuladas.

## 🧩 Exercícios
**1. Fixação.** (a) O que é “configuração” segundo os doze fatores? (b) Por que o padrão de `DEBUG` é `False`? (c) O que o `SIGTERM` gracioso evita? (d) Por que a suíte em SQLite não basta?

<details><summary>Solução</summary>

(a) O que varia entre deploys (credenciais, hosts, URLs de serviços), separado do código. (b) Para que o esquecimento caia no lado seguro. (c) Perder requisições em andamento e deixar trabalho pela metade a cada deploy. (d) Porque SQLite e PostgreSQL diferem em travas, sequências e tipos: bugs aparecem só no banco de produção (como os 29 testes (19 falhas + 10 erros) e o schema desta aula).
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` e `DATABASE_URL` vindos do ambiente, com falha cedo sem a chave
- [ ] `config/envconf.py` testado (`DATABASE_URL`, booleanos, listas)
- [ ] `LOGGING` em stdout
- [ ] `check --deploy` com as variáveis de produção simuladas, com a lista dos avisos restantes justificada
- [ ] Suíte passando em **SQLite e PostgreSQL**, com o relato de cada diferença encontrada
- [ ] `tests/test_concorrencia.py` passando em PostgreSQL
- [ ] `.env.example` (sem segredos) e `.env` no `.gitignore`
- [ ] Demonstração de `SIGTERM` gracioso com uma requisição lenta
- [ ] ADR `docs/adr/0003-configuracao-por-ambiente.md`
- [ ] Commit `refactor(config): twelve-factor configuration and postgres parity`

**3. Desafio (opcional).** Faça os testes **pararem de assumir ids**: crie uma fixture `produto` que devolve o objeto, troque os `add_item(user, 2, 2)` por `add_item(user, produto.pk, 2)` e remova o `_zera_sequences`. Rode nos dois bancos.

## 🎤 Na entrevista
- **O que são os doze fatores?** Um conjunto de práticas para apps que rodam em nuvem: uma base de código, dependências declaradas, configuração no ambiente, serviços como recursos anexados, processos sem estado, logs em stdout, paridade dev/produção, entre outras.
- **Onde ficam os segredos?** No ambiente (ou num cofre de segredos), nunca no repositório; a aplicação falha ao subir se faltarem.
- **Como encerrar um serviço sem perder requisições?** Tratar `SIGTERM`: parar de aceitar novas conexões, terminar as em andamento (`graceful-timeout`) e só então sair; o orquestrador espera mais que esse prazo antes do `SIGKILL`.
- **Por que testar no mesmo banco da produção?** Porque diferenças de travas, sequências, tipos e SQL só aparecem nele (por exemplo, `select_for_update` é ignorado no SQLite).
- **Para onde vão os logs numa app em contêiner?** Para stdout/stderr, como fluxo; a plataforma agrega e roteia.

## 📚 Para ir além
- 📄 Manifesto: [The Twelve-Factor App (pt-br)](https://12factor.net/pt_br/). Os 12 fatores originais.
- 📄 Documentação oficial: [Django — Deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/). O que `check --deploy` cobre.
- 📄 Documentação oficial: [Django — Logging](https://docs.djangoproject.com/en/5.2/topics/logging/). Handlers e `LOGGING`.
- 📄 Documentação oficial: [Django — Notas sobre bancos](https://docs.djangoproject.com/en/5.2/ref/databases/). Diferenças entre SQLite e PostgreSQL (em inglês).
- 📄 Documentação: [Gunicorn — Sinais](https://gunicorn.org/signals/). `TERM`, `HUP`, `USR2` (em inglês).
- 🐳 Imagem oficial: [postgres no Docker Hub](https://hub.docker.com/_/postgres). Variáveis e versões (em inglês).

## ✅ Checklist da aula
- [ ] Auditei o projeto contra os 12 fatores e listei o que viola
- [ ] Segredos e hosts vêm do ambiente; sem chave, o processo não sobe
- [ ] Rodei a suíte em SQLite e PostgreSQL e expliquei cada diferença
- [ ] Demonstrei `SIGTERM` gracioso e logs em stdout
- [ ] Rodei `check --deploy` e justifiquei os avisos que ficaram
