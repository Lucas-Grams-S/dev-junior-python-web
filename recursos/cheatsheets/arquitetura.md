# Cheatsheet: arquitetura, padrões, twelve-factor e legado (módulo 8)

> Aulas 8.01 a 8.07. Tudo foi executado no laboratório [`projeto/referencia-api-m8`](../../projeto/referencia-api-m8/README.md).

## Onde cada coisa mora
| Camada | Faz | Não faz |
|---|---|---|
| interface (`api`, serializers) | HTTP ⇄ caso de uso, valida formato e permissão | regra de negócio, SQL |
| serviços (`services`, `selectors`) | regra, orquestração, transação | conhece `request`, DRF, Channels |
| dados (`models`, `repositories`) | persistência e consultas | regra de negócio |
| domínio (`domain.py`) | regras **puras** (sem I/O) | importar Django |

## Padrões em uma linha
| Padrão | Quando | No MiniShop |
|---|---|---|
| Strategy | 3+ variantes do mesmo comportamento | cupons/pagamento em dicionário de funções |
| Factory | escolher a implementação por configuração | `obter_gateway()` |
| Repository | regras ricas, testes sem banco | `PedidoRepository` (Django e memória) |
| Adapter | integrar terceiro com outro vocabulário | `GatewayFake`, `GatewayAcme` |

## Comandos que usamos
```bash
uv run lint-imports                       # contratos de arquitetura (import-linter)
uv run mypy arquivo.py                    # confere Protocol
uv run radon cc pacote -s -a              # complexidade ciclomática
uv run ruff check --select C901,S608 .    # complexidade e SQL por concatenação
uv run pytest --cov=pacote --cov-branch   # cobertura de ramos
DEBUG=0 SECRET_KEY=... ALLOWED_HOSTS=... uv run python manage.py check --deploy
```

## Twelve-factor: o essencial
- config no **ambiente**; sem `SECRET_KEY` em produção, **não sobe**; `DEBUG` padrão `False`
- `DATABASE_URL`; logs em **stdout**; `SIGTERM` termina o que está em andamento
- rode a suíte **no banco de produção** (sequências, limites do OpenAPI, travas)

## Refatorar legado
1. golden master (100% de ramos) → 2. mutação manual → 3. passos pequenos, rede verde → 4. refatoração e correção em commits **separados** → 5. medir antes/depois

## Armadilhas
- dinheiro em `float`; SQL concatenado; `global`; import circular entre apps
- *fake* sem rollback; padrão sem problema; microsserviços sem motivo medido
