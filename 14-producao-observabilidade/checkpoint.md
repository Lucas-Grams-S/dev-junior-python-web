# Checkpoint — Módulo 14: Produção e observabilidade básica

> ⏱️ ~1h30 · Faça **sem consultar** as aulas na primeira tentativa. 30 min para o quiz, 60 min para a entrega.

## 📝 Quiz (10 questões)
1. Por que **logs em JSON** e não texto? Descreva o `request_id`: quem o gera, como é validado (e por quê), como chega ao log do Django e como você o **provou** nos dois logs.
2. Que dados **nunca** devem ir para o log e quais duas travas o projeto tem? Por que o log de acesso não grava a query string?
3. Diferencie **liveness** e **readiness** (o que checa, o que o orquestrador faz se falha). O que acontece se o liveness consultar o banco? Por que a readiness devolve 503 **sem** o texto do erro e por que as sondas ficam em `SECURE_REDIRECT_EXEMPT`?
4. Log, erro (Sentry), métrica e trace: que pergunta cada um responde? Que erros **não** devem ir ao Sentry? O que o teste do DRF provou sobre o handler de erros?
5. Que privacidade o Sentry exige (`data_collection`, `before_send`)? O que mudou com `send_default_pii` no SDK 2.74? Por que `release` = tag da imagem, e o que "o Sentry envia trechos do seu código" significa para segredos?
6. Counter, gauge e histograma; o que é **cardinalidade** e por que o rótulo é o **padrão da rota**. O que o experimento com 2 workers mostrou (12/8 × 20) e como se corrige? Como o `/metrics/` é protegido (4 camadas)?
7. Cache-aside, TTL e **invalidação por versão**: como funciona a chave? Por que o catálogo só é cacheado para **anônimos**? Por que o estoque exige um `bump()` explícito e o que prova o teste "estoque velho"? Por que `on_commit`?
8. Cache fora do ar: o que continua, o que acusa a readiness e a liveness, e a diferença entre o limite de taxa **geral** (aberto) e o de **login** (fechado, 503). Que defeito o teste revelou no DRF?
9. Acho de consultas lentas: ordem do método e por que ordenar `pg_stat_statements` pelo tempo **total** (qual foi o maior custo agregado e por quê). Q1–Q5: quais ganharam com o índice `(is_active, name)`, quais não, e a alternativa para a busca e a página funda.
10. Backup: RPO, RTO, regra 3-2-1; como o `backup.sh` garante um arquivo íntegro; por que o teste de restauração usa uma **faixa** de contagens; o que cada um dos 3 cenários de corrupção provou; e o que mede o RTO.

<details><summary>Gabarito</summary>

1. JSON tem campos fixos que máquinas filtram, contam e correlacionam (mensagem estável + dados em campos). O **Nginx** gera `$request_id` e o repassa em `X-Request-ID`; o Django só aceita o ID recebido se casar `^[A-Za-z0-9._-]{8,64}$`, senão gera UUID (evita **injeção de log**, como `x\nFAKE {...}`); uma `ContextVar` + filtro de logging copia o ID para todo registro e o middleware o restaura ao fim (threads reutilizadas). Prova: `curl` guardou o `X-Request-ID` da resposta (`dd58c311...`) e a mesma sequência apareceu em `rid=` no log do Nginx e em `"request_id"` no JSON do Django. O ID enviado pelo cliente é substituído pelo do Nginx.
2. Senhas, tokens/JWT, `Authorization`, cookies, chaves, DSN e dados pessoais. Travas: log de acesso só com o **caminho** (nunca query string, onde o WebSocket leva o token) e o formatter **redige** chaves sensíveis (`[REDACTED]`) mesmo em `extra=`. Testes: query `token=SEGREDO` não aparece; `redigir`.
3. Liveness: só o processo (falha → reiniciar), não toca em nada externo (teste: 0 consultas). Readiness: banco e cache (falha → sai da rotação, sem reiniciar). Liveness com banco: o banco cai e **todos** os contêineres reiniciam em cascata. O 503 não vaza IP/usuário/URL porque o endpoint é público; o detalhe vai ao log (teste com `10.0.3.7`). Sondas HTTP simples: `SECURE_REDIRECT_EXEMPT = [r"^health/", r"^metrics/"]` (senão 301).
4. Log: o que houve nesta requisição; erro: exceções novas agrupadas, por release; métrica: agregado/tendência; trace: onde foi o tempo de uma requisição. Não ao Sentry: 4xx tratados (validação, 404, 403, 429). O teste mostrou que um `ZeroDivisionError` dentro de uma view do DRF responde `500 server_error` **e** chega ao Sentry (o handler devolve `None` para o que não é da API e o Django trata como 500).
5. `data_collection={"user_info": False, "http_bodies": [], "stack_frame_variables": False}` e um `before_send` (`scrub`) que filtra cabeçalhos, cookies, corpo e query, testado com um evento sintético. `send_default_pii` está **depreciada** no 2.74 (`DeprecationWarning`). O padrão do SDK já filtrava senhas, mas é promessa de uma versão: teste o resultado. `release` liga cada erro ao deploy (tag da imagem, `RELEASE` no `image.env`). O SDK anexa **linhas de código** ao redor de cada frame (achei o texto do meu próprio teste no evento): segredo escrito no código vai junto.
6. Counter só cresce; gauge sobe/desce; histograma distribui em baldes (p95/p99). Cardinalidade = nº de séries (combinações de rótulos); o caminho cru (`/products/49/`) cria uma série por ID, a rota (`products/(?P<pk>[^/.]+)/$`) uma só; `user_id` seria ~96 milhões de séries. Sem modo multiprocesso, cada worker conta separado e a raspagem alterna (12.0 8.0 12.0…); com `PROMETHEUS_MULTIPROC_DIR` dá 20.0 sempre. Proteção do `/metrics/`: token Bearer (comparação em tempo constante), 404 sem token configurado, Nginx devolve 404 de fora, raspagem interna.
7. Cache-aside: consulta, no miss busca e grava com TTL. Chave = `catalog:v<versão>:<sha256 de caminho + query ordenada + formato>`; `bump()` incrementa a versão e as chaves antigas somem (O(1)) até o TTL. Só anônimos porque a resposta é igual para todos; logado/equipe (vê inativos) passa direto (`BYPASS`) e não alimenta o cache. O estoque muda por `.update(F(...))`, que **não dispara signals**: sem `bump()` o catálogo mostra estoque velho (o teste "sem invalidar" prova). `on_commit` para só invalidar depois de gravado (senão outro processo recacheia o dado antigo).
8. O catálogo segue sem cache (33 ms MISS), a readiness dá 503 (cache `error`), a liveness 200 (não reiniciar), e volta sozinho. O throttle do DRF guarda contadores no cache e **levantava exceção → 500 em tudo**: o limite geral passou a falhar **aberto** (log); o de login falha **fechado** com 503 (`service_unavailable`) para não perder a proteção contra força bruta. Troca consciente, documentada.
9. Métrica por rota → log de lentas/`pg_stat_statements` → `EXPLAIN (ANALYZE, BUFFERS)` → corrigir → medir de novo. Ordena-se pelo tempo total (frequência × duração): o maior custo agregado foi o `COUNT(*)` (40 chamadas × 11 ms = 447 ms), maior que a página funda (5 × 84 ms = 421 ms). Q1 20,0 → 0,044 ms (450×); Q5 (keyset) 16,2 → 0,111 ms; Q2 (OFFSET 179980) 408 ms continua; Q3 (COUNT) 11,6 → 11,1 ms e Q4 (busca `%x%`) 39,9 → 40,9 ms não ganham. Busca: GIN de trigramas (`pg_trgm`, 0,258 ms, só PostgreSQL, não adotado); página funda: cursor/keyset.
10. RPO: dado que se aceita perder; RTO: tempo para voltar; 3-2-1: 3 cópias, 2 mídias, 1 fora. O `backup.sh` grava `.partial`, confirma com `pg_restore --list`, renomeia, gera `.sha256` e `.counts`, aplica retenção. A faixa [antes, depois] existe porque o banco continua escrevendo (comparar com o banco ao vivo deu falso alarme). Cenários: arquivo truncado e byte alterado → checksum reprova; checksum "consertado" → `pg_restore: could not uncompress data: incorrect data check`; o banco temporário é sempre apagado (0 sobras). O RTO medido foi ~2 s para 200 064 produtos (local); o seu será maior e deve ser registrado.
</details>

## 🛠️ Entrega prática
Repositório `minishop` na tag `v4.1-producao`:
- [ ] **Logs:** `config/logging_json.py` + `LOGGING`, `RequestContextMiddleware` (ID validado, log de acesso sem query), Nginx com `X-Request-ID`/`rid=`, e a prova de **um ID nos dois logs**
- [ ] **Health:** `/health/` e `/health/ready/` (503 sem vazamento), `SECURE_REDIRECT_EXEMPT`, sonda do Docker na readiness
- [ ] **Sentry:** `init_sentry` com `data_collection` e `scrub`, `RELEASE`/`ENVIRONMENT`, 4 testes com transporte falso (sem `DeprecationWarning`)
- [ ] **Métricas:** `config/metrics.py`, `/metrics/` protegido (token, 404, Nginx), teste dos rótulos sem ID, e o experimento de 2 workers colado
- [ ] **Cache:** `cache.py`/`signals.py`/`_com_cache`, `bump()` no pedido e no cancelamento, 13 testes, `config/throttling.py` (aberto/fechado) e a tabela MISS × HIT **sua**
- [ ] **Performance:** `pg_stat_statements` por tempo total, tabela Q1–Q5 sem/com índice, `product_active_name_idx` + migração, decisão sobre `pg_trgm`
- [ ] **Backup:** `backup.sh` e `restore_test.sh` rodados, 3 cenários de corrupção, **RTO medido**, `docs/producao.md` (RPO/RTO, restauração, agendamento, alerta de "sem backup em 26 h")
- [ ] Suíte (341), `ruff`, `mypy`, `lint-imports`, `makemigrations --check` e OpenAPI limpos; CI verde
- [ ] Tag: `git tag -a v4.1-producao -m "MiniShop: produção e observabilidade" && git push --follow-tags`

**Prova de fogo (40 min, sem consultar):** (1) alerta às 02:00: "taxa de 5xx > 5%"; liste a ordem em que você olha métricas, Sentry e logs (e como usa o `request_id`); (2) o Redis foi reiniciado e o hit rate caiu de 90% para 10% e não volta: três hipóteses e o que verificar em cada (pense em versão, TTL, `maxmemory` e chaves); (3) explique em 5 linhas por que um backup "verde" no agendador pode não servir no dia do desastre e o que você muda.

## 🪞 Autoavaliação
Nota de 0 a 3. Se algum item ficar em **0 ou 1**, refaça a aula antes de seguir.

| Habilidade | Aula | Nota |
|---|---|---|
| Logs JSON, request id, redação, liveness × readiness | 01 | |
| Sentry sem dados pessoais, release, métricas Prometheus e cardinalidade | 02 | |
| Cache-aside, TTL, invalidação por versão, estoque, falha aberta/fechada | 03 | |
| Consultas lentas, índices, OFFSET × cursor, backup e teste de restauração | 04 | |

## 🧠 Lógica: lista de verificação
Resolveu sem olhar: liveness com banco e 6 contêineres (14.01), cardinalidade de `user_id` (14.02), TTL, invalidação e latência média por hit rate (14.03), frequência × duração e o índice composto (14.04)? Marque o que faltou e refaça.

## 🧪 Estado de verificação deste módulo
**Executado:** **341 testes** em SQLite (338 + 4 pulados em PostgreSQL 18.6, com o mesmo aviso de teardown da aula 12.02), `ruff`, `mypy`, `lint-imports`, OpenAPI e migrações limpos; o **pacote de produção** local (readiness, logs JSON, `X-Request-ID` igual no Nginx e no Django, `/metrics/` 404 por fora e 200 por dentro, `RELEASE`, o Nginx recuperando-se da troca de IP do `web`); **Redis 8 e PostgreSQL 18.6 reais** (200 064 produtos): MISS × HIT, Redis parado com a aplicação no ar, `EXPLAIN (ANALYZE)` antes/depois de índices, `pg_stat_statements`, log de lentas, trigramas; `pg_dump`/`pg_restore` com 3 corrupções; `shellcheck`/`bash -n` em todos os scripts.

**Descobertas e correções (registradas nas aulas):** `send_default_pii` depreciada (SDK 2.74); o limite de taxa do DRF derrubava a API inteira quando o cache caía; o login devia falhar fechado (503); `.update()` do estoque não invalida via signal; teste de métricas flaky por buscar `999999` em texto livre; `PROMETHEUS_MULTIPROC_DIR` global quebrou o `migrate`; `environment` do anchor YAML é substituído (não mesclado); `/metrics/` e `/health/` precisavam de `SECURE_REDIRECT_EXEMPT`; **o Nginx do módulo 13 (corrigido na referência) continuava apontando para o IP antigo do `web` depois de um deploy (502/504) → `resolver` + variável**; o script de backup tinha caminho relativo, arquivos do root e um `docker run -i` que engolia o laço; e a comparação com o banco ao vivo dava falso alarme.

**Não executado:** **nenhuma conta Sentry** (interface, agrupamento, alertas), Prometheus/Grafana (PromQL é de documentação), integração Sentry–Celery, carga concorrente e *stampede*, cache `LocMem` com vários processos, RDS (log de lentas, Performance Insights, PITR, snapshots), WAL/`pg_basebackup`, envio do backup ao S3, `cron`/timers. Os tempos são desta máquina, em cache quente. Código em [`projeto/referencia-api-m14/`](../projeto/referencia-api-m14/README.md).

➡️ Próximo: [Módulo 15 — FastAPI (comparativo)](../15-fastapi-comparativo/README.md).
