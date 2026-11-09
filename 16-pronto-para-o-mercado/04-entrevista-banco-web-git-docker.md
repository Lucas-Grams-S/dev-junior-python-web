# 04. Entrevista: banco, web, Git e Docker

> ⏱️ ~1h30 · Módulo 16 · Pré-requisitos: Módulos 2, 3, 6, 9, 11 e 12

## 🎯 Objetivos
Ao final desta aula você consegue:
- Explicar `JOIN` × `LEFT JOIN`, `NULL`, índice e transação com exemplos que você executou
- Explicar idempotência e a escolha de status HTTP
- Diferenciar `merge`, `rebase`, `reset` e `revert` e recuperar trabalho com `reflog`
- Explicar imagem × container e o que há num Dockerfile
- Responder "como você depuraria isto?" com um roteiro

## 🤔 Por que isso importa
Depois do Python, a entrevista cobre o **ecossistema**: SQL (quase sempre), HTTP, Git e Docker. São perguntas de conceito com pegadinha, e dá para treinar com experimentos de 10 linhas.

## 💡 Intuição (explicação simples)
Banco = fichário com regras; índice = índice remissivo do livro; transação = "ou faz tudo ou não faz nada". HTTP = pedido e resposta com combinados (verbos, status). Git = máquina do tempo com ramos. Docker = marmita lacrada com tudo que o programa precisa.

## 🔬 Como funciona por dentro
Roteiro para depurar em voz alta (vale para qualquer pergunta "isto está lento/quebrado"): **reproduzir → medir/ler o erro → isolar (bisseção) → hipótese → teste → correção + teste que impede a volta.**

HTTP, o que mais cai: `GET` seguro e idempotente; `PUT/DELETE` idempotentes; `POST` não. 401 = não autenticado, 403 = autenticado sem permissão, 404 = não existe, 409 = conflito de estado, 422 = corpo inválido, 429 = limite de taxa. Idempotente significa **mesmo efeito** ao repetir, não necessariamente a mesma resposta.

Docker: **imagem** = receita congelada em camadas (somente leitura); **container** = processo isolado criado de uma imagem; **volume** = dados que sobrevivem ao container; `COPY` das dependências antes do código aproveita o cache de camadas; segredos não vão na imagem.

## 🛠️ Exemplo prático
**SQL** (arquivo [`entrevista/sql_pegadinhas.py`](../projeto/referencia-m16/entrevista/sql_pegadinhas.py), SQLite em memória). Tabelas: `clientes` (Ana, Bruno, Carla) e `pedidos` (um deles com `cliente_id` NULL).

```bash
cd projeto/referencia-m16 && uv run python entrevista/sql_pegadinhas.py
```
```text
-- 1) INNER JOIN: Carla some
   -> [('Ana', 50), ('Ana', 100), ('Bruno', 70)]
-- 2) LEFT JOIN: Carla aparece com NULL
   -> [('Ana', 50), ('Ana', 100), ('Bruno', 70), ('Carla', None)]
-- 3) LEFT JOIN + WHERE no lado direito vira INNER (Carla some de novo)
   -> [('Ana',), ('Ana',)]
-- 4) mesmo filtro no ON preserva Carla
   -> [('Ana', 50), ('Ana', 100), ('Bruno', None), ('Carla', None)]
-- 5) NULL: = NULL não casa; IS NULL casa
   -> [(0, 1)]
-- 6) NOT IN com NULL na subconsulta devolve vazio
   -> []
-- 7) NOT EXISTS é o jeito seguro
   -> [('Carla',)]
-- 8) COUNT(*) × COUNT(coluna)
   -> [(4, 3)]
-- 9) WHERE × HAVING
   -> [(1, 150)]
-- 10) sem índice: ['SCAN pedidos']
   com índice: ['SEARCH pedidos USING INDEX pedidos_cliente (cliente_id=?)']
-- 11) transação desfeita: CHECK constraint failed: saldo >= 0 | saldos: [(1, 100), (2, 0)]
```
(Consultas completas no arquivo.) Lições: o filtro na cláusula `WHERE` sobre a tabela da direita anula o `LEFT JOIN`; `NOT IN` com `NULL` é armadilha clássica (`NULL` torna a comparação "desconhecida"); `COUNT(*)` conta linhas, `COUNT(col)` ignora `NULL`; o índice muda o plano de `SCAN` para `SEARCH` (em tabela de 4 linhas não muda o tempo; o ponto é o **plano**). Em PostgreSQL use `EXPLAIN (ANALYZE)`; o texto do plano do SQLite é diferente.

**HTTP** ([`entrevista/http_idempotencia.py`](../projeto/referencia-m16/entrevista/http_idempotencia.py), usa a API do take-home 2):
```text
POST /salas      -> 201 {'id': 1, 'nome': 'A', 'capacidade': 4}
POST /salas (2x) -> 409 (não é idempotente: nome único recusa)
POST /reservas   -> 201 | repetido -> 409 {'detail': 'conflito com a reserva 1'}
DELETE 1ª vez    -> 204 | 2ª vez -> 404
GET /reservas/x  -> 422 (entrada inválida = 422, não 500)
```
`DELETE` é idempotente no **efeito** (a reserva fica apagada) embora o status mude de 204 para 404. Para tornar `POST` seguro contra repetição (rede que falha e o cliente reenvia) use `Idempotency-Key`, como no pedido do MiniShop.

**Git** ([`entrevista/git_lab.sh`](../projeto/referencia-m16/entrevista/git_lab.sh), repositório descartável, Git 2.53.0):
```text
== merge --no-ff            == rebase
*   fcc48ee merge main      * ec31a65 feature 2
|\                          * 9390d24 feature 1
| * b116b4f main avançou    * b116b4f main avançou
* | 6f34114 feature 2      * 3352dc3 base
* | 65cee72 feature 1
|/
* 3352dc3 base
```
O `rebase` reescreve os commits (hashes **novos**: `65cee72` → `9390d24`): nunca em ramo já compartilhado. Depois, o `git revert` criou um commit que desfaz o "commit ruim" sem apagar a história (seguro em ramo publicado); o `git reset --hard HEAD~2` perdeu o trabalho **na árvore**, mas o `reflog` mostrou `HEAD@{1}` e `git reset --hard 'HEAD@{1}'` o devolveu (`f365254`). O conflito `add/add` deixou os marcadores `<<<<<<<`, `=======`, `>>>>>>>` no arquivo `k`; `git merge --abort` volta ao estado anterior.

**Docker:** não executei Docker nesta aula (já feito no módulo 11). Revise `referencia-api-m14/Dockerfile` e explique, linha a linha, em voz alta: base `python:3.13-slim`, multi-stage, dependências antes do código (cache), usuário não-root, `CMD` em forma exec.

## 🧠 Pausa para lógica
Uma tabela `pedidos` tem 10 milhões de linhas e `WHERE status = 'pago'` é lenta. Um colega propõe indexar `status`. Que pergunta você faz antes?
<details><summary>Dica e solução</summary>

Dica: seletividade. Se 95% das linhas são `pago`, o índice quase não ajuda (o banco prefere varrer). Pergunte a distribuição e leia o `EXPLAIN`; um índice **parcial** ou composto com a coluna de ordenação pode servir melhor.
</details>

## ⚠️ Erros comuns e boas práticas
- `git push --force` em ramo compartilhado (use `--force-with-lease` e só no seu ramo).
- `SELECT *` e `OFFSET` enorme em listagens; consulta em laço (N+1).
- Confundir 401 com 403, ou devolver 200 com `{"erro": ...}`.
- Mensagem real do Git: `CONFLICT (add/add): Merge conflict in k` / `Automatic merge failed; fix conflicts and then commit the result.`
- Container sem `healthcheck`, rodando como root, com `.env` copiado na imagem.

## 🧩 Exercícios
1. **(Fixação)** Escreva, sem olhar, a consulta "clientes sem nenhum pedido" de duas formas (`LEFT JOIN … IS NULL` e `NOT EXISTS`) e explique quando `NOT IN` falha.
2. **(Aplicação no MiniShop)** Rode `EXPLAIN` (PostgreSQL) na listagem de produtos do seu projeto e explique em voz alta o plano; depois simule um conflito de merge e resolva.
   - [ ] Plano lido e explicado (índice usado ou não, por quê)
   - [ ] Conflito criado, resolvido e commitado
   - [ ] Recuperei um commit "perdido" com `reflog`
3. **(Desafio)** Explique o caminho completo de `curl https://loja.exemplo/api/produtos` (DNS → TCP → TLS → Nginx → Gunicorn/Uvicorn → Django → banco → resposta).

<details><summary>Solução do exercício 1</summary>

`SELECT c.nome FROM clientes c LEFT JOIN pedidos p ON p.cliente_id=c.id WHERE p.id IS NULL` e `… WHERE NOT EXISTS (SELECT 1 FROM pedidos p WHERE p.cliente_id=c.id)`. `NOT IN (subconsulta)` devolve vazio se a subconsulta tiver **qualquer** `NULL` (executado acima: resultado `[]`).
</details>

## 🎤 Na entrevista
**Diferença entre `INNER` e `LEFT JOIN`?** O `LEFT` mantém as linhas da esquerda sem par, com `NULL`; cuidado com filtro no `WHERE`. **O que é uma transação / ACID?** Conjunto de operações atômico; Atomicidade, Consistência, Isolamento, Durabilidade; exemplo da transferência. **Merge ou rebase?** Merge preserva a história e é seguro em ramo compartilhado; rebase deixa linear mas reescreve hashes, então só em ramo meu. **Imagem × container?** Receita × processo em execução criado dela.

## 📚 Para ir além
- 📄 [Pro Git (PT-BR)](https://git-scm.com/book/pt-br/v2) e [`git rebase`](https://git-scm.com/docs/git-rebase) (HTTP 200 em 2026-11-09)
- 📄 [MDN — Métodos de requisição HTTP](https://developer.mozilla.org/pt-BR/docs/Web/HTTP/Reference/Methods)
- 📄 [SQLite — EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html)
- 📄 [Docker — Boas práticas de Dockerfile](https://docs.docker.com/build/building/best-practices/)
- 🏋️ Prática extra: refaça as consultas de `recursos/sql/loja.sql` explicando cada `JOIN` em voz alta.

## ✅ Checklist da aula
- [ ] Rodei os três laboratórios e expliquei cada saída
- [ ] Sei recuperar um commit com `reflog`
- [ ] Sei explicar 401/403/404/409/422/429 e idempotência
