# 06. Desafio técnico simulado (take-home) — parte 1: relatório de vendas

> ⏱️ ~1h30 de leitura/correção + **2 h de execução do desafio** · Módulo 16 · Pré-requisitos: aulas 01–05

## 🎯 Objetivos
Ao final desta aula você consegue:
- Ler um enunciado de take-home e transformá-lo em critérios de aceite
- Gerenciar o tempo (planejar, entregar o essencial, documentar o que ficou de fora)
- Tratar dados sujos: validar, rejeitar com motivo, nunca "adivinhar"
- Entregar com testes, README de decisões e execução reproduzível
- Autoavaliar a entrega com a mesma régua de quem corrige

## 🤔 Por que isso importa
Muitas empresas pedem um desafio para fazer em casa. Quem corrige olha: **funciona?** **está testado?** **explica as decisões?** **sabe o que deixou de fora?** Entregar menos, mas correto e honesto, vence entregar muito e quebrado.

## 💡 Intuição (explicação simples)
É um mini-projeto com prazo, como no trabalho. Planeje como quem monta uma refeição com hora marcada: primeiro o prato principal (o requisito obrigatório), depois o acompanhamento (qualidade), e só então a sobremesa (extras).

## 🔬 Como funciona por dentro
**Cronograma sugerido para 2 h:**

| Minutos | O que fazer |
|---|---|
| 0–10 | Ler o enunciado duas vezes; listar requisitos e *perguntas/premissas* |
| 10–25 | Esqueleto: CLI, leitura em fluxo, um teste vermelho |
| 25–80 | Regras de validação e agregações, um teste por regra |
| 80–100 | Casos de borda, código de saída, arquivo grande |
| 100–120 | README (decisões, limitações), `ruff`, rodar tudo em diretório limpo |

Pontos do enunciado que viram decisões: o que fazer com status que não é `pago`? duplicidade vale a primeira ou a última ocorrência? preço `1,250` é 1,25 ou 1250? Quando o enunciado é omisso, **escolha, documente e teste**. (Numa vaga real, pergunte.)

## 🛠️ Exemplo prático
Enunciado completo: [`take-home-1/ENUNCIADO.md`](../projeto/referencia-m16/take-home-1/ENUNCIADO.md). **Faça a sua versão antes de olhar a referência** ([`src/relatorio.py`](../projeto/referencia-m16/take-home-1/src/relatorio.py)).

Execução real da referência com o CSV de exemplo (16 linhas de dados):
```bash
cd projeto/referencia-m16/take-home-1 && uv run --project .. python -m src.relatorio dados/vendas.csv
```
```text
Linhas lidas: 16  |  rejeitadas: 6
Receita total (pedidos pagos): R$ 4603.90
Receita por dia:
  2026-11-01  R$ 258.80
  2026-11-02  R$ 1648.00
  2026-11-04  R$ 2697.10
Top SKUs: INF-001 (6), INF-002 (5), AUD-010 (3)
Rejeitadas:
  linha 7: data inválida: '2026/11/03'
  linha 8: quantidade deve ser > 0: 0
  linha 9: quantidade não numérica: 'abc'
  linha 10: preço negativo ou inválido: '-5.00'
  linha 11: pedido_id duplicado: 1001
  linha 12: SKU vazio
exit=0
```
Arquivo inexistente: `erro: [Errno 2] No such file or directory: 'nao_existe.csv'` e `exit=2`.

Decisões de desenho (e o que provam):
- **`Decimal` e `parse_preco`:** `"1.250,00"` (formato brasileiro) vira 1250.00; `"1,250"` é **ambíguo** e é rejeitado, em vez de chutar.
- **Leitura em fluxo:** `csv.DictReader` linha a linha. Medi 200 mil linhas (7,8 MB gerados aqui): **pico de 19,9 MB** com `tracemalloc` (que deixa a execução mais lenta: 2,7 s não é o tempo "limpo"). A memória cresce com os **ids únicos** guardados no `set`; isso está no README como limitação.
- **Rejeitar com número da linha** (começando em 2, pois a 1 é o cabeçalho).
- **17 testes** (`uv run pytest -q take-home-1`): cada regra, cabeçalho errado/coluna extra, CLI com `--json` e código de saída, e o arquivo grande.

## 🧠 Pausa para lógica
O pedido `1001` aparece duas vezes e a segunda tem valor diferente. A referência mantém a primeira. Cite uma situação real em que manter a **última** seria a decisão certa e o que mudaria no código.
<details><summary>Solução</summary>

Quando o arquivo é um *log de correções* (a última linha é a versão mais recente do pedido). Em vez de `vistos: set`, guardaria um dicionário `pedido_id → linha` e agregaria **depois** da leitura (mais memória). Por isso a decisão deve estar no README.
</details>

## ⚠️ Erros comuns e boas práticas
- `float` para dinheiro (`0.1 + 0.2 = 0.30000000000000004`, aula 03).
- `readlines()` num arquivo grande; engolir exceção com `except: pass`.
- Corrigir dado "no chute" (assumir `1,250` = 1,25) sem avisar.
- Código de saída sempre 0, ou stack trace para o usuário quando o arquivo não existe.
- README genérico: "como rodar" sem **decisões** e **limitações**.
- Entregar sem rodar num diretório limpo (esquece dependência ou arquivo).

## 🧩 Exercícios
1. **(Fixação)** Liste os 6 motivos de rejeição do exemplo e diga em qual função cada um é detectado.
2. **(Aplicação no MiniShop)** Refaça este desafio **sem olhar a referência**, com cronômetro de 2 h.
   - [ ] CLI + `--json`
   - [ ] `Decimal` e leitura em fluxo
   - [ ] Rejeições com linha e motivo
   - [ ] ≥ 10 testes passando
   - [ ] README com decisões e "o que ficou de fora"
   - [ ] Registrei o tempo real gasto e onde estourou
3. **(Desafio)** Adicione `--desde AAAA-MM-DD` e `--formato csv` sem quebrar os testes existentes.

<details><summary>Solução do exercício 1</summary>

Data inválida, quantidade ≤ 0, quantidade não numérica, SKU vazio, `pedido_id` duplicado e status desconhecido: `validar`. Preço negativo/inválido/ambíguo: `parse_preco` (chamada por `validar`). Número de colunas incorreto: `processar`.
</details>

## 🎤 Na entrevista
**"Como você lidou com dados sujos?"** Validei cada linha, rejeitei com motivo e número da linha, não corrigi no chute e relatei o resumo. **"E se o arquivo tivesse 10 GB?"** Já leio em fluxo; o gargalo é o `set` de ids, então usaria ordenação externa, um banco, ou um filtro de Bloom (aceitando falsos positivos). **"O que faltou?"** Fuso/moeda, paralelismo, tipos de dado: está no README.

## 📚 Para ir além
- 📄 [Python — módulo `csv`](https://docs.python.org/pt-br/3/library/csv.html) (HTTP 200 em 2026-11-09)
- 📄 [Python — módulo `decimal`](https://docs.python.org/pt-br/3/library/decimal.html)
- 📄 [Python — `argparse`](https://docs.python.org/pt-br/3/library/argparse.html)
- 🏋️ Prática extra: gere um CSV de 2 milhões de linhas e meça tempo e memória sem `tracemalloc` (use `/usr/bin/time -v`).

## ✅ Checklist da aula
- [ ] Fiz o desafio em ≤ 2 h (ou registrei o motivo do estouro)
- [ ] Comparei com a referência e anotei 3 diferenças
- [ ] README tem decisões e limitações
