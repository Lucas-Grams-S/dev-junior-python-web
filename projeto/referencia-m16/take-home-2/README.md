# Take-home 2 — Reserva de salas (solução de referência, FastAPI + SQLite)

```bash
cd projeto/referencia-m16 && uv sync
RESERVAS_DB=/tmp/reservas.db uv run --directory take-home-2 uvicorn app.main:app   # /docs   (ou: cd take-home-2 && uv run --project .. uvicorn app.main:app)
uv run pytest -q take-home-2                                                         # 13 testes
```

## Decisões
- **Sobreposição:** `existente.inicio < novo.fim AND existente.fim > novo.inicio` (encostar não conflita), testada com 7 casos.
- **Concorrência:** a checagem e o `INSERT` rodam dentro de `BEGIN IMMEDIATE` (um escritor por vez). **Provado:** 20 threads no mesmo horário → exatamente um `201` e 19 `409`; trocando por `BEGIN` comum o teste **falhou em 12 de 15 execuções** (e passou em 3: uma corrida nem sempre se manifesta — por isso um teste que passa uma vez não prova ausência de corrida); com `BEGIN IMMEDIATE` passou nas 15.
- **Fusos:** só aceita `datetime` **com fuso** (`AwareDatetime`); tudo é guardado em UTC; comparar o texto ISO em UTC equivale a comparar instantes (teste com `-03:00`).
- Regras de domínio no modelo Pydantic (`fim > início`, ≤ 4 h); "não no passado" na rota (depende do relógio).

## Limitações (declare no seu README real)
- SQLite: um escritor por vez (suficiente aqui; em PostgreSQL use uma **restrição de exclusão** `EXCLUDE USING gist (sala_id WITH =, tstzrange(inicio, fim) WITH &&)`, não executado).
- `GET /reservas?data=` considera o dia em **UTC**, não no fuso do usuário.
- Sem autenticação: veja a estratégia na aula (sessão/JWT, `responsavel` vindo do token, só o dono cancela). Sem paginação.
- `starlette.testclient` com `httpx` emite `StarletteDeprecationWarning` (sugere `httpx2`); mantive `httpx`, que é o que o curso usa.
