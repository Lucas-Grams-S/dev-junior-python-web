# 05. Lógica no nível de entrevista

> ⏱️ ~1h30 · Módulo 16 · Pré-requisitos: Módulo 1; `recursos/exercicios-logica.md`

## 🎯 Objetivos
Ao final desta aula você consegue:
- Aplicar um roteiro de 6 passos a qualquer problema de lógica
- Escolher a estrutura certa (dicionário, pilha, janela, ordenação, busca binária)
- Dizer a complexidade de tempo e espaço do que escreveu
- Testar casos de borda antes de declarar "pronto"
- Raciocinar em voz alta sem travar

## 🤔 Por que isso importa
Quase todo processo de júnior tem um problema de código ao vivo ou em plataforma. O objetivo **não é decorar**: são ~10 padrões que cobrem a maior parte dos problemas do nível júnior.

## 💡 Intuição (explicação simples)
É como montar um móvel: antes de furar, você lê o manual (entende o problema), separa as peças (estrutura de dados) e testa o encaixe com um exemplo pequeno (caso de borda).

## 🔬 Como funciona por dentro
**Roteiro de 6 passos** (fale cada um):
1. **Reformule** o problema e confirme entradas/saídas.
2. **Exemplos**, incluindo bordas: vazio, um elemento, repetidos, negativos.
3. **Força bruta** primeiro, dita em voz alta, com sua complexidade.
4. **Melhore**: qual estrutura troca tempo por memória?
5. **Codifique** limpo, nomes claros.
6. **Teste** com os exemplos e **analise** O(tempo) e O(espaço).

Padrões e a pista que os denuncia:

| Padrão | Pista no enunciado | Exemplo da aula |
|---|---|---|
| Dicionário/conjunto | "já vi?", "par que soma", contagem | `duas_somas`, `mais_frequentes` |
| Pilha | aninhamento, "desfazer", balanceado | `parenteses_validos`, `achatar` |
| Chave canônica | "agrupar equivalentes" | `agrupar_anagramas` |
| Janela deslizante | "maior trecho contínuo com…" | `maior_substring_sem_repetir`, `LimitadorJanela` |
| Ordenar e varrer | intervalos, "sobreposição" | `mesclar_intervalos` |
| Busca binária | lista ordenada, "primeira posição" | `busca_primeira_ocorrencia` |
| Estrutura auxiliar | "cache", "O(1)" | `LRU` |

## 🛠️ Exemplo prático
Código completo, comentado e testado em [`entrevista/logica.py`](../projeto/referencia-m16/entrevista/logica.py); testes em [`entrevista/test_logica.py`](../projeto/referencia-m16/entrevista/test_logica.py).

```bash
cd projeto/referencia-m16 && uv run pytest entrevista -q
# 27 passed in 0.02s
```
Resultados reais de uma sessão interativa:
```text
duas_somas([2,7,11,15], 9)            -> (0, 1)
parenteses_validos("([{}])") / "(]"   -> True / False
agrupar_anagramas(Roma,amor,gato,toga,mora) -> [['Roma','amor','mora'], ['gato','toga']]
maior_substring_sem_repetir("abcabcbb") -> 3
mesclar_intervalos([(1,3),(2,6),(8,10),(6,7)]) -> [(1, 7), (8, 10)]
mais_frequentes(abracadabra, 2)        -> ['a', 'b']
busca_primeira_ocorrencia([1,2,2,2,3], 2) -> 1
achatar([1,[2,[3,[4]]],5])             -> [1, 2, 3, 4, 5]
LRU(2): put a, put b, get a, put c      -> chaves ['a', 'c']   (b foi expulsa)
LimitadorJanela(2 eventos/10 s), t=0,1,2,10,11 -> [True, True, False, True, True]
```
Destaque: `duas_somas` guarda `valor → índice` e checa o **complemento** antes de inserir (O(n) tempo, O(n) espaço, contra O(n²) da força bruta); `mesclar_intervalos` trata "encostar" como fundir (`(6,7)` com `(1,6)`); o `LimitadorJanela` recebe o **relógio por parâmetro**, o que o torna testável sem `sleep` (mesma técnica do módulo 10).

## 🧠 Pausa para lógica
`mesclar_intervalos([(1,4),(2,3)])` devolve `[(1, 4)]`. Que linha da função garante que o fim não "encolha" para 3?
<details><summary>Solução</summary>

`saida[-1][1] = max(saida[-1][1], b)`: o `max` mantém o maior fim. Sem ele, o resultado seria `(1, 3)`, um bug que só aparece com intervalo **contido** em outro (borda!).
</details>

## ⚠️ Erros comuns e boas práticas
- Codificar antes de entender; ficar em silêncio por minutos (fale suas hipóteses).
- Esquecer bordas: lista vazia, um item, tudo igual, valor negativo.
- Mutar a entrada sem avisar; usar `list.pop(0)` ou `x in lista` em laço (O(n) escondido; use `deque`/`set`).
- Erro real clássico: `IndexError: list index out of range` em busca binária por `hi = len(xs)` em vez de `len(xs) - 1`.
- Otimizar antes de ter uma versão correta.

## 🧩 Exercícios
1. **(Fixação)** Diga a complexidade de `agrupar_anagramas` e por que a chave é `"".join(sorted(p))`.
2. **(Aplicação no MiniShop)** Pegue um problema real do projeto e resolva como lógica pura: "dado o histórico de pedidos, ache os 3 produtos mais vendidos por categoria, desempate por nome".
   - [ ] Função pura com tipos e docstring
   - [ ] Pelo menos 5 testes (vazio, empate, categoria única…)
   - [ ] Complexidade escrita num comentário
3. **(Desafio)** Implemente `LimitadorJanela` com *token bucket* e compare: o que muda no comportamento nas rajadas?

<details><summary>Solução do exercício 1</summary>

O(n·k log k) para n palavras de tamanho k. Anagramas têm as mesmas letras; ordenar as letras produz a **mesma chave** para todos.
</details>

## 🎤 Na entrevista
**"Qual a complexidade do que você escreveu?"** Diga tempo e espaço, e de onde vem cada um. **"Dá para melhorar?"** Cite o *trade-off* (mais memória por menos tempo) ou diga que é suficiente para o tamanho esperado. **"Como testaria?"** Casos normais, bordas, entrada grande, e um teste de propriedade (ex.: o resultado de `mesclar_intervalos` não tem sobreposição).

## 📚 Para ir além
- 📄 [Python — `collections`](https://docs.python.org/pt-br/3/library/collections.html) (HTTP 200 em 2026-11-09)
- 📄 [Python — `bisect`](https://docs.python.org/pt-br/3/library/bisect.html)
- 📑 [Exercícios do curso](../recursos/exercicios-logica.md)
- 🏋️ Prática extra: resolva 1 problema por dia, sempre com os 6 passos, em voz alta e com cronômetro de 30 min.

## ✅ Checklist da aula
- [ ] Refiz 5 das 10 funções sem olhar e passei nos testes
- [ ] Sei dizer o padrão de cada uma
- [ ] Pratiquei falar o raciocínio em voz alta
