# Checkpoint — Módulo 16: Pronto para o mercado

> ⏱️ ~1h30 · Faça **sem consultar** as aulas na primeira tentativa. 30 min para o quiz, 60 min para a entrega.

## 📝 Quiz (10 questões)
1. Qual a ordem recomendada das seções de um README de portfólio e por que "341 testes" é melhor que "código limpo"? O que fazer ao achar um segredo no histórico do Git?
2. Escreva um bullet de currículo fraco e reescreva-o com a fórmula *verbo + o quê + tecnologia + prova*. Como listar uma tecnologia que você só praticou em simulador?
3. Preveja: `def add(x, l=[]): l.append(x); return l` chamada como `add(1)`, `add(2)`, `add(3, [])`. Explique o mecanismo e a correção.
4. Explique `[lambda: i for i in range(3)]` chamadas depois do laço, e a correção. Por que `0.1 + 0.2 != 0.3` e o que usar para dinheiro?
5. Dadas `clientes` e `pedidos`, por que `LEFT JOIN … WHERE p.status='pago'` "perde" clientes sem pedido? Como `NOT IN` com `NULL` falha e qual a alternativa? Qual a diferença entre `COUNT(*)` e `COUNT(col)`?
6. Diferencie 401, 403, 404, 409, 422 e 429. O que significa idempotente? `DELETE` é idempotente mesmo mudando o status de 204 para 404?
7. Compare `merge`, `rebase`, `reset --hard` e `revert`. Quando cada um é seguro? Como recuperar um commit "perdido" por um `reset --hard`?
8. Quais os 6 passos para resolver um problema de lógica em voz alta? Dê o padrão e a complexidade de `duas_somas`, `mesclar_intervalos` e `busca_primeira_ocorrencia`.
9. No take-home 1, por que `1,250` foi **rejeitado** em vez de corrigido? Por que ler em fluxo, e o que ainda cresce com o tamanho do arquivo?
10. No take-home 2, escreva a condição de sobreposição e diga por que "encostar" é permitido. Por que "checar e inserir" precisa de `BEGIN IMMEDIATE` (ou restrição no banco)? Que experimento mostrou que o teste de concorrência pode passar por sorte?

<details><summary>Gabarito</summary>

1. Título + frase + selo da CI → print real → o que demonstra → rodar em 3 comandos → decisões → limitações → autor. Número é **verificável** (qualquer pessoa roda `pytest`), adjetivo não. Segredo no histórico: **revogue/gere outro** (apagar o arquivo não basta; já foi exposto); reescrever histórico é último recurso.
2. Ex.: "Responsável pelo backend" → "Implementei a baixa de estoque transacional (Django, PostgreSQL) e testei a concorrência". Simulador: "noções (EC2/RDS/S3/IAM, praticado em simulador local)" — nunca como experiência em produção.
3. `[1, 2] [1, 2] [3]`: o default é avaliado **uma vez** e compartilhado. Correção: `l=None` e criar a lista dentro.
4. As lambdas capturam a **variável** `i`, que vale 2 no fim: `[2, 2, 2]`; correção `lambda i=i: i` → `[0, 1, 2]`. Binário não representa 0,1 exatamente (0.30000000000000004); use `Decimal("0.1")` criado de **texto**.
5. O `WHERE` sobre a tabela da direita descarta as linhas com `NULL` e vira `INNER`; ponha o filtro no `ON`. `NOT IN (subconsulta com NULL)` devolve vazio (comparação "desconhecida"); use `NOT EXISTS`. `COUNT(*)` conta linhas; `COUNT(col)` ignora `NULL` (executado: 4 × 3).
6. 401 não autenticado; 403 sem permissão; 404 inexistente; 409 conflito de estado; 422 corpo inválido; 429 limite de taxa. Idempotente = mesmo **efeito** ao repetir. `DELETE`: sim no efeito (a reserva fica apagada), apesar de 204 → 404.
7. `merge` preserva a história (seguro em ramo compartilhado); `rebase` deixa linear mas reescreve hashes (só em ramo seu); `reset --hard` descarta alterações locais (perigoso); `revert` cria um commit que desfaz outro (seguro em ramo publicado). Recuperar: `git reflog` e `git reset --hard 'HEAD@{n}'`.
8. Reformular → exemplos/bordas → força bruta → melhorar → codificar → testar e analisar. `duas_somas`: dicionário valor→índice, O(n)/O(n); `mesclar_intervalos`: ordenar e varrer, O(n log n); `busca_primeira_ocorrencia`: busca binária continuando à esquerda, O(log n).
9. Ambíguo (1,25 ou 1250?): adivinhar corrompe dinheiro em silêncio; rejeitar com motivo é auditável. Fluxo para não carregar o arquivo inteiro; cresce o `set` de ids únicos (pico medido de 19,9 MB para 200 mil linhas); solução para escala maior: ordenação externa, banco ou filtro de Bloom.
10. `existente.inicio < novo.fim E existente.fim > novo.inicio`; com desigualdades estritas, terminar às 10:00 e começar às 10:00 não colide. Sem trava, duas requisições leem "livre" e ambas inserem. Troquei `BEGIN IMMEDIATE` por `BEGIN`: o teste **falhou 12 de 15** vezes e **passou 3** (corrida nem sempre aparece); com `IMMEDIATE`, 15 de 15 passaram.
</details>

## 🛠️ Entrega prática
Repositório `minishop` na tag `v5.0-portfolio` (material de referência em `projeto/referencia-m16/`):
- [ ] **Portfólio:** `README.md` e `README.en.md` testados em clone novo; números conferidos; print real; limitações; sem segredos no histórico
- [ ] **Perfil:** ≤ 6 repositórios fixados; projeto principal claro
- [ ] **Currículo (PDF, 1 página)** e **LinkedIn** (título com tecnologias, "Sobre", destaque); links testados em janela anônima
- [ ] **Entrevista:** as 13 pegadinhas previstas por escrito (≥ 10 acertos), 5 usos reais de recursos da linguagem no seu código, as 3 práticas de SQL/Git/HTTP rodadas
- [ ] **Lógica:** 5 das 10 funções refeitas sem olhar, com testes e complexidade
- [ ] **Take-home 1** (2 h) e **take-home 2** (3 h) feitos por você, com testes, README e retrospectiva
- [ ] **Apresentação** do MiniShop em 5 minutos, gravada e cronometrada
- [ ] Tag: `git tag -a v5.0-portfolio -m "MiniShop: portfólio e preparação para entrevistas" && git push --follow-tags`

**Prova de fogo (60 min, sem consultar):** (1) uma pessoa que nunca viu o projeto lê o seu README e roda em 10 min: onde travou? (2) resolva ao vivo, falando, um problema novo de lógica que você nunca viu (ex.: "primeiro caractere que não se repete"); (3) responda: "Seu sistema vende o último item para duas pessoas ao mesmo tempo. Como você investiga, corrige e garante que não volte?".

## 🪞 Autoavaliação
Nota de 0 a 3. Se algum item ficar em **0 ou 1**, refaça a aula antes de se candidatar.

| Habilidade | Aula | Nota |
|---|---|---|
| README, decisões e limpeza do repositório | 01 | |
| Currículo e LinkedIn honestos e ajustados | 02 | |
| Fundamentos de Python em voz alta | 03 | |
| SQL, HTTP, Git e Docker em entrevista | 04 | |
| Lógica: roteiro, padrões e complexidade | 05 | |
| Take-home com dados sujos e entrega honesta | 06 | |
| Concorrência, fusos, apresentação e retrospectiva | 07 | |

## 🧠 Lógica: lista de verificação
Resolveu sem olhar: evidência verificável do README (16.01), versão do currículo por vaga (16.02), o default mutável em duas requisições (16.03), o índice em coluna pouco seletiva (16.04), o `max` no fim do intervalo (16.05), a última ocorrência vs. a primeira (16.06), o par encostando (16.07)? Marque o que faltou e refaça.

## 🧪 Estado de verificação deste módulo
**Executado (2026-11-09):** `projeto/referencia-m16` com Python 3.13: **57 testes** (27 de lógica, 17 do take-home 1, 13 do take-home 2) e `ruff` limpo; as 13 pegadinhas de Python; o laboratório SQL (SQLite em memória, 11 blocos); o laboratório de Git (2.53.0, repositório descartável: merge, rebase, revert, reflog, conflito); o experimento de idempotência na API de reservas; o relatório do take-home 1 com o CSV de exemplo; a medição de memória (200 mil linhas, pico de 19,9 MB); e o teste de concorrência repetido 15 vezes com `BEGIN` e 15 com `BEGIN IMMEDIATE`; links das aulas com HTTP 200.

**Descobertas e correções:** o README do take-home 2 afirmava que o teste de concorrência "falha" sem `IMMEDIATE`; medi **12 falhas em 15** e corrigi o texto; `git revert` não aceita `-q`; o `git merge` com conflito encerra o script sob `set -e`/`pipefail` (tratado); os números de memória usam `tracemalloc`, que deixa a execução lenta (o tempo não é "limpo").

**Não executado:** Docker nesta aula (feito no módulo 11); restrição de exclusão no PostgreSQL; autenticação no take-home 2; o script de coleta de vagas (LinkedIn, termos de uso); tornar o repositório público; candidaturas reais. Os números de portfólio (341 testes etc.) vêm dos marcos dos módulos anteriores e **devem ser reconferidos por você**.

🏁 Fim da trilha: continue estudando (um projeto seu, contribuições em código aberto) e candidate-se.
