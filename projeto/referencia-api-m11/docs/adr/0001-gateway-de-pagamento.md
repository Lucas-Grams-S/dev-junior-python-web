# ADR 0001: Gateway de pagamento atrás de uma porta (Adapter)

Status: aceito · Data: 2026-11-08

## Contexto
O provedor de pagamento ainda não está definido e pode mudar. Cada provedor tem API, estados e assinatura de webhook diferentes. O núcleo (`apps/payments/services.py`) não deve conhecer nenhum deles.

## Decisão
`PaymentGateway` (um `Protocol`) no vocabulário do MiniShop (`Cobranca`, `EventoPagamento`, valores em `Decimal`). Um adaptador por provedor (`GatewayFake`, `GatewayAcme`). `obter_gateway()` escolhe pelo `settings.PAYMENT_GATEWAY`. Retentativas só em falha transitória, com `Idempotency-Key` estável por pedido.

## Alternativas
- Chamar a API do provedor direto das views/serviços: mais rápido hoje, mas acopla o núcleo e dificulta trocar e testar.
- Biblioteca do provedor espalhada pelo código: mesmo acoplamento, e testes dependem da rede.

## Consequências
+ Trocar de provedor = novo adaptador + uma variável de ambiente; testes sem rede (`MockTransport`).
+ O núcleo não importa `httpx` (garantido por `import-linter`).
− Uma classe a mais por provedor e um teste de contrato para mantê-los alinhados.

## Quando rever
Se um provedor exigir um fluxo que a porta não expressa (por exemplo, 3-D Secure com redirecionamento), ampliar a porta em vez de vazar o detalhe para o núcleo.
