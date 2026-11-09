# 2. Monitoramento de erros (Sentry) e métricas

> ⏱️ ~1h30 · Módulo 14 · Pré-requisitos: [14.01](01-logs-estruturados-health.md), [9.06 (segredos, cabeçalhos, limite de taxa)](../09-seguranca/06-segredos-dependencias-headers-rate-limit.md), [12.02 (imagem identificada por tag)](../12-ci-cd/02-pipeline-completo.md)

> ✅ **Verificação.** Executado em 2026-11-09 (sentry-sdk 2.74.0, prometheus-client, `uvicorn` com 2 workers, Docker 29.9.2): **4 testes do Sentry** (com um *transporte falso*: o evento é capturado em memória, **nada vai à rede**) e os testes de métricas; a suíte de **341 testes**; o experimento de **métricas com vários processos**; e o pacote de produção local (`/metrics/` oculto no Nginx, raspagem interna, `RELEASE` no ambiente). **Não executado:** **nenhuma conta Sentry** (não vi a interface, o agrupamento de erros nem as regras de alerta), nenhum **servidor Prometheus/Grafana** (as consultas PromQL são de documentação), e a integração do Sentry com o Celery. Código em [`projeto/referencia-api-m14/`](../projeto/referencia-api-m14/README.md).

## 🎯 Objetivos
- Explicar o que um serviço de **monitoramento de erros** faz que o log sozinho não faz, e ligar o **Sentry** ao MiniShop sem enviar dados sensíveis
- Associar cada erro a um **release** (a tag da imagem) e a um **ambiente**
- Distinguir **log, métrica e erro** (e **trace**) e escolher qual usar para cada pergunta
- Expor **métricas Prometheus** (contagem, latência em histograma) com **rótulos de baixa cardinalidade**
- Evitar a armadilha das **métricas com vários processos** e proteger o `/metrics/`

## 🤔 Por que isso importa
O log diz *o que aconteceu naquela requisição* se você já sabe onde olhar. O **Sentry** avisa que *um erro novo apareceu*, agrupa mil ocorrências iguais em um só problema, mostra em qual versão começou e quem foi afetado. As **métricas** respondem "está piorando?": taxa de erros, latência, saturação, ao longo do tempo, sem varrer milhões de linhas. Time de produção vive disso; é pergunta certa de entrevista ("como você soube que o deploy quebrou algo?").

## 💡 Intuição (explicação simples)
Um hospital. O **log** é o **prontuário detalhado** de cada paciente (preciso, mas você precisa saber qual abrir). O **Sentry** é o **alarme da enfermaria**: toca quando entra uma doença nova, agrupa os casos iguais e diz "começou depois da troca de turno" (o release). As **métricas** são os **monitores de sinais vitais** do andar inteiro: batimentos por minuto, temperatura média, quantos leitos ocupados, mostrados num gráfico. Cada um responde a uma pergunta que os outros respondem mal.

## 🔬 Como funciona por dentro
| Sinal | Pergunta que responde | Exemplo no MiniShop | Custo |
|---|---|---|---|
| **Log** | O que aconteceu *nesta* requisição? | linha JSON com `request_id` | alto volume, busca por texto/campo |
| **Erro (Sentry)** | Que exceções novas estão acontecendo, quantas, desde quando, quem afetou? | `ZeroDivisionError` em `ProductViewSet.list` desde o release `sha-9f3c1` | baixo volume, agrupado |
| **Métrica** | O sistema está saudável *agora* e em tendência? | 99º percentil da latência de `/api/v1/products/`, taxa de 5xx | baixo, agregado |
| **Trace** | Onde foi o tempo *de uma* requisição lenta (banco? cache? API externa?) | span do `SELECT` | amostrado |

**Sentry, em poucas linhas.** O SDK se pendura na aplicação (Django, DRF, Celery…), captura **exceções não tratadas** (e o que você mandar), junta contexto (versão, ambiente, *breadcrumbs* — pequenos eventos anteriores —, o código ao redor de cada frame) e envia ao servidor (o serviço hospedado ou um self-hosted). O servidor **agrupa** por *stack trace* semelhante, mantém o histórico por release e dispara **alertas** por regra. Pontos de atenção:
- **O que NÃO é erro:** respostas 4xx tratadas (validação, 404, 403, 429) são o comportamento normal da API; só **o inesperado (500)** deve chegar ao Sentry. O handler de erros do projeto devolve JSON para erros da API, mas **não engole** o inesperado: o DRF devolve `None` para exceções que não são suas (um `ZeroDivisionError`) e o Django as trata como 500, com o sinal que o Sentry escuta. **Isto foi testado**, não suposto (veja abaixo).
- **Privacidade (LGPD, módulo 9).** Por padrão, um SDK pode anexar cabeçalhos, cookies, corpo da requisição, IP e usuário. Regra do curso: **não enviar nada disso**; no máximo o **ID** interno do usuário. Em duas camadas: a configuração do SDK e um `before_send` que limpa o evento antes de sair.
- **O Sentry envia trechos do seu código-fonte** (algumas linhas ao redor de cada frame da pilha). Se houver um segredo escrito no código, ele sai junto: mais um motivo para segredos nunca estarem no código (módulo 9), e há uma opção para limitar as linhas de contexto.
- **Release e ambiente.** `release` = a tag da imagem (`sha-9f3c1`, aula 12.02/13.07): o Sentry mostra "este erro apareceu no release X" e "foi resolvido no Y"; `environment` separa produção de homologação. Sem release, você não sabe qual deploy quebrou.
- **Amostragem de desempenho** (`traces_sample_rate`): 0 desliga; 0,01 = 1% das requisições viram *traces* (caro). Comece em 0.
- **Cota e custo.** Planos têm limites de eventos; um erro em laço pode gastar a cota inteira em minutos. Use alertas e filtros (ignore ruído conhecido). (Confira planos na página do serviço; não verifiquei preços.)

**Métricas (modelo Prometheus).** O servidor **raspa** (`scrape`) um endpoint de texto `/metrics` a cada N segundos e guarda séries temporais. Tipos:
- **Counter**: só cresce (requisições, erros). Útil via taxa: `rate(...[5m])`.
- **Gauge**: sobe e desce (requisições em andamento, tamanho da fila).
- **Histogram**: distribui valores em **baldes** (`le="0.05"` = "≤ 50 ms"); permite calcular **percentis** (`histogram_quantile`) no servidor. Média esconde cauda: o p99 é o que o usuário azarado sente.
- **Rótulos (*labels*)** criam séries: `route="..."`, `status="200"`. **Cardinalidade** = número de combinações. Rótulo com ID de usuário, e-mail ou caminho cru (`/products/49/`, `/products/50/`...) cria **milhões de séries** e derruba o Prometheus. Regra: rótulos de **poucos valores conhecidos** (método, **padrão** da rota, classe de status), **nunca** valores ilimitados nem pessoais.
- **Os 4 sinais de ouro** (Google SRE) / **RED** para serviços: **R**ate (requisições/s), **E**rrors (taxa de 5xx), **D**uration (latência). Mais **saturação** (CPU, memória, fila, conexões).
- **Várias instâncias/processos.** Com 2+ workers (uvicorn/gunicorn), cada **processo** tem seus próprios contadores em memória; a raspagem cai num deles ao acaso. A solução do `prometheus_client` é o **modo multiprocesso**: cada processo grava em arquivos de uma pasta e a raspagem **agrega** (experimento abaixo).
- **Segurança do `/metrics/`.** Métricas revelam rotas, volume e erros: informação útil a um atacante. Aqui: exige `Authorization: Bearer <METRICS_TOKEN>`, **não existe** (404) se o token não estiver configurado, o Nginx a oculta do mundo (`return 404`), e o raspador acessa direto `web:8000` pela rede interna.

## 🛠️ Exemplo prático
**1. Ligar o Sentry** (`config/observability.py`, chamado no fim do `settings.py`; só liga se existir `SENTRY_DSN`):
```python
def scrub(event, hint):
    """`before_send`: última barreira antes de o evento sair."""
    req = event.get("request")
    if req:
        req["headers"] = _limpar(req.get("headers") or {})       # Authorization, Cookie, X-Api-Key → [Filtered]
        req.pop("cookies", None)
        req.pop("data", None)                                    # corpo da requisição: fora
        if req.get("query_string"):
            req["query_string"] = "[Filtered]"
    if "extra" in event:
        event["extra"] = _limpar(event["extra"])
    return event

def init_sentry(transport=None) -> bool:
    dsn = os.environ.get("SENTRY_DSN", "")
    if not dsn:
        return False
    import sentry_sdk
    sentry_sdk.init(
        dsn=dsn,
        environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
        release=os.environ.get("RELEASE") or None,               # tag da imagem: o erro fica ligado ao deploy
        data_collection={"user_info": False, "http_bodies": [], "stack_frame_variables": False},   # sem usuário/IP, sem corpos, sem valores de variáveis
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0")),
        before_send=scrub,
        transport=transport,                                     # só nos testes
    )
    return True
```
**Duas descobertas da execução.** (1) A minha primeira versão usava `send_default_pii=False`, o que todos os tutoriais mostram; na versão **2.74** do SDK isso gera `DeprecationWarning: The send_default_pii option is deprecated. Use data_collection instead`: o controle fino passou a ser o `data_collection`, que os testes agora exigem sem aviso (`-W error::DeprecationWarning`). **Tutorial antigo, API nova**: leia o aviso e a documentação da versão que você instalou. (2) Testando os dois cenários (`send_default_pii=False` e `data_collection`), o SDK **já filtra** senhas e cookies sozinho (`{"password": "[Filtered]"}`); mesmo assim mantemos o `before_send` e o **testamos diretamente com um evento sintético**, porque o padrão de uma biblioteca é uma promessa de **uma versão**, e a segurança não deve depender dela.

**2. Testar sem rede** (`tests/test_sentry.py`): um *transporte falso* guarda os eventos em memória.
```python
class TransporteFalso(Transport):
    def __init__(self, options=None):
        super().__init__(options); self.eventos = []
    def capture_envelope(self, envelope):
        for item in envelope.items:
            if item.headers.get("type") == "event":
                self.eventos.append(item.payload.json)

def test_excecao_nao_tratada_chega_ao_sentry_com_release_e_sem_segredos(sentry, monkeypatch, settings):
    monkeypatch.setattr("config.metrics.generate_latest", explode)          # uma falha real, numa view real
    settings.METRICS_TOKEN = "t"
    r = Client(raise_request_exception=False).get("/metrics/?token=SEGREDO",
        headers={"Authorization": "Bearer t", "Cookie": "sessionid=abc", "X-Api-Key": "chave-xyz"})
    assert r.status_code == 500
    (ev,) = sentry.eventos
    assert ev["release"] == "sha-abc1234" and ev["exception"]["values"][0]["type"] == "RuntimeError"
    for segredo in ("SEGREDO", "sessionid=abc", "chave-xyz"):
        assert segredo not in str(ev)
```
```text
tests/test_sentry.py ....        4 passed      (sem DSN não liga · scrub remove segredos · exceção chega com release · erro dentro de view do DRF também chega)
```
O quarto teste responde à dúvida do "o handler de erros engole o 500?": uma exceção dentro de `ProductViewSet.get_queryset` produz `500 {"code":"server_error"}` para o cliente **e** um evento `ZeroDivisionError` no Sentry. **Um cuidado ao investigar:** numa checagem informal procurei a palavra `SEGREDO` no evento e a achei; vinha de `exception.values[0].stacktrace.frames[3].post_context[2]`, ou seja, **a linha do meu próprio teste** (o SDK anexa as linhas de código ao redor de cada frame da pilha). Foi falso alarme, mas o aviso é real: **código-fonte vai junto com o erro**.

**3. Releases em produção.** O Compose de produção passa `RELEASE=${RELEASE:-dev}` e o `update.sh` grava a tag da imagem em `image.env` (`RELEASE=sha-...`), que alimenta o contêiner. Conferência feita no pacote local: `printenv RELEASE` → `sha-lab14`. Detalhe de YAML que quase me enganou: no `compose.prod.yaml`, `<<: *app` copia o bloco `environment` do *anchor* de forma **rasa**; ao declarar um `environment:` próprio no `web` (para o `PROMETHEUS_MULTIPROC_DIR`), a chave do anchor é **substituída**, não mesclada: tive de repetir `RELEASE` lá (conferido com `docker compose config`). No Sentry real, o `SENTRY_DSN` é um **segredo de configuração**: vai ao Parameter Store como `SecureString` (aula 13.08), nunca ao Git.

**4. As métricas** (`config/metrics.py`):
```python
REQUISICOES = Counter("minishop_http_requests_total", "Requisições HTTP", ["method", "route", "status"])
LATENCIA = Histogram("minishop_http_request_duration_seconds", "Latência das requisições HTTP", ["method", "route"],
                     buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10))
EM_ANDAMENTO = Gauge("minishop_http_requests_in_flight", "Requisições em andamento", multiprocess_mode="livesum")
CACHE = Counter("minishop_cache_requests_total", "Consultas ao cache do catálogo", ["result"])   # hit | miss | error

def rota(request) -> str:
    """O PADRÃO da URL, não `/api/v1/products/49/`: senão cada ID vira uma série nova."""
    match = getattr(request, "resolver_match", None)
    return match.route if match and match.route else "nao-resolvida"
```
O middleware da aula 01 chama `requisicao_iniciada()` e `observar_requisicao(...)`. O que o endpoint devolve (amostra real, depois de duas listas, um 404 de produto e uma sonda):
```text
minishop_http_requests_total{method="GET",route="api/<str:version>/products/$",status="200"} 2.0
minishop_http_requests_total{method="GET",route="api/<str:version>/products/(?P<pk>[^/.]+)/$",status="404"} 1.0
minishop_http_requests_total{method="GET",route="health/",status="200"} 1.0
minishop_http_request_duration_seconds_bucket{le="0.05",method="GET",route="api/<str:version>/products/$"} 1.0
minishop_http_request_duration_seconds_count{method="GET",route="api/<str:version>/products/$"} 2.0
minishop_cache_requests_total{result="miss"} 2.0
```
Note o `route`: o **padrão** (`products/(?P<pk>[^/.]+)/$`, o formato do roteador do DRF), e o `999999` do produto inexistente **não** aparece em lugar nenhum. O teste que protege a cardinalidade:
```python
rotas = {linha.split('route="')[1].split('"')[0] for linha in corpo.splitlines() if 'route="' in linha}
assert any("products/(?P<pk>" in rota for rota in rotas)       # o padrão vira rótulo…
assert not any("999999" in rota for rota in rotas)              # …e o ID cru, nunca
```
(A primeira versão deste teste procurava `999999` no texto inteiro e **falhava de vez em quando** na suíte completa e passava isolada. A causa provável: cada contador tem um campo `_created` com o *timestamp* de criação em notação científica, cujos dígitos podem conter `999999` por coincidência; **não confirmei linha a linha**, mas a correção, olhar só os rótulos `route=`, eliminou a falha em 3 execuções seguidas. Lição: um teste que procura um número arbitrário em texto livre é frágil.)

**5. A armadilha dos vários processos, medida.** Dois workers do `uvicorn`, 20 requisições a `/health/`, depois 6 leituras seguidas do contador:
```text
SEM modo multiprocesso:    12.0  8.0  12.0  12.0  12.0  8.0        ← cada leitura cai num worker ao acaso (12 + 8 = 20)
COM PROMETHEUS_MULTIPROC_DIR:  20.0  20.0  20.0  20.0  20.0  20.0   ← agregado dos arquivos dos dois processos
```
Um gráfico feito com a primeira configuração **pula** entre 8 e 12 e mente sobre a taxa. A correção: a variável `PROMETHEUS_MULTIPROC_DIR` apontando para uma pasta (no Compose de produção, um `tmpfs` em `/prom`, apagado a cada início) **antes** de importar a biblioteca, e o `/metrics/` agregando com `MultiProcessCollector`. Um bug que isso me mostrou: pôr a variável no bloco comum (`x-app`) fez o serviço `migrate` quebrar (`FileNotFoundError: '/prom/gauge_livesum_1.db'`), porque ele não tem a pasta. Correções: a variável só no serviço `web`, **e** o módulo cria a pasta ou, se não puder, segue sem o modo multiprocesso com um aviso (em vez de falhar na importação).

**6. Proteger o `/metrics/`.**
```python
def metricas(request):
    token = getattr(settings, "METRICS_TOKEN", "")
    if not token:
        raise Http404                                            # sem token configurado, o endpoint NÃO EXISTE
    enviado = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not hmac.compare_digest(enviado.encode(), token.encode()):   # comparação em tempo constante
        return HttpResponseForbidden("forbidden")
```
No pacote de produção, medi: `nginx /metrics/ -> 404` (o Nginx a oculta) e, **de dentro** da rede, uma requisição ao `web:8000/metrics/` com o token devolveu `200` (15 linhas `minishop_`). Um tropeço útil: com `SECURE_SSL_REDIRECT=1`, o raspador (HTTP simples, direto no `web`) recebia **301**; por isso `/metrics/` entrou no `SECURE_REDIRECT_EXEMPT` junto com `/health/`.

**7. Consultas PromQL (documentação; não executei um Prometheus).** O que você escreveria no dia em que tivesse um:
```text
sum(rate(minishop_http_requests_total[5m]))                                          # requisições por segundo
sum(rate(minishop_http_requests_total{status=~"5.."}[5m])) / sum(rate(minishop_http_requests_total[5m]))   # taxa de erro
histogram_quantile(0.99, sum by (le, route) (rate(minishop_http_request_duration_seconds_bucket[5m])))     # p99 por rota
sum(rate(minishop_cache_requests_total{result="hit"}[5m])) / sum(rate(minishop_cache_requests_total{result=~"hit|miss"}[5m]))   # taxa de acerto do cache
```
E um alerta clássico: "taxa de erro > 2% por 5 minutos" avisa; um erro isolado, não.

## 🧠 Pausa para lógica
**Problema.** Um colega propõe acrescentar o rótulo `user_id` ao contador de requisições "para saber quem usa mais a API". A loja tem 80 mil usuários ativos, 40 rotas, 5 métodos e 6 classes de status que realmente ocorrem. (a) Quantas séries no máximo (rotas × métodos × status) existem **sem** `user_id`? (b) E **com**? (c) Cada série custa ~3 KB de memória no servidor de métricas: quanto isso significa? (d) Como responder à pergunta "quem usa mais" sem esse rótulo?

<details><summary>Dica</summary>Multiplique as dimensões. Pense em onde dados por usuário pertencem.</details>

<details><summary>Solução comentada</summary>

(a) 40 × 5 × 6 = **1 200** séries (na prática bem menos, pois nem toda combinação ocorre). (b) 1 200 × 80 000 = **96 milhões** de séries potenciais. (c) 96 000 000 × 3 KB ≈ **288 GB**: o servidor de métricas cai (e cada novo usuário cria séries novas que nunca acabam). (d) Métrica é para **agregados**; "por usuário" é pergunta de **log/análise**: a linha de acesso já tem `user_id` (aula 01), então uma consulta no CloudWatch Logs Insights/`jq` (`stats count(*) by user_id`) responde, ou um banco analítico para uso de produto. Regra: o que tem cardinalidade ilimitada vai para log ou evento, não para rótulo de métrica.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma / mensagem | Causa | Solução |
|---|---|---|
| `DeprecationWarning: The send_default_pii option is deprecated` | Tutorial para SDK antigo | `data_collection` (SDK 2.7x); leia as notas da versão |
| Erros do Sentry sem versão | `release` ausente | `RELEASE` = tag da imagem |
| Segredo ou dado pessoal no evento | Cabeçalhos/corpo/query anexados | `data_collection` restritivo + `before_send` **testado** |
| Cota do Sentry estourou em minutos | Erro em laço / 4xx tratados enviados | Só 500; `ignore_errors`; limite por regra |
| Código-fonte com segredo enviado ao Sentry | Segredo escrito no código | Segredos fora do código; limitar linhas de contexto |
| Gráfico de contador "pulando" | Vários processos sem modo multiprocesso | `PROMETHEUS_MULTIPROC_DIR` (e pasta limpa a cada início) |
| `FileNotFoundError: /prom/gauge_...db` | Variável definida onde a pasta não existe (migrate/celery) | Só no `web`; o módulo trata a ausência |
| Prometheus lento/cai com milhões de séries | Rótulo de alta cardinalidade | Rótulos limitados; o padrão da rota, não o caminho |
| `/metrics/` público | Sem proteção | Token + 404 sem token + Nginx escondendo + raspagem interna |
| `/metrics/` devolve `301` ao raspar | `SECURE_SSL_REDIRECT` sem isenção | `SECURE_REDIRECT_EXEMPT` |
| Média "boa", usuários reclamando | Só a média | Histograma e p95/p99 |
| Alerta que toca toda hora | Limite sem janela, ou sobre contagem absoluta | Taxa/percentual por janela (5 min) |
- **Alerta acionável ou nenhum alerta.** Cada alerta precisa de dono e de uma ação clara (runbook em `docs/producao.md`).
- **Meça o que importa ao usuário** (latência e erro), não só CPU.
- **Teste a observabilidade** como teste qualquer código: ela é a que você vai usar quando tudo estiver quebrado.
- **Cuide dos dados:** retenção, acesso e LGPD também valem para o Sentry e para os logs.

## 🧩 Exercícios
**1. Fixação.** (a) Log × erro × métrica × trace. (b) Por que `release` importa? (c) O que é cardinalidade e por que o rótulo é a **rota** e não o caminho? (d) Por que a média engana e o que usar? (e) Por que o `/metrics/` não é público?

<details><summary>Solução</summary>

(a) Log: detalhe de um evento; erro: exceção nova agrupada; métrica: agregado no tempo; trace: onde foi o tempo de uma requisição. (b) Liga o erro ao deploy que o causou e mostra quando foi resolvido. (c) Número de séries distintas; o caminho cru cria uma série por ID. (d) Esconde a cauda; histograma e percentis (p95/p99). (e) Revela rotas, volumes e erros a quem quiser atacar.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] `config/observability.py` (`init_sentry`, `scrub`) chamado no `settings.py`; `data_collection` (sem `send_default_pii`); `RELEASE`/`SENTRY_ENVIRONMENT`; teste sem `DeprecationWarning`
- [ ] Os **4 testes** do Sentry (sem DSN, scrub direto, exceção real com release, erro dentro do DRF) com o transporte falso
- [ ] `config/metrics.py` (contador, histograma, gauge, métrica de cache), `/metrics/` com token (404 sem token, 403 com token errado) e o teste dos **rótulos sem ID**
- [ ] O experimento dos **2 workers** (sem e com `PROMETHEUS_MULTIPROC_DIR`) com as 6 leituras coladas em `docs/producao.md`
- [ ] Nginx escondendo `/metrics/` (404 de fora) e uma raspagem interna com token (`200`)
- [ ] `SENTRY_DSN` e `METRICS_TOKEN` no Parameter Store (nomes em `docs/aws.md`, **sem valores**)
- [ ] Três consultas PromQL escritas por você em `docs/producao.md` (taxa, erro, p99) e dois alertas propostos com a ação de cada um
- [ ] Commit `feat(observability): sentry with scrubbing and prometheus metrics`

**3. Desafio (opcional).** Suba um Prometheus (`prom/prometheus`) e um Grafana em contêineres de nome único, raspe o `web:8000/metrics/` com o token (`authorization` no `scrape_config`) e monte um painel com RED (taxa, erros, p95). Registre se o gráfico do contador fica estável com 2 workers.

## 🎤 Na entrevista
**1. Qual a diferença entre logs, métricas e traces?** Logs são eventos detalhados; métricas são séries numéricas agregadas no tempo, baratas e boas para alertar sobre tendências; traces mostram o caminho e o tempo de uma requisição entre componentes. Usam-se juntos: a métrica avisa, o trace localiza, o log explica.

**2. Para que serve o Sentry e que cuidados você tem?** Captura e agrupa exceções com contexto, versão e frequência, e alerta sobre erros novos. Cuidados: só enviar o inesperado (500), ligar cada erro ao release, não enviar dados pessoais nem segredos (configuração restritiva e `before_send` testado) e controlar a cota.

**3. O que é cardinalidade em métricas e por que importa?** É o número de combinações de valores de rótulos; cada uma é uma série que custa memória e consulta. Rótulos com valores ilimitados (IDs, e-mails, caminhos crus) derrubam o servidor de métricas, então usam-se rótulos de poucos valores, como o padrão da rota.

## 📚 Para ir além
- 📄 Documentação oficial: [Sentry para Django](https://docs.sentry.io/platforms/python/integrations/django/), [opções de configuração](https://docs.sentry.io/platforms/python/configuration/options/) e [dados coletados](https://docs.sentry.io/platforms/python/data-management/data-collected/). O que o SDK anexa e como limitar.
- 📄 Documentação oficial: [Sentry para Celery](https://docs.sentry.io/platforms/python/integrations/celery/). Erros nas tarefas (não executei).
- 📄 Documentação oficial: [Prometheus — visão geral](https://prometheus.io/docs/introduction/overview/), [práticas de instrumentação](https://prometheus.io/docs/practices/instrumentation/), [nomes](https://prometheus.io/docs/practices/naming/) e [histogramas](https://prometheus.io/docs/practices/histograms/).
- 📄 Documentação oficial: [`prometheus_client` — modo multiprocesso](https://prometheus.github.io/client_python/multiprocess/). Pasta, limpeza e `mode` dos gauges.
- 📄 Livro online: [Google SRE — Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/). Os quatro sinais de ouro.
- 📄 Documentação oficial: [Django — `SECURE_REDIRECT_EXEMPT`](https://docs.djangoproject.com/en/5.2/ref/settings/#secure-redirect-exempt).
- 🏋️ Prática extra: provoque um 500 de propósito no ambiente local (com o transporte falso ou um projeto gratuito do Sentry), mude `RELEASE` entre duas execuções e descreva o que você veria na lista de *issues* de cada release.

## ✅ Checklist da aula
- [ ] Sei escolher entre log, erro, métrica e trace
- [ ] O Sentry só liga com DSN, envia `release`/`environment` e **não** envia dados pessoais (testado)
- [ ] Sei por que `send_default_pii` saiu e o que usar no lugar
- [ ] O rótulo das métricas é o padrão da rota, e há um teste contra IDs
- [ ] Mostrei a diferença entre 1 e 2 processos com e sem modo multiprocesso
- [ ] O `/metrics/` é protegido por token, escondido no Nginx e isento do redirecionamento
