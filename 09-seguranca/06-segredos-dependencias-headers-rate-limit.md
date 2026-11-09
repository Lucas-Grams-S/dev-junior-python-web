# 6. Segredos, dependências, cabeçalhos e limitação de taxa

> ⏱️ ~1h30 · Módulo 9 · Pré-requisitos: [9.01](01-owasp-ameacas.md), [9.05](05-controle-acesso-idor.md), [8.06 (twelve-factor)](../08-arquitetura/06-twelve-factor.md)

> ✅ **Verificação.** Tudo executado em 2026-11-08 no laboratório do MiniShop (Python 3.13, Django 5.2.19; `pip-audit`, `detect-secrets`, Gunicorn 26.2 com 2 workers, Redis 8 num contêiner **meu**, que removi depois). **As saídas são reais.** Esta aula **fecha os achados abertos** da auditoria da aula 01: cabeçalhos (A02), rotas expostas (A02), dependências (A03), segredos e log de eventos (A09) e a limitação de taxa.

## 🎯 Objetivos
- Manter **segredos fora do repositório**, **varrê-los** com ferramenta e saber o que fazer quando um vaza
- Auditar **dependências** com `pip-audit` e entender o risco da **cadeia de suprimentos** (A03)
- Ativar **cabeçalhos de segurança** (CSP, HSTS, `nosniff`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`) e conferi-los por teste
- **Reduzir a superfície exposta** (rotas de demonstração, documentação, painel administrativo)
- Registrar **eventos de segurança** (login falho, acesso negado, limite excedido) sem vazar dados nem permitir *log injection*
- Entender que a **limitação de taxa depende do cache compartilhado** (medido com 2 workers)

## 🤔 Por que isso importa
A maioria dos incidentes reais não vem de ataques sofisticados: vem de **uma chave no repositório**, **uma biblioteca desatualizada com falha conhecida**, **um painel esquecido aberto** ou **ninguém ter percebido** a varredura de senhas durante horas. Essas quatro coisas são a parte “de higiene” da segurança: baratas de fazer, caras de ignorar. São os itens A02, A03 e A09 do OWASP Top 10:2025.

## 💡 Intuição (explicação simples)
É a manutenção do prédio: **guardar as chaves num cofre** e não no tapete da porta (segredos); **verificar se as peças compradas de terceiros têm recall** (dependências); **fechar as portas de serviço e tirar as placas “entrada de funcionários” da rua** (superfície exposta e cabeçalhos); e **ter câmeras e livro de ocorrências** para saber quem tentou entrar (logs). E lembrar que o **porteiro** (limite de tentativas) precisa **conversar com os outros porteiros**: se cada um conta as tentativas sozinho, o infrator multiplica suas chances pelo número de porteiros.

## 🔬 Como funciona por dentro
- **Segredos** (chaves de API, senhas de banco, `SECRET_KEY`): vivem **no ambiente** (aula 8.06) ou num cofre (AWS Secrets Manager no módulo 13), **nunca no Git**. O Git guarda **o histórico para sempre**: apagar o arquivo no commit seguinte **não remove** o segredo. Se vazou: (1) **revogar/rotacionar** imediatamente, (2) avaliar o uso indevido nos logs do provedor, (3) só então limpar o histórico (o item 1 é o que importa). Ferramentas de varredura (`detect-secrets`, `gitleaks`, o *push protection* do GitHub) procuram padrões de chaves conhecidas e textos de alta entropia; têm **falsos positivos** e **falsos negativos**, então são uma rede de segurança, não uma garantia.
- **Dependências (A03):** seu código é uma fração pequena do que roda. As bibliotecas (e as delas) podem ter **CVEs** (falhas públicas catalogadas) ou ser **maliciosas** (nomes parecidos, *typosquatting*; contas de mantenedores comprometidas). Defesas: **travar versões** (`uv.lock`), **auditar** (`pip-audit` consulta bases de vulnerabilidades), **atualizar com regularidade** (Dependabot/Renovate abrem PRs), conferir **hashes**, reduzir o número de dependências e rever o que se instala.
- **Cabeçalhos de segurança:** instruções que o servidor dá ao navegador:
  | Cabeçalho | O que faz |
  |---|---|
  | `Content-Security-Policy` (CSP) | limita de onde scripts, estilos e imagens podem vir; segunda camada contra XSS |
  | `Strict-Transport-Security` (HSTS) | “fale comigo só por HTTPS” durante `max-age` segundos |
  | `X-Content-Type-Options: nosniff` | o navegador não “adivinha” o tipo do conteúdo |
  | `X-Frame-Options: DENY` / `frame-ancestors` | impede que o site seja colocado em `<iframe>` de outro (*clickjacking*) |
  | `Referrer-Policy` | controla quanto da URL anterior vai no cabeçalho `Referer` |
  | `Permissions-Policy` | desliga recursos do navegador (câmera, microfone, geolocalização) que o site não usa |
  | `Cross-Origin-Opener-Policy` | isola a janela de outras origens |
  Para uma **API JSON**, a CSP pode ser radical (`default-src 'none'`): a resposta não deve carregar nada. Telas de documentação e painel precisam de políticas mais abertas, **só nas suas rotas**.
- **HSTS é difícil de desfazer:** o navegador obedece pelo `max-age` inteiro. Comece com **valores baixos** (horas), aumente aos poucos e só use `includeSubDomains` e `preload` quando **todos** os subdomínios forem HTTPS.
- **Superfície de ataque:** tudo que está exposto pode ser usado. Rotas de demonstração, documentação interativa e painel administrativo **não precisam** estar públicos em produção por padrão: ligue por **decisão** (variável de ambiente), proteja com rede/VPN/autenticação adicional e, no caso do admin, considere trocar o caminho (reduz varredura automática, **não** substitui senha forte e MFA).
- **Logs de segurança (A09):** registre **eventos**: login falho (usuário, IP, quando), acesso negado, limite excedido, mudança de permissão, ações sensíveis. **Nunca** registre senhas, tokens ou dados pessoais desnecessários. **Sanitize** o que vem do usuário antes de registrar (*log injection*: um nome de usuário com `\n` forjaria uma linha de log). Sem alertas, o log vira só um arquivo; o ideal é alertar sobre padrões (muitos `login_failed` do mesmo IP).
- **Limitação de taxa:** o `throttling` do DRF guarda o contador no **cache do Django**. O cache padrão (`LocMemCache`) é **da memória de cada processo**: com `N` workers, cada um conta por conta própria e o limite real chega perto de `N × limite`. Em produção o cache precisa ser **compartilhado** (Redis). E **atrás de um proxy**, o IP da conexão é o do proxy: configure `NUM_PROXIES` para ler o IP real do cliente sem confiar cegamente no cabeçalho `X-Forwarded-For`.

## 🛠️ Exemplo prático
**1. Segredos: o que a varredura achou e o que descartei** (`detect-secrets scan --all-files`)
```bash
uv run detect-secrets scan --all-files --exclude-files '(\.venv|uv\.lock|\.git/|__pycache__|\.sqlite3|node_modules|schema\.yml|_cache)' .
```
```text
  .env.example:5  Basic Auth Credentials
  aula06.py:48  Secret Keyword
  aula09.py:40  Secret Keyword
  config/envconf.py:21  Basic Auth Credentials
  docs/adr/0003-configuracao-por-ambiente.md:9  Secret Keyword
  arquivos com achados: 5
```
Os cinco achados são **falsos positivos ou placeholders**: o exemplo `postgres://usuario:senha@host/...` do `.env.example` e de uma *docstring*, um parágrafo do ADR e dois scripts de experimento antigos da série com a senha de desenvolvimento. **Dois cuidados que apareceram aqui:**
- Minha **primeira execução disse “0 achados”** e estava errada: por padrão o `detect-secrets` só varre arquivos **rastreados pelo Git**, e a pasta não era um repositório. Só com `--all-files` ele leu tudo. Validei o instrumento plantando num arquivo temporário a chave de **exemplo** que a documentação da AWS publica (`AKIAIOSFODNN7EXAMPLE`): ele a achou como `AWS Access Key`; removi o arquivo.
- Ele **não** sinalizou a senha `dev-somente-local-123` do `seed` (ela não tem “cara” de segredo). Isso é uma limitação real das heurísticas, e o risco era concreto: o comando `seed` cria usuários com senha **conhecida**. Correção: o comando agora **recusa rodar** fora do desenvolvimento (`ALLOW_SEED`, calculado a partir de `DEBUG`) e há teste. *(Nota: usei uma configuração própria porque o pytest-django força `settings.DEBUG = False` durante os testes.)*

**2. Dependências: `pip-audit` sobre as versões travadas**
```bash
uv export --no-hashes --no-emit-project -o requirements.txt
uv run pip-audit -r requirements.txt --no-deps --disable-pip
```
```text
No known vulnerabilities found          (124 pacotes travados)
```
“Nenhuma vulnerabilidade” só tem valor se a ferramenta realmente as enxerga, então **validei** contra uma lista descartável com versões antigas (`django==3.2.0`, `requests==2.19.0`, fora do projeto): ele apontou **75 vulnerabilidades conhecidas** em 2 pacotes, com os identificadores (`PYSEC-2021-8`…) e as versões que corrigem. Duas ressalvas honestas: (1) a ferramenta só conhece o que está **publicado** numa base de vulnerabilidades (nada de falhas ainda não divulgadas); (2) “não vulnerável” hoje não é “não vulnerável” amanhã, por isso a verificação entra no CI e roda **periodicamente**.

**3. Cabeçalhos: antes e depois.** A auditoria da aula 01 apontou `Content-Security-Policy` e `Permissions-Policy` ausentes. A solução é um *middleware* pequeno, que dá CSP **diferente por área** (`config/security_headers.py`):
```python
"""Cabeçalhos de segurança que o Django 5.2 não envia sozinho: Content-Security-Policy e Permissions-Policy."""
API = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
DOCS = ("default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://cdn.jsdelivr.net; worker-src blob:; frame-ancestors 'none'; base-uri 'self'")
ADMIN = "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
PERMISSOES = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        resp = self.get_response(request)
        caminho = request.path
        if caminho.startswith(("/api/docs", "/api/redoc")):
            csp = DOCS
        elif caminho.startswith("/admin") or caminho.lstrip("/").startswith(self._admin()):
            csp = ADMIN
        else:
            csp = API
        resp.headers.setdefault("Content-Security-Policy", csp)
        resp.headers.setdefault("Permissions-Policy", PERMISSOES)
        return resp

    @staticmethod
    def _admin():
        from django.conf import settings
        return settings.ADMIN_URL
```
E a resposta real do MiniShop em modo produção (`DEBUG=0`, requisição HTTPS):
```text
GET /api/v1/categories/ → 200
   Strict-Transport-Security: max-age=3600
   Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'
   X-Content-Type-Options: nosniff
   X-Frame-Options: DENY
   Referrer-Policy: same-origin
   Cross-Origin-Opener-Policy: same-origin
   Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()
GET /admin/login/ → 200
   Strict-Transport-Security: max-age=3600
   Content-Security-Policy: default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'
   X-Content-Type-Options: nosniff
   X-Frame-Options: DENY
   Referrer-Policy: same-origin
   Cross-Origin-Opener-Policy: same-origin
   Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()
```
- A **API** recebe `default-src 'none'`: ela devolve só JSON, não precisa carregar nada.
- O **admin** recebe uma CSP própria, que permite o que ele usa e nada além.
- O **HSTS** começou em `max-age=3600` (1 h) de propósito; subir para meses só depois de confirmar que tudo funciona em HTTPS.
- Em `settings.py`: `X_FRAME_OPTIONS = "DENY"`, `SECURE_REFERRER_POLICY = "same-origin"`, `SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"`, e o *middleware* `XFrameOptionsMiddleware` agora vale em **todos** os ambientes (antes só em produção).
- Teste (`tests/test_endurecimento.py`): a API tem a CSP restritiva e todos os cabeçalhos; admin e documentação têm CSP própria **sem afrouxar a da API**; ao tirar o *middleware*, 2 testes **falharam** (validação por mutação) e voltaram a passar ao restaurá-lo.

**4. Reduzindo a superfície exposta.** Em `config/urls.py`: as rotas de demonstração (`/demo/*`) só existem com `DEBUG`; a documentação (`/api/docs`, `/api/redoc`, `/api/schema`) só com `EXPOSE_DOCS=1` (ou em `DEBUG`); o caminho do admin vem de `ADMIN_URL`. O teste sobe um **processo em modo produção** e faz as requisições de verdade:
```text
produção, sem variáveis extras:  /demo/sync/ → NAO_EXISTE · /api/docs/ → NAO_EXISTE · /api/schema/ → NAO_EXISTE · /admin/login/ → EXISTE
EXPOSE_DOCS=1:                   /api/docs/ → EXISTE (e /demo/sync/ continua NAO_EXISTE)
ADMIN_URL=painel-interno:        /admin/login/ → NAO_EXISTE · /painel-interno/login/ → EXISTE
```
> 🔎 **Um tropeço instrutivo.** Meu primeiro teste usou `resolve("/api/docs/")` e “achou” a rota mesmo desligada: o padrão `api/<str:version>/` captura qualquer texto (`docs` virou uma “versão”), e a resposta real é `404`. A verificação confiável é a **requisição**, não a existência de um padrão.

**5. Eventos de segurança (A09)** (`apps/accounts/receivers.py` e o tratador de erros):
```python
"""Eventos de segurança: quem tentou, quando e de onde (nunca a senha)."""
import logging

from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver

seguranca = logging.getLogger("security")


def limpo(valor, limite=64):
    """Evita *log injection*: sem quebras de linha nem caracteres de controle, e com tamanho limitado."""
    return "".join(ch if ch.isprintable() else "?" for ch in str(valor))[:limite]


def ip_do_cliente(request):
    if request is None:
        return "-"
    return limpo(request.META.get("REMOTE_ADDR", "-"), 45)


@receiver(user_login_failed)
def registrar_login_falho(sender, credentials, request=None, **kwargs):
    seguranca.warning("login_failed username=%s ip=%s", limpo(credentials.get("username", "-")), ip_do_cliente(request))
```
Agora o log tem **quem, de onde e o quê**, sem a senha. Trechos reais da auditoria:
```text
login_failed username=cliente ip=127.0.0.1
access_denied user=3 path=/api/v1/products/
rate_limited user=None path=/api/v1/auth/token/
```
Testes: o login falho aparece com o usuário e o IP (`203.0.113.7` num endereço de documentação) e **a senha digitada não aparece**; o acesso negado é registrado; e `limpo("maria\nlogin_ok username=admin")` devolve `maria?login_ok username=admin` (a quebra de linha vira `?`, então não se forja uma linha de log).

**6. Limitação de taxa com mais de um worker** (`limite_workers.sh`: 14 tentativas de login seguidas contra um Gunicorn com **2 workers**; limite configurado `5/min`)
```text
limite configurado: login = 5/min; 14 tentativas seguidas contra 2 workers
cache_local_por_processo: 401 401 401 401 401 401 429 401 401 429 429 401 401 429
   passaram (401): 10 · bloqueadas (429): 4
cache_compartilhado_redis: 401 401 401 401 401 429 429 429 429 429 429 429 429 429
   passaram (401): 5 · bloqueadas (429): 9
```
- **Cache local (padrão):** passaram **10** tentativas (o dobro do limite) e só 4 foram bloqueadas: cada worker mantém o seu contador (observe o `429` intercalado com `401`).
- **Cache compartilhado (Redis):** passaram **5** e 9 foram bloqueadas, o limite real.
A configuração é uma variável (`REDIS_CACHE_URL`), que troca o backend para `RedisCache`, e há teste que a aciona. **Atrás de proxy:** o teste mostra que, com `NUM_PROXIES=1`, o IP usado é o **último** adicionado pelo seu proxy (`203.0.113.9`), e com `NUM_PROXIES=0` ignora o cabeçalho e usa o da conexão. Se o `X-Forwarded-For` for confiado sem critério, o atacante forja o IP e escapa do limite.

**7. Reauditoria**
```text
Item  Resultado   Verificação → evidência
A01   OK          Anônimo lista pedidos? → GET /orders/ sem token → 401
A01   OK          Outro usuário lê o pedido de 'cliente' (IDOR)? → GET /orders/1/ como estoquista → 404
A01   OK          Outro usuário cancela o pedido? → POST /orders/1/cancel/ → 404
A01   OK          Cliente comum cria produto? → POST /products/ como cliente → 403
A02   OK          Cabeçalhos de segurança presentes? → ausentes: 
A02   OK          /demo/sync/ exposto em produção? → GET /demo/sync/ → 404
A02   ATENÇÃO     /admin/login/ exposto em produção? → GET /admin/login/ → 200
A02   OK          /api/docs/ exposto em produção? → GET /api/docs/ → 404
A02   OK          DEBUG desligado? → DEBUG=False
A03   NÃO MEDIDO  Dependências auditadas (pip-audit)? → veja a aula 9.06
A04   OK          Algoritmo de hash de senhas → Argon2PasswordHasher (primeiro da lista PASSWORD_HASHERS; os demais só verificam senhas antigas)
A04   ATENÇÃO     JWT assinado com → HS256 usando a SECRET_KEY da aplicação (a mesma chave assina sessões)
A05   ATENÇÃO     SQL cru, mark_safe ou csrf_exempt no código? → 2 ocorrência(s): apps/payments/api.py:4:from django.views.decorators.csrf import csrf_exempt | apps/payments/api.py:16:@csrf_exempt                                                  # nã
A05   OK          Busca resiste a ' OR 1=1 --? → GET /products/?search=' OR 1=1 -- → 200, 0 resultados
A06   OK          Quantidade negativa no carrinho? → POST quantity=-5 → 400
A06   OK          Auto-promoção a gerente (mass assignment)? → PATCH /auth/me/ role=manager → 405
A07   OK          Erro de login revela se o usuário existe? → usuário inexistente → 401; senha errada → 401; corpos iguais: True
A07   OK          Tentativas de login são limitadas? → 7 tentativas seguidas → [401, 401, 401, 401, 401, 429, 429]
A07   OK          Há validadores de senha? → AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'}, {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}}, {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'}, {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}]
A08   OK          Webhook exige assinatura? → HMAC + timestamp (aula 7.09); sem assinatura → 401
A08   OK          Celery aceita só JSON (sem pickle)? → CELERY_ACCEPT_CONTENT = ['json']
A09   OK          Login falho registra QUEM tentou (usuário/IP)? → mensagens geradas: ['login_failed username=cliente ip=127.0.0.1', 'Unauthorized: /api/v1/auth/token/']
A10   OK          JSON quebrado vira erro limpo (sem stack trace)? → POST /cart/items/ com corpo inválido → 400 {"detail":"JSON parse error - Expecting property name enclosed in double quotes: line 1 column 2 (char 1)","code":"parse
A10   ATENÇÃO     Com DEBUG=1 a página 404 vaza o mapa de rotas? → (status, mostra rotas) = 404 True  ← por isso DEBUG=0 em produção

resumo: {"OK": 19, "ATENÇÃO": 4, "NÃO MEDIDO": 1}
```
De `{"OK": 14, "FALHA": 3, "ATENÇÃO": 6}` na aula 01 para **`{"OK": 19, "ATENÇÃO": 4, "NÃO MEDIDO": 1}`, sem nenhuma falha**. As quatro “atenção” restantes são **decisões conscientes**: o admin existe (por design, com o caminho configurável); o JWT usa HS256 com a chave da aplicação (aceitável, mas uma chave de assinatura separada é melhoria); o `csrf_exempt` do webhook (justificado); e o `DEBUG=1` revelar o mapa de rotas (por isso nunca em produção). O item A03 aparece “não medido” na tabela porque a medição é este `pip-audit`, feito à parte. Suíte do laboratório: **229 passed, 1 skipped**; `lint-imports`, `ruff S` e `spectacular --validate --fail-on-warn` limpos.

## 🧠 Pausa para lógica
**Problema.** O limite de login é 5 por minuto por IP. Quantas tentativas de adivinhar a senha de **uma conta** um atacante consegue por hora (a) com 1 worker, (b) com 4 workers e cache local, (c) com 4 workers e Redis, (d) se ele controlar 100 IPs diferentes com Redis? O que isso diz sobre a defesa?

<details><summary>Dica</summary>Multiplique o limite por minuto por 60; depois considere quantos contadores independentes existem.</details>

<details><summary>Solução comentada</summary>

(a) 5 × 60 = **300**/h. (b) até 4 × 300 = **1 200**/h (cada worker conta à parte; na medição, 2 workers deixaram passar o dobro). (c) **300**/h (contador único). (d) 100 × 300 = **30 000**/h: o limite **por IP** não protege **uma conta** contra um ataque distribuído. Conclusões: limite por IP é só uma camada; some **limite por conta** (atraso progressivo, não bloqueio total, que viraria negação de serviço contra a vítima), **senhas fortes e validadas** (aula 04), **MFA**, e **alertas** sobre muitas falhas na mesma conta vindas de IPs diferentes (os logs de segurança desta aula).
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| Chave de API no repositório | “Só pra testar” | Variável de ambiente / cofre; varredura no pré-commit e no CI |
| Segredo vazado e só apagado no commit seguinte | O Git guarda o histórico | **Rotacionar** primeiro; depois limpar |
| `.env` versionado | Falta do `.gitignore` | `.env` ignorado; `.env.example` sem valores reais |
| Ferramenta de segredos “limpa”, mas lendo só arquivos rastreados | Configuração padrão | `--all-files` e validar com uma chave de exemplo |
| `pip-audit` rodando só uma vez | Falsa sensação de segurança | Agendar no CI e em intervalos; Dependabot/Renovate |
| Dependências sem versão travada | `pip install` solto | `uv.lock` e `uv sync --frozen` no deploy |
| CSP com `unsafe-inline` e `*` em tudo | “Funcionar” de qualquer jeito | Política mínima por área; relaxar só onde necessário |
| HSTS de 1 ano logo no primeiro dia | Pressa | Começar com horas; `preload` só com todos os subdomínios em HTTPS |
| Docs, demo e admin públicos em produção | Padrão de desenvolvimento | Ligar por decisão, proteger e/ou isolar |
| Log com senha/token/dados pessoais | Registrar o corpo inteiro | Registrar eventos e identificadores, não segredos |
| Entrada do usuário direto no log | *Log injection* | Sanitizar quebras de linha e limitar tamanho |
| Limite de taxa com cache local e vários workers | Contador por processo | Cache compartilhado (Redis) |
| Todos os usuários atrás do proxy com o mesmo IP | `NUM_PROXIES` ausente | Configurar o número de proxies confiáveis |

- **Higiene automática vale mais que boa vontade:** coloque varredura de segredos, `pip-audit` e `ruff S` no CI (módulo 12).
- **Atualize em intervalos curtos:** muitas pequenas atualizações são mais seguras que uma grande a cada dois anos.
- **Ligue por decisão, desligue por padrão.**

## 🧩 Exercícios
**1. Fixação.** (a) Por que apagar um segredo do último commit não resolve? (b) O que o `pip-audit` não encontra? (c) Para que serve a CSP se o framework já escapa a saída? (d) Por que o cache local falha com mais de um worker?

<details><summary>Solução</summary>

(a) O histórico do Git guarda o segredo; quem clonou ou tem o remoto o vê. É preciso revogar/rotacionar. (b) Falhas ainda não divulgadas, pacotes maliciosos que não têm CVE, e problemas de configuração; só olha versões contra uma base conhecida. (c) Defesa em profundidade: se um XSS escapar, a CSP limita o que o script pode fazer ou carregar. (d) Cada processo mantém o seu contador na memória; N workers dão cerca de N vezes o limite.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] `detect-secrets` (com `--all-files`) rodando, com o resultado **triado** (cada achado justificado) e um *baseline* versionado
- [ ] `pip-audit` limpo e **validado** contra um pacote sabidamente vulnerável; agendado no CI
- [ ] Middleware com CSP, `Permissions-Policy` e demais cabeçalhos, com testes por rota e validação por mutação
- [ ] Rotas de demonstração e documentação desligadas em produção por padrão; `ADMIN_URL` configurável
- [ ] Eventos `login_failed`, `access_denied` e `rate_limited` com *log injection* neutralizado e sem senhas
- [ ] `REDIS_CACHE_URL` em produção e `NUM_PROXIES` documentado; medição do limite com 2 workers
- [ ] Reauditoria (`auditoria.py`) sem `FALHA`, com as “atenção” restantes justificadas em `docs/seguranca.md`
- [ ] Commit `feat(security): headers, exposure, security events and shared throttle cache`

**3. Desafio (opcional).** Acrescente ao limite de login um contador **por conta** (atraso progressivo, por exemplo 1 s, 2 s, 4 s… até 60 s, guardado no Redis) e mostre que um ataque com vários IPs contra a mesma conta é desacelerado sem bloquear o dono legítimo.

## 🎤 Na entrevista
- **O que fazer quando um segredo vaza no Git?** Revogar e rotacionar imediatamente, verificar o uso indevido nos logs do provedor, e só depois (se necessário) limpar o histórico; apagar o arquivo não basta.
- **Como você gerencia vulnerabilidades em dependências?** Versões travadas, auditoria automatizada (`pip-audit`/Dependabot) no CI e periódica, atualizações pequenas e frequentes, e menos dependências.
- **O que é CSP?** Uma política enviada pelo servidor que limita de onde scripts, estilos e outros recursos podem ser carregados; é uma camada extra contra XSS.
- **O que é HSTS e qual o cuidado?** Instrui o navegador a usar só HTTPS por um tempo; é difícil de desfazer, então se começa com valores baixos.
- **Por que o limite de taxa pode falhar com vários workers?** Porque o contador fica no cache; o cache local é por processo, então o limite real é multiplicado. Usa-se um cache compartilhado (Redis).
- **O que registrar em logs de segurança?** Eventos (login falho, acesso negado, limites), com quem, de onde e quando; nunca senhas ou tokens, e sanitizando o que vem do usuário.

## 📚 Para ir além
- 📄 Guia: [OWASP — Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html). Ciclo de vida e rotação (em inglês).
- 🧰 Ferramenta: [detect-secrets](https://github.com/Yelp/detect-secrets). Varredura e *baseline* (em inglês).
- 📄 Documentação: [GitHub — Push protection](https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection). Bloqueio de segredos no push (em inglês).
- 🧰 Ferramenta: [pip-audit](https://pypi.org/project/pip-audit/). Auditoria de dependências Python (em inglês).
- 📄 Documentação: [GitHub — Dependabot](https://docs.github.com/en/code-security/dependabot). Atualizações automáticas (em inglês).
- 📄 Referência: [OWASP Top 10:2025 — A03 Software Supply Chain Failures](https://owasp.org/Top10/2025/A03_2025-Software_Supply_Chain_Failures/) e [A09 Security Logging and Alerting Failures](https://owasp.org/Top10/2025/A09_2025-Security_Logging_and_Alerting_Failures/) (em inglês).
- 📄 Guia: [OWASP — HTTP Headers Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html). Cada cabeçalho e valor recomendado (em inglês).
- 📄 Referência: [MDN — CSP](https://developer.mozilla.org/pt-BR/docs/Web/HTTP/Guides/CSP), [HSTS](https://developer.mozilla.org/pt-BR/docs/Web/HTTP/Reference/Headers/Strict-Transport-Security) e [Permissions-Policy](https://developer.mozilla.org/pt-BR/docs/Web/HTTP/Reference/Headers/Permissions-Policy).
- 📄 Guia: [OWASP — Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html). O que registrar e o que evitar (em inglês).
- 📄 Documentação oficial: [DRF — Throttling](https://www.django-rest-framework.org/api-guide/throttling/) e [Django — Cache](https://docs.djangoproject.com/en/5.2/topics/cache/). `NUM_PROXIES` e o backend Redis.

## ✅ Checklist da aula
- [ ] Nenhum segredo no repositório; varredura triada e validada
- [ ] `pip-audit` limpo e validado contra um caso vulnerável
- [ ] Cabeçalhos de segurança ativos e testados por rota
- [ ] Rotas de demonstração, docs e admin sob controle em produção
- [ ] Eventos de segurança registrados, sem senhas e sem *log injection*
- [ ] Limite de taxa com cache compartilhado e IP real atrás do proxy
