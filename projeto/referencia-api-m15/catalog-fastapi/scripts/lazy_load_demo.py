"""O que acontece ao acessar `produto.category` sem carregar antes (o "N+1 silencioso" do Django vira ERRO no async)."""

import asyncio

from sqlalchemy import ForeignKey, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, declarative_base, joinedload, mapped_column, relationship  # noqa: F401


class Base(DeclarativeBase):
    pass


class Cat(Base):
    __tablename__ = "cat"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class Prod(Base):
    __tablename__ = "prod"
    id: Mapped[int] = mapped_column(primary_key=True)
    cat_id: Mapped[int] = mapped_column(ForeignKey("cat.id"))
    cat: Mapped[Cat] = relationship()  # lazy="select" (padrão): carrega sob demanda


async def main() -> None:
    eng = create_async_engine("sqlite+aiosqlite://")
    async with eng.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    S = async_sessionmaker(eng, expire_on_commit=False)
    async with S() as s:
        s.add_all([Cat(id=1, name="Áudio"), Prod(id=1, cat_id=1)])
        await s.commit()
    async with S() as s:
        p = (await s.scalars(select(Prod))).one()
        try:
            print(p.cat.name)  # lazy load = I/O síncrono escondido num atributo
        except Exception as e:  # noqa: BLE001
            print(f"{type(e).__name__}: {str(e)[:120]}...")
    async with S() as s:
        p = (await s.scalars(select(Prod).options(joinedload(Prod.cat)))).one()
        print("com joinedload:", p.cat.name)
    await eng.dispose()


asyncio.run(main())
