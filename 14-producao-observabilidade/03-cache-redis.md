# 3. Cache com Redis: TTL e invalidação

> ⏱️ ~1h30 · Módulo 14 · Pré-requisitos: [14.02](02-sentry-metricas.md), [7.06 (Redis e Celery)](../07-sincrono-assincrono/06-filas-celery.md), [9.06 (limite de taxa e cache compartilhado)](../09-seguranca/06-segredos-dependencias-headers-rate-limit.md)

> ✅ **Verificação.** Executado em 2026-11-09 com **PostgreSQL 18.6 (200 mil produtos), Redis 8 e `uvicorn` de 1 processo**, todos locais, contêineres de nomes únicos: **13 testes** do cache (`tests/test_cache_catalogo.py`, entre eles os de invalidação por estoque, falha aberta e segurança), a suíte de **341 testes**, medições de latência (200 requisições sequenciais por caso) e um experimento **derrubando o Redis com a aplicação no ar**. **Não medido:** carga concorrente (a medição é sequencial), *stampede* (descrito, não reproduzido), Redis gerenciado (ElastiCache), e o cache de LocMem com vários processos (raciocínio, não experimento). Código em [`projeto/referencia-api-m14/`](../projeto/referencia-api-m14/README.md).

## 🎯 Objetivos
- Explicar **onde** e **o que** cachear, e o custo de cachear (dados velhos, complexidade)
- Implementar **cache-aside** com **TTL** e **invalidação por versão** no catálogo do MiniShop
- Reconhecer as invalidações que **não** disparam *signals* (`.update()` do estoque) e tratá-las
- Fazer o cache **falhar aberto** (o site continua sem ele) e decidir onde, ao contrário, falhar fechado
- **Medir** o ganho antes e depois e saber o que o número não diz

## 🤔 Por que isso importa
A página do catálogo é a mais acessada e a menos mutável: ideal para cache. Mas "há duas coisas difíceis em computação: invalidar cache e dar nomes às coisas". Cache mal feito mostra **estoque que não existe**, **preço velho**, ou dados de **outra pessoa**. E um Redis fora do ar pode derrubar toda a API se a aplicação depender dele sem querer (veremos que o limite de taxa do próprio projeto dependia). Em entrevista: "como você faz cache e como invalida?" separa quem já tomou prejuízo de quem não.

## 💡 Intuição (explicação simples)
O cache é a **prateleira de frente** da loja com os itens mais pedidos: o atendente pega ali (rápido) em vez de ir ao estoque no fundo (lento). Dois riscos: a prateleira pode ficar com **produto desatualizado** (alguém trocou o preço no fundo) e **ocupar espaço demais**. Estratégias: **validade** (cada item na prateleira tem etiqueta "descartar em 60 s" = TTL) e **troca de catálogo** (quando algo muda, o gerente imprime um catálogo novo com outro número de edição; as prateleiras de edições antigas simplesmente deixam de ser consultadas, sem ninguém sair apagando item por item = invalidação por versão).

## 🔬 Como funciona por dentro
**Onde cachear** (do mais perto do usuário ao mais fundo)
| Camada | Exemplo | Quem controla | Observação |
|---|---|---|---|
| Navegador / HTTP | `Cache-Control: max-age` | cabeçalhos da resposta | evita até a requisição |
| CDN / proxy (Nginx, CloudFront) | respostas públicas | cabeçalhos, regras | ótimo para estáticos e catálogo público; **não implementado** aqui |
| **Aplicação (Redis)** | **resposta da lista de produtos** | o código | **o desta aula** |
| Banco | `shared_buffers`, plano de execução | o SGBD | automático |
O curso fica na camada da aplicação, para ver o mecanismo; a de HTTP/CDN é a evolução natural.

**Padrões**
- **Cache-aside** (o que fazemos): a aplicação consulta o cache; se não tem (*miss*), busca na fonte, grava no cache e responde; se tem (*hit*), responde direto. A aplicação, não o cache, mantém a consistência.
- *Write-through/behind*: grava no cache junto/antes do banco (não usamos).
- **TTL (*time to live*)**: validade em segundos; é o **teto da desatualização tolerada** mesmo se a invalidação falhar. Use sempre, mesmo com invalidação.
- **Invalidação** (apagar/renovar o que mudou):
  | Estratégia | Como | Problema |
  |---|---|---|
  | só TTL | espera expirar | dado velho até 60 s |
  | apagar chaves | `cache.delete(...)` por chave | você precisa **conhecer todas** as chaves afetadas (lista paginada, filtros, busca…) |
  | **versão na chave** (o nosso) | incrementa um contador; chaves novas incluem a versão | chaves velhas ficam órfãs até o TTL (custo de memória, aceitável) |
  | tags | grupos de chaves | exige suporte do cache |

**Redis como cache.** Memória; **não precisa persistir** (`--save ""`); defina `maxmemory` e a política de **remoção** (`allkeys-lru`: ao encher, descarta as menos usadas) para ele nunca "estourar" (no Compose de produção: `redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru --save ""`). **Segurança:** o backend do Django serializa com `pickle`; quem escreve no seu Redis consegue executar código na aplicação. O Redis **nunca** fica exposto fora da rede privada (aula 11.04: sem porta publicada) e não é compartilhado com sistemas não confiáveis.

**O que NUNCA cachear sem cuidado.** Respostas **por usuário** sob uma chave comum (um cliente veria o carrinho de outro). Por isso o catálogo só é cacheado para **anônimos** (a resposta é idêntica para todos); logado (inclusive a equipe, que vê produtos inativos) **passa direto** (`X-Cache: BYPASS`).

**A parte difícil: o estoque.** O produto mostra `stock`/`in_stock`. Quem altera o estoque? O pedido e o cancelamento, com `Product.objects.filter(...).update(stock=F("stock") - n)`. Um `.update()` em lote **não dispara `post_save`**, então o *signal* que invalida o cache **não roda**: sem cuidado, o catálogo mostraria estoque velho por até 60 s. A solução: o repositório e o serviço chamam `bump()` explicitamente, com `transaction.on_commit`, porque invalidar **antes** do *commit* permite que outro processo recache o dado antigo no intervalo (o dado novo ainda não está visível para ele).

**Falhar aberto.** O cache é uma **otimização**, não uma dependência. Se o Redis cai: o catálogo continua (sem cache), a leitura/gravação do cache é protegida por `try/except` com log, e os *timeouts* curtos (`socket_connect_timeout`, `socket_timeout` = 1 s) impedem que uma conexão lenta trave tudo. **Mas** o Django REST Framework guarda os contadores do limite de taxa **no mesmo cache**; se o `cache.get` do throttle levanta exceção, cada requisição vira 500. Foi o que o teste revelou (abaixo). A decisão: limite geral **falha aberto**; limite de **login** **falha fechado** (503), porque sem contador não há como limitar tentativas de senha.

**Cache stampede (debandada).** Quando uma chave popular expira, muitas requisições simultâneas sofrem *miss* e recomputam a mesma coisa de uma vez, esmagando o banco. Mitigações (**não implementadas**): TTL com variação aleatória (*jitter*), um *lock* para só uma requisição recomputar, e servir o valor velho enquanto recalcula (*stale-while-revalidate*). Com TTL de 60 s e pouco tráfego não é problema; com milhares de requisições por segundo, é.

**Vários processos.** Com o cache padrão do Django (`LocMemCache`, memória **por processo**), cada worker tem o seu: a invalidação feita em um **não alcança** os outros, e o hit rate cai. Em produção, o cache é o **Redis compartilhado** (`REDIS_CACHE_URL`). (Raciocínio; não rodei o experimento com LocMem em 2 processos.)

## 🛠️ Exemplo prático
**1. O módulo do cache** (`apps/catalog/cache.py`):
```python
VERSION_KEY = "catalog:version"

def versao() -> int:
    v = cache.get(VERSION_KEY)
    if v is None:
        cache.add(VERSION_KEY, 1, None)            # `add` não sobrescreve: se outro processo criou antes, vale o dele
        v = cache.get(VERSION_KEY) or 1
    return int(v)

def bump() -> None:
    """Invalida o catálogo inteiro: as chaves da versão anterior ficam inalcançáveis (O(1)) e morrem pelo TTL."""
    try:
        cache.incr(VERSION_KEY)
    except ValueError:
        cache.add(VERSION_KEY, 2, None)

def chave(request, formato: str) -> str:
    bruto = f"{request.path}?{'&'.join(sorted(request.META.get('QUERY_STRING', '').split('&')))}|{formato}"
    return f"catalog:v{versao()}:{hashlib.sha256(bruto.encode()).hexdigest()[:32]}"
```
`obter()` e `gravar()` têm `try/except` e registram a métrica `minishop_cache_requests_total{result="hit|miss|error"}`. A chave inclui **caminho + parâmetros ordenados + formato** (`?a=1&b=2` e `?b=2&a=1` são a mesma consulta) e a versão.

**2. Usar no endpoint** (`apps/catalog/api.py`):
```python
def _com_cache(self, request, producao, *args, **kwargs):
    if request.method != "GET" or request.user.is_authenticated:
        resposta = producao(request, *args, **kwargs); resposta["X-Cache"] = "BYPASS"; return resposta
    k = cache.chave(request, request.accepted_renderer.format)
    guardado = cache.obter(k)
    if guardado is not None:
        resposta = Response(guardado); resposta["X-Cache"] = "HIT"; return resposta
    resposta = producao(request, *args, **kwargs)
    if resposta.status_code == 200:
        cache.gravar(k, json.loads(JSONRenderer().render(resposta.data)))      # dados simples (sem o serializer preso ao ReturnDict)
    resposta["X-Cache"] = "MISS"
    return resposta

def list(self, request, *args, **kwargs):      return self._com_cache(request, super().list, *args, **kwargs)
def retrieve(self, request, *args, **kwargs):  return self._com_cache(request, super().retrieve, *args, **kwargs)
```
O cabeçalho `X-Cache` é **observabilidade grátis** (e as métricas contam). Em `settings.py`: `CATALOG_CACHE_TTL = 60` (variável de ambiente) e o `RedisCache` com `socket_connect_timeout`/`socket_timeout` de 1 s.

**3. A invalidação**, em três lugares:
```python
# apps/catalog/signals.py — salvar/apagar Product ou Category
@receiver([post_save, post_delete], sender=Product)
@receiver([post_save, post_delete], sender=Category)
def invalidar_catalogo(sender, **kwargs):
    transaction.on_commit(cache.bump)             # só DEPOIS de gravado

# apps/orders/repositories.py — baixar o estoque (um .update(): sem signal)
def baixar_estoque(self, product_id, quantidade):
    transaction.on_commit(catalog_cache.bump)
    return Product.objects.filter(pk=product_id, stock__gte=quantidade).update(stock=F("stock") - quantidade) == 1

# apps/orders/services.py — cancelar o pedido devolve o estoque, também por .update()
transaction.on_commit(catalog_cache.bump)
```
O `apps/catalog/apps.py` importa os signals em `ready()`. A arquitetura permanece: `orders` (em cima) usa `catalog` (embaixo), e os contratos do `import-linter` seguem verdes (`3 kept, 0 broken`).

**4. Os testes** (`tests/test_cache_catalogo.py`, 13). Os essenciais:
```python
def test_anonimo_miss_depois_hit_sem_tocar_o_banco(api_as, django_assert_num_queries):
    anon = api_as(None)
    assert anon.get("/api/v1/products/")["X-Cache"] == "MISS"
    with django_assert_num_queries(0):                # a resposta veio do cache: ZERO consultas
        r = anon.get("/api/v1/products/")
    assert r["X-Cache"] == "HIT"

def test_pedido_e_cancelamento_invalidam_por_causa_do_estoque(api_as, django_capture_on_commit_callbacks, settings):
    ...
    with django_capture_on_commit_callbacks(execute=True):
        pedido = cli.post("/api/v1/orders/").json()
    r = anon.get(f"/api/v1/products/{p.pk}/")
    assert r["X-Cache"] == "MISS" and r.json()["stock"] == antes - 2

def test_sem_invalidar_o_estoque_fica_velho_ate_o_ttl(api_as):
    """A PROVA do porquê do bump: mudando o estoque 'por fora' do caminho invalidado, o cache mente."""
    Product.objects.filter(pk=p.pk).update(stock=antes + 100)        # sem signal, sem bump
    assert anon.get(f"/api/v1/products/{p.pk}/").json()["stock"] == antes     # velho, de propósito
```
O último teste **documenta o defeito** que o `bump()` corrige: é uma garantia de que o problema é real e não uma preocupação teórica. Os demais cobrem: o corpo do HIT igual ao do MISS, consultas diferentes com chaves diferentes, o detalhe, o **logado não usa nem alimenta o cache**, a **equipe vê inativos sem vazar para anônimos**, alterar o produto invalida, o TTL expira (esperando 1,2 s de relógio real), e os três cenários de falha do cache. Um detalhe de teste: `transaction.on_commit` só executa dentro de `django_capture_on_commit_callbacks(execute=True)`, porque cada teste roda numa transação que nunca é confirmada. E criar o pedido nesse teste acionou o Celery e tentou conectar ao broker (`ConnectionRefusedError`): o teste passou a usar `settings.ORDER_EMAIL_MODE = "off"`.

**5. Medindo o ganho** (PostgreSQL 18.6 com **200 064 produtos**, Redis 8, um `uvicorn`, 200 requisições sequenciais por linha, anônimas; o servidor sem cache usa `CATALOG_CACHE_TTL=0`). Tempo por requisição, mediana (p50) e p95:
| Consulta | Sem cache (MISS) p50 / p95 | Com cache (HIT) p50 / p95 | Ganho (p50) |
|---|---|---|---|
| lista, página 1 | 26,4 ms / 29,2 ms | 5,3 ms / 6,2 ms | ≈ 5× |
| lista, página 3000 (OFFSET fundo) | 60,4 ms / 64,5 ms | 5,6 ms / 6,9 ms | ≈ 11× |
| busca `?search=a1b2c3` (varre a tabela) | 76,9 ms / 102,9 ms | 5,3 ms / 6,3 ms | ≈ 14× |
**Como ler o número com honestidade.** (1) O *hit* custa ≈ 5 ms **e não zero**: é o piso do framework (middleware, autenticação, limite de taxa, serialização da resposta e a ida ao Redis); o cache só elimina a parte do banco. (2) O ganho cresce com o **custo da consulta** (busca > página funda > página 1); na página 1 o banco já é rápido (a aula 04 mostra por quê, com o índice). (3) É **sequencial, um cliente, uma máquina**: sob concorrência a vantagem é maior (o banco é o gargalo e o cache o poupa), mas **não medi**. (4) Em produção, o ganho depende da **taxa de acerto**: com 90% de acertos, 5,3 ms nos acertos e 26,4 ms nos erros dá média de 0,9 × 5,3 + 0,1 × 26,4 ≈ **7,4 ms**; com 50%, ≈ 15,9 ms. Por isso a métrica `minishop_cache_requests_total` importa. (5) Um achado paralelo: os requisitos de limite de taxa **continuam valendo para quem acerta o cache** (o `429` apareceu no meio das medições, e o limite do *usuário* de 1000/hora também contava anônimos).

**6. Derrubando o Redis com a aplicação no ar** (a prova da falha aberta; `uvicorn` local, Redis em contêiner que parei e religuei):
```text
--- com Redis ---
catálogo 200 em 0.0300s  X-Cache=MISS
{"status": "ok", "checks": {"database": {"status": "ok", "ms": 7.6}, "cache": {"status": "ok", "ms": 2.3}}}  <- ready 200
--- Redis PARADO ---
catálogo 200 em 0.0339s  X-Cache=MISS          ← o catálogo CONTINUA (sem cache)
catálogo 200 em 0.0333s  X-Cache=MISS
{"status": "error", "checks": {"database": {"status": "ok", "ms": 5.8}, "cache": {"status": "error"}}}  <- ready 503
{"status": "ok"}  <- live 200                  ← o processo está vivo: NÃO reiniciar
login (estrito) 500                            ← (antes da correção abaixo)
--- Redis de volta ---
catálogo 200 X-Cache=HIT
{"status": "ok", ...}  <- ready 200            ← voltou sozinho
```
O catálogo permaneceu no ar, a **readiness** acusou o problema (503) e a **liveness** não (200), exatamente o desenho da aula 01. **E apareceu um defeito que eu não tinha previsto:** o login deu **500**. O primeiro teste automatizado (com o cache "quebrado" em todo o processo) já tinha derrubado a **listagem** com um traceback no `throttle.allow_request`: os contadores do limite de taxa vivem no cache, e o DRF não trata a falha. Correções (`config/throttling.py`):
```python
class _FalhaAberta:
    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except Exception:
            logger.warning("throttle_cache_unavailable scope=%s", getattr(self, "scope", "?"), exc_info=True)
            return True                                # sem Redis: passa, e registra

class LoginThrottleFechado(ScopedRateThrottle):          # o limite de LOGIN falha FECHADO
    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except Exception as erro:
            raise ServicoIndisponivel() from erro        # 503 {"code": "service_unavailable"}
```
Os testes cobrem os três: catálogo continua sem cache; o limite geral falha aberto; o login responde `503` (verificado por teste; a execução ao vivo acima é anterior a esta correção e mostrou o 500). **A troca é consciente e deve estar documentada:** durante a queda do Redis, a proteção contra volume some (aberto), mas a proteção contra *força bruta de senha* se mantém (fechado, ao custo de o login ficar indisponível).

**7. Inspecionar o cache de verdade** (comandos do `redis-cli`, no Redis do teste):
```bash
docker exec lab14-redis redis-cli -n 1 keys '*'              # em produção use SCAN, nunca KEYS (bloqueia)
docker exec lab14-redis redis-cli -n 1 ttl ':1:catalog:v1:bd467aea3582086beaa6a559b77d3571'
docker exec lab14-redis redis-cli info stats | grep -E "keyspace_(hits|misses)"
docker exec lab14-redis redis-cli info memory | grep -E "used_memory_human|maxmemory"
```
```text
:1:catalog:version
:1:throttle_user_127.0.0.1
:1:catalog:v1:bd467aea3582086beaa6a559b77d3571
:1:throttle_anon_127.0.0.1
```
O prefixo `:1:` é o *key prefix*/versão do Django; vê-se a chave de versão, as chaves de resposta (`catalog:v1:...`) **e os contadores do limite de taxa no mesmo Redis**, o que explica a dependência. Em produção, separar os dois em **bancos/instâncias** diferentes é uma opção (o `REDIS_CACHE_URL` aponta para o banco 1).

## 🧠 Pausa para lógica
**Problema.** O catálogo tem TTL de 60 s. Uma promoção troca o preço de um produto às 10:00:00, e a invalidação por versão **funciona**. (a) Em que instante o preço novo aparece para todos os anônimos? (b) Imagine que a invalidação **falhou** (Redis caiu naquele instante): até quando um anônimo pode ver o preço velho? (c) Hit rate de 95%, *hit* de 5 ms e *miss* de 30 ms: qual a latência média? E se a cada 20 s alguém alterar um produto (invalidando tudo), o hit rate cai para 60%? (d) Por que invalidar o catálogo **inteiro** a cada mudança é aceitável aqui, mas não seria numa loja com mil alterações por minuto?

<details><summary>Dica</summary>Média ponderada; pense em quantas vezes a versão muda por minuto e no que cada mudança custa.</details>

<details><summary>Solução comentada</summary>

(a) Na **próxima** requisição após o *commit* (a versão mudou; a chave nova não existe; é um *miss*): ≈ 10:00:00. (b) Até **60 s** depois do último momento em que a resposta velha foi gravada: no pior caso 10:01:00. É o papel do TTL como teto. (c) 0,95 × 5 + 0,05 × 30 = **6,25 ms**; com 60%: 0,6 × 5 + 0,4 × 30 = **15 ms** (2,4× pior): invalidação frequente corrói o cache. (d) Com poucas alterações, a versão muda raramente e o cache vive quase todo o TTL; com mil alterações por minuto (≈ 16 por segundo), a versão muda sem parar, o hit rate tende a zero e o cache só custa memória e latência extra: o desenho precisaria de invalidação **granular** (por produto/categoria), ou de TTL curto sem invalidação para dados que mudam muito.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma / mensagem | Causa | Solução |
|---|---|---|
| Estoque/preço velho na loja | Mudança por `.update()`/SQL direto não dispara signal | `bump()` explícito (no commit) em todo caminho que muda o dado |
| Cache mostra dados de outra pessoa | Resposta por usuário sob chave comum | Só dados idênticos para todos; logado passa direto |
| Invalidou, mas ainda mostra o velho | Invalidou **antes** do commit e outro processo recacheou | `transaction.on_commit` |
| Toda a API 500 quando o Redis cai | Código/biblioteca dependendo do cache sem tratar falha (throttle do DRF) | Falha aberta onde for seguro; fechada (503) onde não |
| Requisições lentas quando o Redis está lento | Sem timeouts | `socket_connect_timeout`/`socket_timeout` curtos |
| Hit rate baixo | TTL curto demais, chave com parâmetros desordenados, invalidação demais | Normalizar a chave; medir `hit/miss`; rever o TTL |
| Memória do Redis cresce sem parar | Sem `maxmemory`/política, TTL ausente | `maxmemory` + `allkeys-lru`; sempre TTL |
| `KEYS *` travou o Redis em produção | Operação O(N) bloqueante | `SCAN`; não use `KEYS` |
| Cache "funciona" em dev e não em produção | `LocMemCache` por processo | Redis compartilhado |
| Debandada ao expirar uma chave popular | Muitos *misses* simultâneos | *Jitter*, lock, *stale-while-revalidate* |
| Execução arbitrária via cache | `pickle` + Redis exposto/compartilhado | Redis privado, sem porta publicada |
| Teste de invalidação nunca invalida | `on_commit` não roda em transação de teste | `django_capture_on_commit_callbacks(execute=True)` |
- **Cache é otimização, nunca fonte da verdade**: o sistema deve estar correto sem ele.
- **Meça antes e depois** (e o hit rate em produção).
- **TTL sempre**, mesmo com invalidação.
- **Documente o que cacheia e quem invalida** (`docs/producao.md`).

## 🧩 Exercícios
**1. Fixação.** (a) Cache-aside em três passos. (b) TTL × invalidação. (c) Por que `.update()` exige tratamento especial? (d) Por que `on_commit`? (e) Falha aberta × fechada: um exemplo de cada.

<details><summary>Solução</summary>

(a) Consulta o cache; no *miss* busca na fonte e grava; responde. (b) O TTL limita o pior caso; a invalidação reduz a desatualização típica. (c) Não dispara `post_save`, então o signal de invalidação não roda. (d) Para só invalidar depois que o dado novo está visível. (e) Aberta: catálogo sem cache e limite geral de taxa; fechada: limite de login (503).
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] `apps/catalog/cache.py` (versão, `bump`, chave normalizada, `obter`/`gravar` tolerantes a falha) e `signals.py` (com `on_commit`)
- [ ] `_com_cache` em `list`/`retrieve` (só anônimo, `X-Cache`), `CATALOG_CACHE_TTL`, `RedisCache` com timeouts
- [ ] `bump()` no `baixar_estoque` e no `cancel_order`; `import-linter` verde
- [ ] Os **13 testes** (HIT/MISS sem consultas, corpo igual, chaves distintas, detalhe, logado bypass, equipe sem vazamento, alterar produto, pedido/cancelamento, **estoque velho sem bump**, TTL, cache fora, throttle aberto, login fechado)
- [ ] `config/throttling.py` (aberto e fechado) e a troca documentada em `docs/producao.md`
- [ ] A **tabela de medição** feita por você (p50/p95, MISS × HIT, 3 consultas), com as premissas, e o experimento de **parar o Redis** com o que cada endpoint respondeu
- [ ] `redis-server --maxmemory ... --maxmemory-policy allkeys-lru --save ""` no Compose de produção (já em `deploy/compose.prod.yaml`)
- [ ] Commit `feat(catalog): redis cache with versioned invalidation and fail-open`

**3. Desafio (opcional).** Reproduza o *stampede*: 200 requisições simultâneas logo após um `bump()`, contando quantas consultas SQL a página gera (`CaptureQueriesContext` ou `pg_stat_statements`). Depois implemente um *lock* (`cache.add` com timeout curto como mutex) para que só uma requisição recompute, e compare.

## 🎤 Na entrevista
**1. Como você implementa cache e como o invalida?** Cache-aside no Redis: consulta, no miss busca e grava com TTL. Invalidação por versão na chave (incrementar um contador torna as chaves antigas inalcançáveis), disparada após o commit pelos pontos que alteram o dado, inclusive os que usam `update()` em lote e não geram signals; o TTL é o teto de segurança.

**2. O que acontece com sua aplicação se o Redis cair?** O cache é só otimização, então as leituras seguem sem ele, com timeouts curtos e falhas registradas; a readiness acusa o problema (503) e a liveness não. O limite de taxa geral falha aberto; o de login falha fechado, para não perder a proteção contra força bruta.

**3. Quais os riscos do cache?** Dados velhos (inconsistência), vazamento entre usuários se a chave não separar o contexto, debandada quando chaves populares expiram, uso de memória sem limite, e acoplamento (a aplicação passa a depender dele). Mitigam-se com TTL, chaves/escopo corretos, `maxmemory` com política de remoção, jitter/locks e falha aberta.

## 📚 Para ir além
- 📄 Documentação oficial: [Django — Framework de cache](https://docs.djangoproject.com/en/5.2/topics/cache/). `get/set/add/incr`, backends, `KEY_PREFIX`, `VERSION`.
- 📄 Documentação oficial: [Redis — políticas de remoção](https://redis.io/docs/latest/develop/reference/eviction/). `maxmemory`, `allkeys-lru`.
- 📄 Documentação oficial: [ElastiCache — estratégias de cache](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Strategies.html). Lazy loading, write-through, TTL e adição de jitter (em inglês).
- 📄 Documentação oficial: [MDN — HTTP caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching). `Cache-Control`, validação e a camada de navegador/CDN (em inglês).
- 📄 Documentação oficial: [DRF — Throttling](https://www.django-rest-framework.org/api-guide/throttling/). Onde ficam os contadores e como personalizar.
- 📄 Documentação oficial: [Django — otimização de acesso ao banco](https://docs.djangoproject.com/en/5.2/topics/db/optimization/). O que fazer **antes** de cachear.
- 🏋️ Prática extra: ligue `CATALOG_CACHE_TTL=5`, faça 100 requisições por 30 s e conte, pelas métricas, quantos *misses* ocorrem; compare com a previsão (30/5 = 6 expirações).

## ✅ Checklist da aula
- [ ] Sei os padrões (cache-aside), TTL e as estratégias de invalidação
- [ ] O catálogo anônimo usa cache com chave normalizada e versão; logado passa direto
- [ ] Todo caminho que muda o dado (inclusive o estoque por `.update()`) invalida **no commit**
- [ ] O cache falha aberto; o login falha fechado (503); medi com o Redis parado
- [ ] Tenho a tabela de latência antes/depois e sei o que ela não diz
- [ ] Sei o risco do `pickle`, do `KEYS`, da falta de `maxmemory` e do *stampede*
