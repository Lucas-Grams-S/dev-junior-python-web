# Cheatsheet — FastAPI, Pydantic, SQLAlchemy e Alembic (módulo 15)

```bash
uv add fastapi uvicorn "sqlalchemy[asyncio]" alembic pydantic-settings asyncpg aiosqlite
uv add --dev pytest pytest-asyncio httpx
uv run uvicorn app.main:app --reload --port 8815          # /docs e /redoc
uv run alembic init -t async migrations
uv run alembic revision --autogenerate -m "mensagem" --rev-id 0002   # LEIA o arquivo gerado
uv run alembic upgrade head | downgrade -1 | check | history | upgrade head --sql
```

```python
# rota: de onde vem cada parâmetro
@app.get("/itens/{item_id}")                       # caminho
async def ler(item_id: int, detalhe: bool = False):  # query
    ...
@app.post("/itens", status_code=201)
async def criar(item: Item): ...                    # corpo (BaseModel)

# Pydantic v2
class In(BaseModel):
    model_config = ConfigDict(extra="forbid")
    preco: Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]
    @field_validator("sku")  @classmethod ...        # um campo
    @model_validator(mode="after") ...               # entre campos
class Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # lê de objetos ORM
    @computed_field @property ...                    # campo calculado

# dependências
async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as s:
        yield s                                      # setup / teardown
Session = Annotated[AsyncSession, Depends(get_session)]
app.dependency_overrides[get_session] = outra        # testes (limpar no fim)

# SQLAlchemy 2
class P(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    peso: Mapped[int | None] = mapped_column(default=None)       # NULL
    category: Mapped[Category] = relationship(lazy="raise")
select(P).join(P.category).options(contains_eager(P.category)).where(...).order_by(...).limit(20).offset(0)
await session.scalars(stmt); await session.commit()
```

```python
# testes
# pyproject: asyncio_mode = "auto"; filterwarnings = ["error"]
async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c: ...
httpx.AsyncClient(transport=httpx.MockTransport(handler))        # serviço externo simulado
await asyncio.gather(*(chamada(x) for x in xs))                  # independentes juntas
```

Regras: `async def` + `await` só com biblioteca async; bloqueante → `def`; **nunca** bloquear dentro de `async def`. Uma `AsyncSession` por requisição/tarefa. `lazy="raise"` e `contains_eager`/`selectinload`. Gere migrações no SGBD de produção e **revise** (renomeação = drop+add; `server_default` por dialeto). `ASGITransport` não roda o `lifespan`. Token vazio no servidor = escrita fechada; `hmac.compare_digest`. O 422 ecoa o `input`. Meça com `falhas=0`.
