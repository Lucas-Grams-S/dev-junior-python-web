# ADR 0002: MiniShop continua um monolito modular

Status: aceito · Data: 2026-11-08

## Contexto
Um time, tráfego baixo, transações que cruzam pedido, estoque e pagamento.

## Decisão
Manter um único deploy e impor fronteiras entre apps com `import-linter` (apps em hierarquia, sem ciclos; serviços sem DRF/Channels).

## Alternativas
Microsserviços: rejeitado. Perde a transação única, multiplica a operação e as falhas de rede (medido: a chamada HTTP local custou ~10 mil vezes uma chamada de função), sem time ou escala que o justifique.

## Consequências
+ Deploy e depuração simples. − A disciplina de fronteiras depende do CI.
`payments` é o primeiro candidato a extração (porta e eventos já existem).

## Gatilhos para rever
Times independentes, escala desigual medida, ciclos de deploy conflitantes.
