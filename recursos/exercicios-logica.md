# exercicios-logica

*(preenchido ao longo da geração dos módulos)*

## Módulo 0
**Média com lista vazia** (aula 0.05, nível ★). Defina o comportamento de `media([])`: devolver `None` ou levantar `ValueError`? Justifique e implemente as duas versões. *Variação:* o que acontece com `None + 1`? (`TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'`)

## Módulo 1
| Aula | Problema | Nível | Conceito |
|---|---|---|---|
| 1.01 | Parcelas que somam exatamente o total (`divmod` em centavos) | ★ | aritmética inteira |
| 1.02 | Ano bissexto | ★ | booleanos |
| 1.03 | Paginação (`offset/limit`, total de páginas) | ★★ | off-by-one |
| 1.04 | Total do carrinho com cupom | ★★ | `Decimal`, funções |
| 1.05 | Busca linear vs binária (contando comparações) | ★★ | O(n) vs O(log n) |
| 1.06 | Processar eventos duplicados (idempotência com `set`) | ★★ | hash, sets |
| 1.07 | Validar CPF (dígitos verificadores) | ★★★ | laços, strings |
| 1.08 | Entrada válida com 3 tentativas | ★★ | exceções |
| 1.09 | Importação de CSV com erros por linha | ★★★ | arquivos, sets |
| 1.10 | Resolver import circular | ★★ | arquitetura |
| 1.11 | Palíndromo guiado por testes | ★★ | TDD |
| 1.13 | Frete por estratégia sem `if/elif` | ★★★ | polimorfismo |
| 1.14 | Ordenação por vários critérios | ★★ | estabilidade do `sorted` |
| 1.15 | Fibonacci infinito e primos com gerador | ★★★ | geradores |
| 1.16 | Decorator de retentativa | ★★★ | decorators |
| 1.17 | Estimar Big-O de 5 trechos | ★★ | complexidade |
| 1.18 | Race condition na retirada de estoque | ★★★ | concorrência |
| 1.19 | Top-N com `sorted` vs `heapq.nlargest` | ★★★ | complexidade |

### Lista extra (resolva com testes)
★ FizzBuzz · soma de dígitos · inverter string · contar vogais · maior e menor sem `max`/`min`
★★ Anagramas · remover duplicados mantendo ordem · rotacionar lista · two-sum com `dict` · números primos até N · parênteses balanceados (pilha) · contagem de palavras de um texto
★★★ Mesclar intervalos · LRU cache do zero · calculadora de expressões com pilha · torres de Hanói · permutações recursivas · validar sudoku

## Módulo 2
| Aula | Problema | Nível | Conceito |
|---|---|---|---|
| 2.01 | IP ↔ inteiro e pertencimento a um CIDR com bits | ★★★ | operações bit a bit |
| 2.02 | Parser de requisição HTTP bruta (headers case-insensitive, `Content-Length`) | ★★ | strings, dicts |
| 2.03 | `parse_query` com `+`, `%XX` e UTF-8 | ★★★ | codificação |
| 2.03 | Por que IDs de sessão exigem `secrets` | ★ | aleatoriedade |
| 2.04 | Média vs p95 de latências | ★★ | estatística, ordenação |
| 2.05 | Roteador por segmentos e prioridade de rotas | ★★ | listas, especificidade |
| 2.05 | Race condition com `Lock` (30 clientes, estoque 10) | ★★★ | concorrência |

Lista extra: validar IPv4/IPv6 sem `ipaddress` · calcular a máscara de sub-rede a partir de `/n` · contar requisições por status em um log de acesso · agrupar URLs por host · detectar rajadas (mais de N requisições em T segundos por IP) com janela deslizante.

## Módulo 3
| Aula | Problema | Nível | Conceito |
|---|---|---|---|
| 3.01 | Join à mão: O(n·m) × hash O(n+m); produtos por categoria | ★★ | hash, complexidade |
| 3.02 | Dependência funcional `A → B` a partir de linhas | ★★ | dicts, normalização |
| 3.03 | Seed idempotente (SQL `ON CONFLICT` × Python) | ★★ | idempotência |
| 3.04 | `LIMIT/OFFSET`, desempate, paginação por cursor | ★★ | off-by-one, ordem total |
| 3.05 | `left_join` em Python em O(n+m) | ★★★ | hash join |
| 3.06 | Ranking de mais vendidos: SQL × `Counter` com desempate | ★★ | ordenação estável |
| 3.07 | 19 exercícios de SQL (blocos A–E) e acumulado `accumulate` × `sum() OVER` | ★–★★★ | conjuntos |
| 3.08 | Altura de uma B-tree e busca binária × linear | ★★ | O(log n) |
| 3.09 | Transação como context manager com rollback | ★★★ | atomicidade |
| 3.10 | Filtros dinâmicos sem concatenar valores | ★★★ | segurança |
| 3.11 | Cache com TTL (dict + expiração) | ★★ | hash O(1) |
| 3.12 | Ordem de criação/remoção de tabelas (ordenação topológica) | ★★★ | grafos |

Lista extra: two-sum em SQL (self join) · duplicados em uma tabela (`GROUP BY ... HAVING count(*) > 1`) · segundo maior salário (`DISTINCT`, `OFFSET`, janela) · clientes que compraram em 3 meses seguidos (janelas/`lag`) · pares de produtos comprados juntos · medir `EXPLAIN` antes/depois para 5 consultas.

## Módulo 4
| Aula | Problema | Nível | Conceito |
|---|---|---|---|
| 4.01 | `validar_checkout` no servidor (CPF, CEP, UF, qtd) | ★★★ | validação, segurança |
| 4.02 | Calculadora de especificidade CSS e "qual regra vence?" | ★★★ | strings, regex, comparação lexicográfica |
| 4.03 | Número de colunas do `auto-fill` por fórmula (verificado no navegador) | ★★ | aritmética, floor |
| 4.04 | `totalCarrinho` em centavos e paginação em JS | ★★ | inteiros, off-by-one |
| 4.05 | Índice invertido × busca linear; `debounce` | ★★★ | hash, tempo |
| 4.06 | `mapLimit` (concorrência limitada); `retry` com backoff | ★★★ | assíncrono |
| 4.07 | Cache de CEP com TTL e deduplicação de chamadas | ★★★ | Promises, cache |
| 4.08 | Contraste WCAG; ajustar cor até 4,5:1 (busca binária) | ★★★ | números, busca binária |

Lista extra: converter "R$ 1.234,56" para centavos sem `float` · agrupar produtos por categoria com `reduce` · ordenar por vários critérios (`sort` estável) · `groupBy` e `partition` · "flatten" recursivo de arrays aninhados · `throttle` · implementar `Promise.all`/`race` do zero · detectar parênteses balanceados em um template.

## Módulo 5 — Django
| Aula | Problema | Nível | Conceito |
|---|---|---|---|
| 5.01 | Mini WSGI e `aplicar_middlewares` | ★★★ | funções de ordem superior, ciclo da requisição |
| 5.02 | Roteador com *converters* e `reverse` | ★★★ | regex, strings |
| 5.03 | Mini motor de templates (`{{ a.b }}`, filtros) | ★★★ | parsing, regex |
| 5.04 | Ler o grafo de migrações | ★★★ | grafos, ordenação topológica |
| 5.05 | Um `Q` de brinquedo (`&`, `|`, `~`) | ★★★ | métodos especiais, composição |
| 5.06 | `GROUP BY` à mão em uma passada | ★★ | dicionários, agregação |
| 5.07 | Modelo de custo do N+1 | ★★ | aritmética, estimativa |
| 5.08 | Tabela de texto por introspecção | ★★★ | metaprogramação |
| 5.09 | MRO por C3 na mão | ★★★★ | herança múltipla, listas |
| 5.10 | Validador de CPF | ★★ | dígitos verificadores |
| 5.11 | Mini *hasher* com PBKDF2 e atualização de hash | ★★★ | criptografia básica, tempo constante |
| 5.12 | Permissões efetivas com herança e ciclos | ★★★ | grafos, DFS |
| 5.13 | Nome de arquivo seguro | ★★ | strings, segurança |
| 5.14 | Leitor de `.env` | ★★ | parsing |
| 5.15 | Paginação por cursor `(preço, id)` | ★★★ | comparação de tuplas, keyset |
| 5.16 | Cupom em centavos sem `float` | ★★ | inteiros, arredondamento |
| 5.17 | Pedidos "tudo ou nada" (atomicidade) | ★★★ | transação simulada, `Counter` |
| 5.18 | Sincronizador idempotente | ★★ | estado desejado, idempotência |

Lista extra: janela de páginas (`1 … 4 5 6 … 20`) · agrupar pedidos por dia e somar · detectar *deadlock* em um grafo de espera · token bucket para limitar tentativas de login · validar CNPJ · implementar um *LRU cache* · calcular o troco com o menor número de notas.

## Módulo 6 — APIs REST
| Aula | Problema | Nível | Conceito |
|---|---|---|---|
| 6.01 | `pode_repetir(metodo, tem_chave)` e decorador de chave de idempotência | ★★ | idempotência, retry seguro |
| 6.02 | Linter de rotas (verbo no caminho, plural, kebab-case, aninhamento) e regra de `{id}` por método | ★★ | regex, convenções |
| 6.03 | Mini serializer com campos, conversão e erros acumulados | ★★★ | validação, dicionários |
| 6.04 | Mini router: gerar rotas a partir de um viewset e de `@acao` | ★★★ | introspecção, decoradores |
| 6.05 | Achatar o dicionário de erros do DRF em linhas `caminho: mensagem` | ★★ | recursão |
| 6.06 | JWT HS256 à mão: assinar, verificar, expiração, `alg: none` | ★★★ | HMAC, Base64URL, segurança |
| 6.07 | Permissões compostas com `&`, `\|` e `~` (`Autenticado`, `TemPerm`, `Dono`) | ★★★ | métodos especiais, composição |
| 6.08 | Ordenação multi-campo estável com lista permitida | ★★ | `sort` estável |
| 6.09 | Paginação por `OFFSET` × cursor com inserção concorrente | ★★★ | consistência, keyset |
| 6.10 | Classificar mudanças de contrato (compatível/quebra) e sugerir a versão; diff de OpenAPI | ★★★ | semver, grafos de dados |
| 6.11 | Simular a decisão de CORS (origem, preflight, cabeçalhos) | ★★ | conjuntos, regras |
| 6.12 | Cobertura de rotas do contrato a partir do `schema.yml` e do código dos testes | ★★★ | regex, arquivos |
| 6.13 | Armazém de chaves de idempotência com TTL, hash do corpo e relógio injetável | ★★★ | hashing, tempo |
| 6.14 | `comRetry` com `Retry-After` e backoff exponencial (JavaScript) | ★★★ | assíncrono, injeção de dependência |

Lista extra: implementar um *token bucket* para o throttling · validar o corpo de uma requisição contra um esquema JSON simples · calcular o ETag (hash) de uma resposta e responder `304` · detectar rotas duplicadas num roteador · gerar o `Allow` de uma rota a partir dos métodos do viewset · converter `?ordering=-price,name` em tuplas de ordenação · implementar *long polling* simples com `threading.Event`.

## Módulo 7 — Comunicação síncrona e assíncrona
| Aula | Problema | Nível | Conceito |
|---|---|---|---|
| 7.01 | Classificar funções por razão CPU/parede; vazão e número de workers | ★★ | medição, dimensionamento |
| 7.02 | `MiniPool`: pool de threads com fila e "pílula de veneno" | ★★★ | `queue`, `Thread`, `Lock` |
| 7.03 | Laço de eventos de brinquedo com geradores e `heapq` | ★★★★ | geradores, agendamento cooperativo |
| 7.04 | Disjuntor (*circuit breaker*) com relógio injetado | ★★★ | máquina de estados, injeção de dependência |
| 7.05 | Middleware ASGI de *load shedding* | ★★★ | ASGI, `nonlocal`, `try/finally` |
| 7.06 | `MiniBroker` com ack e prazo de visibilidade (at-least-once) | ★★★ | filas, reentrega |
| 7.07 | Consumidor idempotente com reclamo (*lease*) | ★★★ | atomicidade, prazos |
| 7.08 | Interpretador de cron de 5 campos validado contra o Celery | ★★★ | conjuntos, datas, fusos |
| 7.09 | Redutor de eventos independente da ordem (estado que só avança) | ★★★ | comutatividade, idempotência |
| 7.10 | Relé do outbox com queda entre publicar e marcar | ★★★ | at-least-once, deduplicação |

Lista extra: *token bucket* para *throttling* · fila de prioridade com *aging* · *rate limiter* de janela deslizante · detectar *deadlock* num grafo de espera · simular *consistent hashing* para particionar consumidores · implementar `asyncio.gather` e `asyncio.timeout` do zero · reconectar um WebSocket com *backoff* e *jitter* e ressincronizar o estado.

## Módulo 8 — Estrutura de projetos e arquitetura
| Aula | Problema | Nível | Conceito |
|---|---|---|---|
| 8.01 | Separar domínio puro de I/O e achar ciclos num grafo de imports | ★★★ | grafos, dependências |
| 8.02 | Unidade de trabalho com rollback num *fake* em memória | ★★★ | transação, snapshot |
| 8.03 | Disponibilidade combinada e função × hierarquia de classes | ★★ | probabilidade, KISS |
| 8.04 | Tradutor de estados de provedor com `Decimal` e centavos | ★★ | adaptador, dinheiro |
| 8.05 | Disponibilidade de 4 dependências síncronas a 99,95% | ★★ | probabilidade, SLA |
| 8.06 | `env_list`/`database_from_url` com casos de borda | ★★ | parsing, falhar cedo |
| 8.07 | Ordem de commits ao trocar `float` por `Decimal` num legado | ★★ | refatoração × correção |

## Módulo 9 — Segurança
| Aula | Problema | Nível | Conceito |
|---|---|---|---|
| 9.01 | Ordenar achados por risco (probabilidade × impacto) e desempatar | ★★ | priorização |
| 9.02 | *Allowlist* de colunas para `ORDER BY` | ★★ | injeção, identificadores |
| 9.03 | Por que o CORS não impede um `POST` simples | ★★ | CSRF × CORS |
| 9.04 | Migrar hashes `md5` para Argon2id sem conhecer as senhas | ★★★ | derivação de chave, migração |
| 9.05 | Matriz de autorização de uma rota nova (e a mutação) | ★★ | IDOR, testes |
| 9.06 | Tentativas por hora com N workers e vários IPs | ★★ | limite de taxa |
| 9.07 | Consulta de marketing que exclui quem pediu eliminação | ★★ | LGPD, finalidade |

## Módulo 10 — Qualidade, testes e boas práticas
| Aula | Problema | Nível | Conceito |
|---|---|---|---|
| 10.01 | Tempo de uma suíte por nível e o efeito de trocar E2E por unidade | ★★ | pirâmide, custo |
| 10.02 | `calcular_frete` com `parametrize`: produto cartesiano e fronteiras | ★★ | tabelas de casos |
| 10.03 | Cobertura de ramos de `desconto` com um só teste; mutante que sobrevive | ★★ | ramos, mutação |
| 10.04 | *Kata* de frete em TDD: a ordem dos testes e as implementações "fingidas" | ★★ | ciclo TDD, triangulação |
| 10.05 | Ordem correta de commits ao introduzir um formatador | ★★ | refatoração × formatação |
| 10.06 | O que fazer com um PR de 1 800 linhas e as 3 perguntas de segurança | ★★ | revisão, segurança |
| 10.07 | `.env` colado num assistente de IA e pacote sugerido que não existe | ★★ | LGPD, cadeia de suprimentos |

## Módulo 11 — Docker e containers
| Aula | Problema | Nível | Conceito |
|---|---|---|---|
| 11.01 | Espaço em disco de duas imagens que compartilham a base e de 30 containers | ★ | camadas compartilhadas |
| 11.02 | Quais camadas são refeitas ao mudar um arquivo, conforme a ordem do Dockerfile | ★★ | cache de camadas |
| 11.03 | Caminho crítico de inicialização com `depends_on` por condição; o que acontece se a migração falha | ★★ | grafo de dependências |
| 11.04 | Nomes de volume que um projeto Compose cria, a colisão e os passos seguros de recuperação | ★★ | nomes, segurança de dados |
| 11.05 | Serviço "Up" cujo tempo não cresce: crash loop, `RestartCount` e OOM | ★★ | diagnóstico por evidências |
| 11.06 | Workers necessários pela lei de Little (30 req/s × 0,4 s) e o risco das threads | ★★ | dimensionamento |


## Módulo 12 — CI/CD
| Aula | Problema | Nível | Conceito |
|---|---|---|---|
| 12.01 | Tempo de relógio × minutos de runner com matriz e `needs` | ★★ | paralelismo, custo |
| 12.02 | Taxa de erro global em rolling × canary com 10% de falha na versão nova | ★★ | risco, observabilidade |

## Módulo 13 — Introdução à nuvem com AWS
| Aula | Problema | Nível | Conceito |
|---|---|---|---|
| 13.01 | Custo por hora de uma pilha esquecida e o dia em que o alerta de 80% dispara | ★★ | custo, alertas |
| 13.02 | O que migra com pouco esforço e o que fica preso ao provedor | ★★ | lock-in |
| 13.03 | Avaliar requisições contra um `Allow s3:*` e um `Deny DeleteObject` em prefixo | ★★ | avaliação de políticas |
| 13.04 | Banco aberto ao mundo, alternativas e o SG como origem | ★★ | superfície de ataque |
| 13.05 | Custo do RDS ligado × parado × apagado | ★★ | custo, ciclo de vida |
| 13.06 | O que acontece com uma URL pré-assinada ao trocar a imagem ou revogar a permissão | ★★★ | credencial ao portador |
| 13.07 | EC2, Fargate e Lightsail para estudo e para loja real (disponibilidade) | ★★ | trade-offs |
| 13.08 | Custo "EC2-Other"/CloudWatch com tudo "limpo": hipóteses e onde olhar | ★★★ | diagnóstico de custos |

## Módulo 14 — Produção e observabilidade básica
| Aula | Problema | Nível | Conceito |
|---|---|---|---|
| 14.01 | Liveness que consulta o banco com 6 contêineres e 2 min de manutenção | ★★ | reinício em cascata |
| 14.02 | Cardinalidade ao adicionar `user_id` como rótulo | ★★ | séries × memória |
| 14.03 | TTL, invalidação falha e latência média por hit rate | ★★ | cache, média ponderada |
| 14.04 | Frequência × duração, índice composto, RPO e RTO | ★★★ | priorização, recuperação |

## Módulo 15 — FastAPI (comparativo)
| Aula | Problema | Nível | Conceito |
|---|---|---|---|
| 15.01 | `tags` enviado como string e por que `Decimal` | ★ | validação, tipos |
| 15.02 | Renomear coluna sem perder dados e com tabela grande | ★★★ | migrações, expandir e contrair |
| 15.03 | Tempo de uma rota com E/S em paralelo e passo de CPU | ★★ | `gather`, bloqueio |
| 15.04 | `await` esquecido, falso-positivo e série × paralelo | ★★ | testes async |
| 15.05 | Páginas, fora do intervalo e `OFFSET` com inserção | ★★ | paginação |
| 15.06 | "10× mais rápido" e a parte que domina o tempo | ★★ | Lei de Amdahl |

## Módulo 16 — Pronto para o mercado
| Aula | Problema | Nível | Conceito |
|---|---|---|---|
| 16.01 | "10 mil pedidos por minuto" sem medição | ★ | evidência verificável |
| 16.02 | Vaga pede tecnologia que você só viu em simulador | ★ | honestidade seletiva |
| 16.03 | Default mutável compartilhado entre requisições | ★★ | estado global escondido |
| 16.04 | Índice em coluna com 95% de um valor | ★★ | seletividade |
| 16.05 | Intervalo contido em outro e o `max` | ★★ | bordas |
| 16.06 | Pedido duplicado: primeira × última ocorrência | ★★ | decisão e custo |
| 16.07 | Reservas que encostam e a sobreposição | ★★ | intervalos semiabertos |
