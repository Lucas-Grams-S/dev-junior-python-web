"""Pegadinhas clássicas de entrevista de Python: cada bloco imprime o resultado REAL (aula 16.03)."""

import asyncio
import sys


def default_mutavel():
    def add(x, lista=[]):
        lista.append(x)
        return lista

    print("1) default mutável:", add(1), add(2), add(3, []))


def closure_tardia():
    fs = [lambda: i for i in range(3)]
    ok = [lambda i=i: i for i in range(3)]
    print("2) closure tardia:", [f() for f in fs], "| corrigido:", [f() for f in ok])


def is_vs_igual():
    xs, ys = [1], [1]
    print(
        "3) is x ==:",
        xs == ys,
        xs is ys,
        "| None:",
        None is None,
    )


def copia_rasa():
    import copy

    m = [[1, 2], [3]]
    r = m.copy()
    d = copy.deepcopy(m)
    m[0].append(99)
    print("4) cópia rasa:", r, "| profunda:", d)


def float_dinheiro():
    from decimal import Decimal

    print("5) float:", 0.1 + 0.2, 0.1 + 0.2 == 0.3, "| Decimal:", Decimal("0.1") + Decimal("0.2") == Decimal("0.3"))


def gerador_esgota():
    g = (x * x for x in range(3))
    print("6) gerador:", list(g), list(g))


def dict_ordem_e_chave():
    d = {}
    d[1] = "a"
    d[1.0] = "b"
    d[True] = "c"
    print("7) chaves 1, 1.0, True colapsam:", d)


def mutar_enquanto_itera():
    xs = [2, 4, 6, 1, 3, 8]
    for x in xs:
        if x % 2 == 0:
            xs.remove(x)
    print("8) remover iterando:", xs, "| certo:", [x for x in [2, 4, 6, 1, 3, 8] if x % 2])


def args_kwargs():
    def f(a, /, b, *, c):
        return a, b, c

    try:
        f(1, 2, 3)
    except TypeError as e:
        print("9) posicional/keyword:", f(1, b=2, c=3), "| erro:", e)


def escopo():
    x = 10

    def f():
        try:
            x += 1
        except UnboundLocalError as e:
            return type(e).__name__

    print("10) escopo:", f())


async def _await_esquecido():
    async def dado():
        return 42

    c = dado()
    print("11) sem await:", type(c).__name__, "| com await:", await dado())
    c.close()


def finally_return():
    def f():
        try:
            return "try"
        finally:
            print("   (finally executa antes de devolver)")

    print("12) finally:", f())


def tamanhos():
    print("13) memória:", sys.getsizeof([]), sys.getsizeof([0] * 1000), "bytes; tupla vazia:", sys.getsizeof(()))


if __name__ == "__main__":
    for fn in (
        default_mutavel,
        closure_tardia,
        is_vs_igual,
        copia_rasa,
        float_dinheiro,
        gerador_esgota,
        dict_ordem_e_chave,
        mutar_enquanto_itera,
        args_kwargs,
        escopo,
        finally_return,
        tamanhos,
    ):
        fn()
    asyncio.run(_await_esquecido())
