import pytest

from entrevista.logica import (
    LRU,
    LimitadorJanela,
    achatar,
    agrupar_anagramas,
    busca_primeira_ocorrencia,
    duas_somas,
    maior_substring_sem_repetir,
    mais_frequentes,
    mesclar_intervalos,
    parenteses_validos,
)


@pytest.mark.parametrize(
    ("nums", "alvo", "esperado"), [([2, 7, 11, 15], 9, (0, 1)), ([3, 3], 6, (0, 1)), ([1, 2], 10, None), ([], 0, None)]
)
def test_duas_somas(nums, alvo, esperado):
    assert duas_somas(nums, alvo) == esperado


@pytest.mark.parametrize(
    ("s", "ok"),
    [("", True), ("()[]{}", True), ("([{}])", True), ("(]", False), ("((", False), ("))", False), ("a(b)c", True)],
)
def test_parenteses(s, ok):
    assert parenteses_validos(s) is ok


def test_anagramas():
    g = agrupar_anagramas(["listen", "silent", "enlist", "google", "gogole", "cat"])
    assert sorted(map(sorted, g)) == [["cat"], ["enlist", "listen", "silent"], ["gogole", "google"]]


@pytest.mark.parametrize(("s", "n"), [("abcabcbb", 3), ("bbbbb", 1), ("pwwkew", 3), ("", 0), ("abba", 2)])
def test_substring(s, n):
    assert maior_substring_sem_repetir(s) == n


def test_intervalos():
    assert mesclar_intervalos([(8, 10), (1, 3), (2, 6), (15, 18), (6, 7)]) == [(1, 7), (8, 10), (15, 18)]
    assert mesclar_intervalos([]) == [] and mesclar_intervalos([(1, 4), (4, 5)]) == [(1, 5)]


def test_top_k():
    assert mais_frequentes(list("aabbbc"), 2) == ["b", "a"]
    assert mais_frequentes(list("abab"), 1) == ["a"]  # empate: alfabético


@pytest.mark.parametrize(
    ("xs", "alvo", "i"), [([1, 2, 2, 2, 3], 2, 1), ([1, 2, 3], 4, -1), ([], 1, -1), ([5], 5, 0), ([2, 2, 2], 2, 0)]
)
def test_busca(xs, alvo, i):
    assert busca_primeira_ocorrencia(xs, alvo) == i


def test_achatar():
    assert achatar([1, [2, [3, [4]], 5], [], [[6]]]) == [1, 2, 3, 4, 5, 6]
    fundo = [1]
    for _ in range(5000):  # 5 000 níveis: recursão estouraria; a pilha explícita não
        fundo = [fundo]
    assert achatar(fundo) == [1]


def test_lru():
    c = LRU(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1
    c.put("c", 3)  # remove "b" (o menos recente)
    assert c.get("b") is None and c.get("a") == 1 and c.get("c") == 3
    with pytest.raises(ValueError):
        LRU(0)


def test_limitador():
    t = [0.0]
    lim = LimitadorJanela(3, 10, lambda: t[0])
    assert [lim.permitir() for _ in range(4)] == [True, True, True, False]
    t[0] = 9.9
    assert lim.permitir() is False
    t[0] = 10.0  # a primeira saiu da janela
    assert lim.permitir() is True
