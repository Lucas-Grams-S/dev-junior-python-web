# Take-home 1 — Relatório de vendas (solução de referência)

```bash
cd take-home-1
python -m src.relatorio dados/vendas.csv          # texto
python -m src.relatorio dados/vendas.csv --json   # JSON
cd .. && uv run pytest -q take-home-1             # 17 testes
```

## Decisões
- **`Decimal`** em todo cálculo; o JSON devolve texto (`"4603.90"`).
- **Leitura em fluxo** (`csv.DictReader` linha a linha), nunca `readlines()`.
- **Rejeitar com motivo** em vez de corrigir "no chute": preço ambíguo (`1,250`) é rejeitado; `1.250,00` (formato brasileiro) é aceito.
- Só **pedidos `pago`** entram na receita e no ranking; linhas válidas de outros status são lidas mas não somadas.
- Duplicidade de `pedido_id`: **vale a primeira ocorrência**, as seguintes são rejeitadas.
- Código de saída: 0 (leu), 2 (arquivo inexistente ou cabeçalho errado).

## O que ficou de fora (declare isto no seu README real)
- O conjunto de `pedido_id` vistos cresce com o número de ids **únicos** (medido: pico de ~19,9 MB para 200 mil linhas, arquivo de 7,2 MB). Para arquivos de bilhões de linhas: ordenar externamente, usar banco ou um filtro de Bloom (com falsos positivos).
- Fuso horário e moeda única (BRL) assumidos; datas só ISO `AAAA-MM-DD`.
- Sem paralelismo nem barra de progresso.
