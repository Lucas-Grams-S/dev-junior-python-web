# Take-home 1 — Relatório de vendas (tempo-alvo: 2 h)

A loja recebe um CSV diário de vendas (`dados/vendas.csv`, colunas `pedido_id,data,sku,quantidade,preco_unitario,status`). O arquivo vem **sujo**.

Entregue um programa de linha de comando `python -m src.relatorio dados/vendas.csv` que imprime (e `--json` devolve em JSON):
1. Receita total **somente de pedidos com status `pago`**.
2. Receita por dia (ordem cronológica).
3. Os 3 SKUs com maior quantidade vendida (empate: ordem alfabética).
4. Uma seção de **linhas rejeitadas** com número da linha e o motivo (data inválida, quantidade ≤ 0 ou não numérica, preço negativo/inválido, `pedido_id` duplicado, SKU vazio, status desconhecido).

Regras: dinheiro com `Decimal` (nunca `float`); arquivo grande não pode ser carregado inteiro na memória; código de saída 0 se leu o arquivo (mesmo com rejeições), 2 se o arquivo não existe/cabeçalho errado; testes com `pytest`; README curto com decisões e o que ficou de fora.
