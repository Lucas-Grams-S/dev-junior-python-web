"""Dez problemas de lógica de entrevista júnior, com solução, complexidade e testes (aula 16.05)."""

from collections import Counter, OrderedDict, defaultdict, deque


def duas_somas(nums: list[int], alvo: int) -> tuple[int, int] | None:
    """Índices de dois números que somam `alvo`. O(n) tempo, O(n) espaço (dicionário valor -> índice)."""
    vistos: dict[int, int] = {}
    for i, n in enumerate(nums):
        if alvo - n in vistos:
            return vistos[alvo - n], i
        vistos[n] = i
    return None


def parenteses_validos(s: str) -> bool:
    """([{}]) balanceado? Pilha. O(n)."""
    pares = {")": "(", "]": "[", "}": "{"}
    pilha: list[str] = []
    for c in s:
        if c in "([{":
            pilha.append(c)
        elif c in pares:
            if not pilha or pilha.pop() != pares[c]:
                return False
    return not pilha


def agrupar_anagramas(palavras: list[str]) -> list[list[str]]:
    """Chave = letras ordenadas. O(n·k log k)."""
    grupos: dict[str, list[str]] = defaultdict(list)
    for p in palavras:
        grupos["".join(sorted(p.lower()))].append(p)
    return list(grupos.values())


def maior_substring_sem_repetir(s: str) -> int:
    """Janela deslizante com último índice visto. O(n)."""
    ultimo: dict[str, int] = {}
    inicio = melhor = 0
    for i, c in enumerate(s):
        if c in ultimo and ultimo[c] >= inicio:
            inicio = ultimo[c] + 1
        ultimo[c] = i
        melhor = max(melhor, i - inicio + 1)
    return melhor


def mesclar_intervalos(intervalos: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Ordena e funde sobrepostos (toca na borda = funde). O(n log n)."""
    saida: list[list[int]] = []
    for a, b in sorted(intervalos):
        if saida and a <= saida[-1][1]:
            saida[-1][1] = max(saida[-1][1], b)
        else:
            saida.append([a, b])
    return [(a, b) for a, b in saida]


def mais_frequentes(itens: list[str], k: int) -> list[str]:
    """Top-k por frequência; empate = ordem alfabética (determinístico). O(n log n)."""
    return [x for x, _ in sorted(Counter(itens).items(), key=lambda p: (-p[1], p[0]))[:k]]


def busca_primeira_ocorrencia(xs: list[int], alvo: int) -> int:
    """Busca binária pela PRIMEIRA posição de `alvo` em lista ordenada com repetidos; -1 se não existe. O(log n)."""
    lo, hi, achado = 0, len(xs) - 1, -1
    while lo <= hi:
        meio = (lo + hi) // 2
        if xs[meio] == alvo:
            achado, hi = meio, meio - 1  # continua à esquerda
        elif xs[meio] < alvo:
            lo = meio + 1
        else:
            hi = meio - 1
    return achado


def achatar(x: object) -> list:
    """Achata listas aninhadas (sem recursão profunda: pilha explícita)."""
    saida, pilha = [], [iter([x])]
    while pilha:
        for item in pilha[-1]:
            if isinstance(item, list):
                pilha.append(iter(item))
                break
            saida.append(item)
        else:
            pilha.pop()
    return saida


class LRU:
    """Cache LRU de capacidade fixa: get/put em O(1) com OrderedDict."""

    def __init__(self, capacidade: int):
        if capacidade < 1:
            raise ValueError("capacidade deve ser >= 1")
        self.cap, self.d = capacidade, OrderedDict()

    def get(self, k):
        if k not in self.d:
            return None
        self.d.move_to_end(k)
        return self.d[k]

    def put(self, k, v):
        self.d[k] = v
        self.d.move_to_end(k)
        if len(self.d) > self.cap:
            self.d.popitem(last=False)


class LimitadorJanela:
    """No máximo `limite` eventos em `janela` segundos (janela deslizante). Relógio injetado = testável."""

    def __init__(self, limite: int, janela: float, relogio):
        self.limite, self.janela, self.relogio, self.ts = limite, janela, relogio, deque()

    def permitir(self) -> bool:
        agora = self.relogio()
        while self.ts and self.ts[0] <= agora - self.janela:
            self.ts.popleft()
        if len(self.ts) >= self.limite:
            return False
        self.ts.append(agora)
        return True
