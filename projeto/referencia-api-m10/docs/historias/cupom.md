# História: aplicar cupom ao pedido

**Como** cliente, **quero** informar um cupom ao finalizar a compra, **para** pagar menos.

## Critérios de aceitação (Dado / Quando / Então)
1. **Cupom percentual.** *Dado* o cupom `PROMO10` (10%), *quando* o subtotal é R$ 200,00, *então* o desconto é R$ 20,00.
2. **Desconto limitado.** *Dado* um cupom fixo de R$ 500,00, *quando* o subtotal é R$ 120,00, *então* o desconto é R$ 120,00 (nunca passa do subtotal).
3. **Cupom vencido.** *Dado* um cupom válido até 07/11/2026, *quando* hoje é 08/11/2026, *então* o pedido é recusado com "O cupom venceu em 07/11/2026.".
4. **Pedido mínimo.** *Dado* um cupom com mínimo de R$ 100,00, *quando* o subtotal é R$ 99,99, *então* o pedido é recusado informando o mínimo.
5. **Centavos.** *Dado* um desconto de 0,025, *quando* calculado, *então* vale R$ 0,03 (meio centavo para cima).

## Fora do escopo (nesta história)
Cupom por cliente, uso máximo e cumulativo (histórias futuras).

## Definição de pronto
Ver `scripts/definicao_de_pronto.sh`.
