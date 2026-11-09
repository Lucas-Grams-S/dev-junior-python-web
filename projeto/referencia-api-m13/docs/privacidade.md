# Inventário de dados pessoais (LGPD)

> Rascunho técnico. Bases legais e prazos precisam ser **confirmados pelo jurídico/encarregado de dados**.

| Dado | Onde | Finalidade | Base legal provável | Retenção | Direitos atendidos |
|---|---|---|---|---|---|
| Usuário, e-mail, nome | `accounts_user` | identificar a conta; confirmação de pedido | execução de contrato | enquanto houver conta; anonimizar a pedido | acesso, portabilidade, anonimização |
| Hash da senha | `accounts_user.password` | autenticar | execução de contrato / segurança | idem; nunca exportado | n/a |
| Pedidos, itens, pagamentos | `orders_*`, `payments_*` | venda e documento fiscal | obrigação legal; contrato | prazos legais (a definir) | acesso, portabilidade (mantidos ao anonimizar) |
| Carrinho | `cart_*` | compra em andamento | execução de contrato | apagado ao anonimizar | acesso |
| IP e usuário em logs de segurança | logs | detectar abuso | legítimo interesse / segurança | curta (definir), acesso restrito | — |
| Tokens JWT | `token_blacklist_*` | sessão | execução de contrato | até expirar; revogados ao anonimizar | — |

Comandos: `manage.py exportar_dados_titular <usuario>` · `manage.py anonimizar_titular <usuario>`.
