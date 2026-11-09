# 14. Configurações por ambiente, `.env` e logging

> ⏱️ ~1h30 · Módulo 5 · Pré-requisitos: [01](01-projeto-apps-mvt.md), [11](11-autenticacao.md), [13](13-estaticos-midia.md); variáveis de ambiente ([aula 0.1](../00-ambiente-ferramentas/01-terminal-e-arquivos.md))

> ⚠️ **Nota de verificação.** Como nas aulas 12 e 13, o laboratório não estava disponível: os blocos **não foram executados** e as saídas em `text` são as esperadas. Rode no seu projeto e confie na sua saída se divergir.

## 🎯 Objetivos
Ao final desta aula você consegue:
- Explicar por que **segredos e configurações não ficam no código** (princípio *12-factor*)
- Ler configuração de **variáveis de ambiente** e de um arquivo `.env` com `django-environ`, com tipos e valores padrão
- Separar o que muda por ambiente (`DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, banco) do que não muda
- Configurar **logging** com níveis, formatadores e destinos, e usar `logging.getLogger(__name__)` nos apps
- Rodar `manage.py check --deploy` e corrigir os avisos principais

## 🤔 Por que isso importa
`SECRET_KEY` no GitHub é um clássico de incidente: com ela, um atacante forja sessões e *cookies* assinados. Já “funciona na minha máquina” costuma ser configuração diferente entre ambientes. E em produção você não tem depurador: **o log é seus olhos**. Quem não sabe ler e escrever logs depura no escuro.

## 💡 Intuição (explicação simples)
Pense numa **receita** e nos **ingredientes**. A receita (código) é igual em todas as cozinhas; o que muda é a marca do açúcar, a voltagem do forno (configuração). Você não reescreve a receita em cada cozinha: deixa um **bilhete** (`.env`) colado na porta de cada uma. E o **diário de bordo** (log) registra o que aconteceu: “19:02 forno ligado”, “19:40 ALERTA: fumaça”. Registrar tudo é ruído; registrar nada é cegueira, por isso há **níveis**.

## 🔬 Como funciona por dentro
```mermaid
flowchart LR
    E[(Variáveis de ambiente\nou arquivo .env)] --> S[settings.py\nenv.bool / env.str / env.db]
    S --> D[Dev: DEBUG=True\nSQLite/Postgres local]
    S --> P[Produção: DEBUG=False\nSECRET_KEY real, Postgres, HTTPS]
```
- **12-factor, item “Config”.** Tudo o que varia entre ambientes vem do **ambiente**, não de constantes no código. O código vai para o Git; os valores, não.
- **`.env`.** Arquivo de texto `CHAVE=valor`, lido em desenvolvimento. **Nunca** vai para o Git (`.gitignore`); em seu lugar entra um `.env.example` sem segredos. Em produção, o valor vem das variáveis do servidor/contêiner/nuvem (módulos 11 e 13), não de um arquivo.
- **Variáveis de ambiente são texto.** `DEBUG=False` chega como a *string* `"False"`, que em Python é verdadeira! Por isso usamos `env.bool("DEBUG")`, que converte direito.
- **Padrão seguro.** `DEBUG` deve ter padrão **`False`** e `SECRET_KEY` **não** deve ter padrão: se faltar, o sistema não sobe (falha rápida) em vez de rodar inseguro.
- **Logging do Python.** Quatro peças: *logger* (quem registra), *level* (gravidade mínima), *handler* (para onde vai: console, arquivo) e *formatter* (como aparece). Níveis, do mais leve ao mais grave: `DEBUG < INFO < WARNING < ERROR < CRITICAL`.
- **Hierarquia de loggers.** `logging.getLogger("apps.catalog.views")` é filho de `apps.catalog` e de `apps`: configurar `"apps"` vale para todos. Por isso se usa `getLogger(__name__)`.
- **Logger do Django.** `django.request` registra erros 5xx/4xx; `django.db.backends` com nível `DEBUG` mostra as consultas SQL (só com `DEBUG=True`).
- **Em contêiner, o log vai para o `stdout`.** Quem coleta (Docker, CloudWatch) é a plataforma; o app não gerencia arquivos de log.

## 🛠️ Exemplo prático
**1. Instalando e criando o `.env`**
```bash
uv add django-environ
cat > .env.example <<'E'
# Copie para .env e ajuste. NUNCA commite o .env.
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=troque-por-uma-chave-longa-e-aleatoria
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
LOG_LEVEL=INFO
E
cp .env.example .env
printf ".env\n" >> .gitignore
git check-ignore -v .env
```
```text
.gitignore:3:.env	.env
```
Para gerar uma chave de verdade:
```bash
uv run python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

**2. `settings.py` lendo do ambiente**
```python
# config/settings.py (topo e trechos substituídos)
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),                          # padrão seguro: desligado
    DJANGO_ALLOWED_HOSTS=(list, []),
    LOG_LEVEL=(str, "INFO"),
)
environ.Env.read_env(BASE_DIR / ".env")                  # se o arquivo não existir, só usa o ambiente

SECRET_KEY = env("DJANGO_SECRET_KEY")                    # sem padrão: se faltar, falha ao subir
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

DATABASES = {"default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")}
```
`env.db()` entende URLs como `postgres://usuario:senha@host:5432/minishop` (aula 3). Isto já resolve a variável `DJANGO_DEBUG` usada na aula 13.
```bash
uv run python manage.py check
DJANGO_SECRET_KEY= uv run python manage.py check 2>&1 | tail -2
```
```text
System check identified no issues (0 silenced).
django.core.exceptions.ImproperlyConfigured: Set the DJANGO_SECRET_KEY environment variable
```
> No segundo comando, uma variável vazia no ambiente **vence** o `.env`. O importante: sem chave, não sobe. Se o seu `check` não falhar, confira se a variável está mesmo vazia ou ausente.

**3. Seguro com `DEBUG=False`**
```python
# config/settings.py (acrescentar no final)
if not DEBUG:
    SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30              # comece pequeno; só aumente quando tiver certeza do HTTPS
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")   # atrás de proxy/ALB que termina o TLS
    CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])
```
`SECURE_PROXY_SSL_HEADER` só deve ser ligado se o seu proxy **sempre** define esse cabeçalho (senão um cliente pode forjá-lo). Será configurado no deploy (módulos 11 e 13).
```bash
DJANGO_DEBUG=False DJANGO_ALLOWED_HOSTS=minishop.exemplo.com uv run python manage.py check --deploy
```
```text
System check identified no issues (0 silenced).
```
Antes das linhas acima, o `check --deploy` lista avisos como `security.W004` (HSTS), `W008` (SSL redirect), `W012`/`W016` (cookies seguros) e `W018` (`DEBUG` ligado). Cada um tem um código: pesquise-o na documentação.

**4. Logging**
```python
# config/settings.py
LOG_LEVEL = env("LOG_LEVEL")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,                   # não silencia loggers das bibliotecas
    "formatters": {
        "simples": {"format": "{asctime} {levelname:<8} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simples"},   # stdout/stderr
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "apps": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},   # o NOSSO código
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
```
**5. Usando o logger no código**
```python
import logging

from django.contrib import messages

logger = logging.getLogger(__name__)                     # "apps.catalog.views_forms"


class ProductUpdateView(PermissionRequiredMixin, UpdateView):
    ...

    def form_valid(self, form):
        antigo = self.get_object().price
        resposta = super().form_valid(form)
        if self.object.price != antigo:
            logger.info("price_changed sku=%s old=%s new=%s user=%s",
                        self.object.sku, antigo, self.object.price, self.request.user.pk)
        messages.success(self.request, f"Produto {self.object.sku} atualizado.")
        return resposta

    def form_invalid(self, form):
        logger.warning("product_update_invalid sku=%s errors=%s", self.object.sku, list(form.errors))
        return super().form_invalid(form)
```
Ao editar um preço pelo navegador, o terminal do `runserver` mostra algo assim:
```text
2026-11-08 14:02:11,418 INFO     apps.catalog.views_forms: price_changed sku=MNT-001 old=1299.00 new=1199.00 user=3
```
Três regras que aparecem no código:
- **`logger.info("… %s", valor)`**, não f-string: a mensagem só é montada se o nível estiver ativo.
- **Nunca** registre senha, token, cartão ou CPF completo. Registre **ids**, não dados pessoais.
- Para exceções, `logger.exception("falha ao …")` dentro do `except` inclui o *traceback*.

**6. Testes**
```python
import logging

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_alterar_preco_gera_log(client, gerente, produto, caplog):
    client.force_login(gerente)                          # fixtures das aulas 12 e 13
    dados = {"category": produto.category_id, "sku": produto.sku, "name": produto.name,
             "price": "1.00", "stock": produto.stock, "is_active": "on"}
    with caplog.at_level(logging.INFO, logger="apps"):
        client.post(reverse("catalog:update", args=[produto.slug]), dados)
    assert any("price_changed" in m and produto.sku in m for m in caplog.messages)


def test_settings_nao_tem_segredo_no_codigo():
    from pathlib import Path
    texto = Path("config/settings.py").read_text()
    assert "django-insecure" not in texto


def test_debug_tem_padrao_desligado(monkeypatch):
    import environ
    monkeypatch.delenv("DJANGO_DEBUG", raising=False)
    env = environ.Env(DJANGO_DEBUG=(bool, False))
    assert env("DJANGO_DEBUG") is False


@pytest.mark.parametrize("texto,esperado", [("True", True), ("true", True), ("1", True), ("False", False), ("0", False)])
def test_bool_do_ambiente_converte_direito(monkeypatch, texto, esperado):
    import environ
    monkeypatch.setenv("X", texto)
    assert environ.Env().bool("X") is esperado
```
```bash
uv run pytest -q
```
```text
.......................................................................... [100%]
```
O teste do `caplog` usa `logger="apps"` porque o logger do app tem `propagate=False`: o `caplog` precisa estar no mesmo ponto da hierarquia. Se o seu falhar por isso, é aí que se olha.

## 🧠 Pausa para lógica
**Problema (leitor de `.env`).** Escreva `ler_env(texto)` que devolve um dicionário a partir de linhas `CHAVE=valor`, ignorando linhas vazias e comentários (`#`), aceitando aspas ao redor do valor e `=` dentro do valor (`URL=a=b`), e **rejeitando** linhas sem `=`.

<details><summary>Dica</summary>
<code>linha.partition("=")</code> divide só no <strong>primeiro</strong> <code>=</code>. Tire espaços com <code>strip()</code> e aspas simétricas com cuidado.
</details>

<details><summary>Solução comentada</summary>

```python
def ler_env(texto):
    resultado = {}
    for numero, linha in enumerate(texto.splitlines(), start=1):
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        chave, igual, valor = linha.partition("=")          # só o primeiro "="
        if not igual or not chave.strip():
            raise ValueError(f"linha {numero} inválida: {linha!r}")
        valor = valor.strip()
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
            valor = valor[1:-1]
        resultado[chave.strip()] = valor
    return resultado


exemplo = """
# banco
DATABASE_URL=postgres://u:p@db:5432/x?sslmode=require
SECRET="com espaços = e igual"

DEBUG=False
"""
print(ler_env(exemplo))
try:
    ler_env("QUEBRADA")
except ValueError as e:
    print("erro:", e)
```
```text
{'DATABASE_URL': 'postgres://u:p@db:5432/x?sslmode=require', 'SECRET': 'com espaços = e igual', 'DEBUG': 'False'}
erro: linha 1 inválida: 'QUEBRADA'
```
Repare que `DEBUG` ficou como a *string* `'False'`: converter tipos é papel de quem lê (`env.bool`).
</details>

## ⚠️ Erros comuns e boas práticas
| Mensagem / sintoma | Causa | Solução |
|---|---|---|
| `ImproperlyConfigured: Set the DJANGO_SECRET_KEY environment variable` | Variável ausente | Crie o `.env` a partir do `.env.example` |
| `CommandError: You must set settings.ALLOWED_HOSTS if DEBUG is False` | `DEBUG=False` sem hosts | Defina `DJANGO_ALLOWED_HOSTS` |
| `DisallowedHost: Invalid HTTP_HOST header` | Host fora de `ALLOWED_HOSTS` | Acrescente o domínio |
| `DEBUG=False` mas o Django age como ligado | `"False"` lido como texto verdadeiro | `env.bool(...)`, nunca `bool(os.environ[...])` |
| `CSRF verification failed` atrás de HTTPS/proxy | Falta `CSRF_TRUSTED_ORIGINS` e/ou cabeçalho do proxy | Configure ambos (com `https://`) |
| Redirecionamento infinito com `SECURE_SSL_REDIRECT` | Proxy termina o TLS e o Django não sabe | `SECURE_PROXY_SSL_HEADER` correto |
| Nenhum log aparece | Nível do logger acima do nível da mensagem, ou `propagate`/handler faltando | Confira `level`, `handlers` e o nome do logger |
| Logs duplicados | Logger e `root` com o mesmo handler e `propagate=True` | `propagate: False` no logger filho |
| `.env` foi para o Git | Esqueceu o `.gitignore` | **Troque a chave** (apagar o commit não basta: ela já vazou) |

- Em produção, defina variáveis no servidor; **não envie o `.env`** para ele.
- `DEBUG=True` em produção expõe código, variáveis e configurações nas páginas de erro.
- Mensagens de log com contexto (`sku=`, `user=`) permitem filtrar depois; o módulo 14 trata de logs estruturados em JSON.
- Níveis: `DEBUG` detalhe de desenvolvimento · `INFO` fatos normais · `WARNING` algo estranho · `ERROR` falha numa operação · `CRITICAL` o sistema está em risco.

## 🧩 Exercícios
**1. Fixação**
(a) Por que `SECRET_KEY` não pode ir para o Git? (b) Por que `DEBUG` deve ter padrão `False`? (c) O que significa `propagate: False`? (d) Diferença entre `logger.error` e `logger.exception`?

<details><summary>Solução</summary>

(a) Ela assina sessões, tokens e *cookies*; quem a tem forja dados e pode, dependendo do caso, executar código. (b) Se esquecerem de configurar em produção, o erro é o lado seguro. (c) A mensagem não sobe para os handlers dos loggers pais (evita duplicar). (d) `exception` só vale dentro de `except` e inclui o *traceback*.
</details>

**2. Aplicação no projeto MiniShop**
Prepare o projeto para sair do seu computador.

Critérios de pronto:
- [ ] `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` e `DATABASE_URL` vêm do ambiente; `.env.example` versionado, `.env` ignorado
- [ ] `manage.py check --deploy` com `DEBUG=False` sem avisos de segurança
- [ ] `LOGGING` com console e nível controlado por `LOG_LEVEL`
- [ ] Log `INFO` ao alterar preço, `WARNING` em formulário inválido e `exception` em falha inesperada
- [ ] Teste de que nenhum segredo está no código e de que o `DEBUG` tem padrão desligado
- [ ] `docs/configuracao.md` com a tabela de variáveis (nome, obrigatória?, exemplo)
- [ ] Commit `chore(config): environment-based settings and logging`

<details><summary>Solução de referência (tabela)</summary>

| Variável | Obrigatória | Exemplo |
|---|---|---|
| `DJANGO_SECRET_KEY` | sim | (aleatória, 50+ caracteres) |
| `DJANGO_DEBUG` | não (padrão `False`) | `True` |
| `DJANGO_ALLOWED_HOSTS` | em produção | `minishop.exemplo.com` |
| `DATABASE_URL` | não (padrão SQLite) | `postgres://user:senha@db:5432/minishop` |
| `LOG_LEVEL` | não (padrão `INFO`) | `DEBUG` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | atrás de HTTPS | `https://minishop.exemplo.com` |
</details>

**3. Desafio (opcional)**
Crie um `logging.Filter` que acrescente a cada registro um `request_id` (gerado por um *middleware* e guardado em `contextvars`) e mostre-o no formato do log. Assim, todas as linhas de uma mesma requisição ficam ligadas.

## 🎤 Na entrevista
- **Como você gerencia segredos e configuração?** Variáveis de ambiente (12-factor), `.env` só em desenvolvimento e fora do Git, `.env.example` como documentação; em produção, o gerenciador da plataforma (AWS Parameter Store/Secrets Manager).
- **O que você muda ao colocar o Django em produção?** `DEBUG=False`, `SECRET_KEY` própria, `ALLOWED_HOSTS`, banco real, HTTPS com *cookies* seguros e HSTS, estáticos coletados, logs no `stdout`; confirmo com `check --deploy`.
- **Quando usar cada nível de log?** `DEBUG` detalhe; `INFO` eventos normais relevantes; `WARNING` situação inesperada, mas tolerável; `ERROR` falha; `CRITICAL` sistema comprometido. Sem dados sensíveis.

## 📚 Para ir além
- 📄 Documentação oficial: [Configurações do Django](https://docs.djangoproject.com/en/5.2/topics/settings/). Como as configurações funcionam.
- 📄 Documentação oficial: [Checklist de implantação](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/). Base do `check --deploy`.
- 📄 Documentação oficial: [Logging no Django](https://docs.djangoproject.com/en/5.2/topics/logging/). Loggers, handlers e `LOGGING`.
- 📄 Documentação oficial: [Logging HOWTO (Python)](https://docs.python.org/3/howto/logging.html). A base, em português do assunto: níveis e hierarquia.
- 📑 Artigo/tutorial: [The Twelve-Factor App — Config](https://12factor.net/config). A ideia original, curta.
- 📄 Documentação: [django-environ](https://django-environ.readthedocs.io/). Tipos suportados e `env.db()`.
- 🏋️ Prática extra: ative `django.db.backends` em `DEBUG` e conte as consultas de uma tela (relaciona-se à aula 07).

> Links verificados em 2026-11-08 (HTTP 200).

## ✅ Checklist da aula
- [ ] Nenhum segredo no código; `.env` ignorado e `.env.example` versionado
- [ ] `DEBUG` com padrão seguro e `SECRET_KEY` obrigatória
- [ ] `check --deploy` sem avisos de segurança com `DEBUG=False`
- [ ] `LOGGING` configurado e `getLogger(__name__)` nos apps
- [ ] Sei os níveis de log e o que nunca registrar
