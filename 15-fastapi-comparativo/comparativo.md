# Comparativo: Django/DRF × FastAPI × Flask

> Entrega do módulo 15. Resumo de consulta rápida; o raciocínio e as medições estão na [aula 06](06-comparativo-quando-escolher.md). Django/DRF e FastAPI foram **implementados e executados** (catálogo do MiniShop); sobre Flask só rodei um exemplo mínimo. Medições de 2026-11-09, máquina local, 1 processo, PostgreSQL 18.6.

## Tabela por dimensão
| Dimensão | Django + DRF | FastAPI | Flask |
|---|---|---|---|
| Filosofia | baterias incluídas | focado em API; você escolhe o resto | micro |
| Tipagem | opcional | central (anotações guiam tudo) | opcional |
| Validação | serializers | Pydantic | manual/extensões |
| Erro de validação | `400`, `{campo: [msgs]}`, pt-br | `422`, lista `loc/type/msg`, inglês | o que você definir |
| Async | parcial | nativo | limitado |
| Injeção de dependências | não há | `Depends` | não há |
| ORM | Django ORM | à escolha (SQLAlchemy) | à escolha |
| Migrações | integradas | Alembic | Alembic |
| Admin | sim | não | extensões |
| Autenticação | sessão/permissões prontas | blocos; lógica sua | extensões |
| Documentação da API | `drf-spectacular` | de fábrica | extensões |
| Testes | `APIClient` | `httpx` + `dependency_overrides` | `test_client()` |
| Segurança de fábrica | CSRF, headers, sessões, senhas | você configura | você configura |
| Convenções | fortes | fracas | quase nenhuma |

## Diferenças reais medidas no catálogo (13 iguais, 3 diferentes em 16 consultas)
| Consulta | DRF | FastAPI (este serviço) |
|---|---|---|
| `?page=99` (fora do intervalo) | `404` "Página inválida" | `200`, lista vazia |
| `?page=0` | `404` | `422` |
| `?ordering=password` (não permitido) | `200`, ignora em silêncio | `400`, informa a lista permitida |
| corpo inválido | `400` agrupado por campo, pt-br | `422` lista plana, inglês, ecoa `input` |

## Desempenho (listagem, 5 rodadas × 600 requisições, mediana)
| Concorrência | Django (ASGI) | FastAPI |
|---|---|---|
| 1 | 330 req/s | 312 req/s |
| 20 | 469 req/s | 470 req/s |

Empate prático (±10% entre rodadas). Onde o async aparece: 20 requisições de 0,5 s de espera em 0,53 s (`await`) contra 10,02 s (chamada bloqueante dentro de `async def`).

## Quando escolher
| Cenário | Provável escolha |
|---|---|
| Loja completa, painel, usuários, regras | Django |
| API com muita E/S concorrente (chamadas externas, streaming, IA) | FastAPI |
| Microsserviço pequeno, webhook, protótipo | FastAPI ou Flask |
| Time Django, API CRUD para app | Django + DRF |
| Reescrever Django por "velocidade" sem gargalo medido | não migrar |

## Seus cenários (preencha na aula 06)
| Cenário | Escolha | Critério decisivo |
|---|---|---|
| 1. | | |
| 2. | | |
| 3. | | |
