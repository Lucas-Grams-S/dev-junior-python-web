# 4. TDD (introdução)

> ⏱️ ~1h30 · Módulo 10 · Pré-requisitos: [10.01](01-piramide-fixtures.md), [10.02](02-parametrize-mocks.md), [10.03](03-integracao-api-cobertura.md), [8.03 (KISS e YAGNI)](../08-arquitetura/03-solid-dry-kiss-yagni.md)

> ✅ **Verificação.** Tudo executado em 2026-11-08 no laboratório do MiniShop (Python 3.13, pytest 9). **As saídas são reais**: a sessão de TDD abaixo foi **reproduzida passo a passo** por um script que escreve cada teste, roda (vermelho), escreve o código mínimo e roda de novo (verde). O recurso desenvolvido é **novo** (cupons de desconto), não um exemplo de livro.

## 🎯 Objetivos
- Explicar o ciclo **vermelho → verde → refatorar** e o que cada fase protege
- Conduzir uma sessão de **TDD** para uma regra de negócio, em passos pequenos, com **triangulação** e **fronteiras**
- Perceber como TDD **pressiona o design** (código puro, dependências injetadas)
- Usar a rede de testes para **refatorar sem medo** e validar a rede por **mutação**
- Saber **quando** o TDD ajuda muito e quando é melhor outra abordagem

## 🤔 Por que isso importa
Escrever o teste **antes** muda o jeito de pensar: você define *o que* o código deve fazer antes de decidir *como*. O resultado costuma ser código mais simples, mais fácil de testar e com menos funcionalidades desnecessárias. Em equipes, TDD é tema de entrevista ("você pratica TDD? para quê?"), e a resposta madura é um "depende, e aqui está quando eu uso", com um exemplo concreto. Esta aula dá o exemplo.

## 💡 Intuição (explicação simples)
É **escalar com corda**: antes de dar o próximo passo, você crava um **grampo** (o teste) na parede. Se escorregar, cai só até o último grampo, não até o chão. Cada ciclo é um passo curto e travado: **vermelho** (o grampo novo ainda não segura nada: o teste falha), **verde** (você sobe até ele: o código mínimo que o satisfaz) e **refatorar** (arruma o equipamento com a segurança dos grampos já cravados).

## 🔬 Como funciona por dentro
- **O ciclo (Kent Beck):**
  1. 🔴 **Vermelho:** escreva **um** teste pequeno que descreve o próximo comportamento. Rode e **veja falhar**, pelo motivo certo (se ele já passa, não testa nada novo).
  2. 🟢 **Verde:** escreva o **mínimo** de código para passar. Vale até "fingir" (devolver uma constante). Não generalize ainda.
  3. 🔵 **Refatorar:** com tudo verde, melhore a estrutura (nomes, duplicação, `if` em tabela) **sem mudar o comportamento**. Os testes dizem se você errou.
- **Triangulação:** um único exemplo permite uma resposta "fingida" (`return 20.00`). Um **segundo caso com outros valores** obriga a escrever a fórmula de verdade. Dois ou três casos bem escolhidos substituem especulação.
- **Fronteiras primeiro:** a maioria dos bugs mora na borda (`>` ou `>=`, exatamente o mínimo, o último dia de validade, meio centavo). Um bom teste de TDD **nomeia** a fronteira.
- **Passos pequenos:** se um passo exigir muita coisa para passar, o teste era grande demais; divida. Se o vermelho for por um erro de digitação (e não pelo comportamento que falta), conserte o teste primeiro.
- **TDD pressiona o design:** para testar sem esforço, o código precisa ser **simples de chamar**, sem relógio escondido (`datetime.now()`), sem banco, sem estado global. Por isso a função recebe `hoje` por parâmetro e é **pura** (aula 8.01).
- **Rede de segurança:** o conjunto de testes acumulado é o que torna a refatoração barata. Para saber se a rede é boa, **estrague o código de propósito** (mutação) e veja se algum teste falha.
- **Testes de exemplo × de propriedade:** exemplos fixam casos concretos; uma **propriedade** diz algo que vale para *qualquer* entrada válida (por exemplo, "o desconto nunca é negativo nem passa do subtotal") e é testada com muitas entradas geradas (bibliotecas como `hypothesis` fazem isso de forma inteligente).
- **Quando ajuda muito:** regras de negócio bem definidas (preço, desconto, prazos, validações), correção de bugs (escreva o teste que o reproduz **antes** de corrigir), código com muitas fronteiras. **Quando ajuda menos:** exploração/protótipo (você ainda não sabe o que quer; faça um *spike* descartável e depois escreva os testes), telas e layout, integração com serviço desconhecido (descubra primeiro com um script).
- **Não é religião:** o valor está no *feedback rápido e nos passos pequenos*. Escrever o teste logo depois, em seguida ao código, ainda é muito melhor que nunca.

## 🛠️ Exemplo prático
**A necessidade (novo recurso do MiniShop):** *cupons de desconto*. Regras: percentual ou valor fixo; o desconto nunca passa do subtotal; cupom pode ter validade e valor mínimo; arredondamento correto em centavos. Código **puro**, em `apps/orders/cupons.py`, sem banco e sem relógio global.

**1. A sessão, ciclo a ciclo** (reproduzida pelo script `roda_ciclos.py`; cada teste é *acrescentado* aos anteriores, então o verde de cada ciclo também confirma que nada quebrou):
```text
CICLO 1: percentual
  🔴 VERMELHO: 1 error in 0.07s  ←  E   ModuleNotFoundError: No module named 'apps.orders.cupons'
  🟢 VERDE   : 1 passed in 0.01s
CICLO 2: triangulação (outro percentual)
  🔴 VERMELHO: 1 failed, 1 passed in 0.03s  ←  E       AssertionError: assert Decimal('20.00') == Decimal('12.00')
  🟢 VERDE   : 2 passed in 0.01s
CICLO 3: valor fixo
  🔴 VERMELHO: 1 failed, 2 passed in 0.03s  ←  E       AssertionError: assert Decimal('50.00') == Decimal('25.00')
  🟢 VERDE   : 3 passed in 0.01s
CICLO 4: desconto não passa do subtotal
  🔴 VERMELHO: 1 failed, 3 passed in 0.03s  ←  E       AssertionError: assert Decimal('500.00') == Decimal('120.00')
  🟢 VERDE   : 4 passed in 0.01s
CICLO 5: validade (injetando a data)
  🔴 VERMELHO: 1 error in 0.07s  ←  E   ImportError: cannot import name 'CupomInvalido' from 'apps.orders.cupons' (/tmp/claude-1000/-home-lucas-docs-dev-jun
  🟢 VERDE   : 6 passed in 0.01s
CICLO 6: valor mínimo e arredondamento
  🔴 VERMELHO: 3 failed, 6 passed in 0.04s  ←  E       TypeError: Cupom.__init__() got an unexpected keyword argument 'minimo'
  🟢 VERDE   : 9 passed in 0.02s
```
Os seis ciclos, com o que cada um ensina:

**Ciclo 1: o primeiro teste (🔴 por inexistência).** O teste existe antes do módulo, então falha com `ModuleNotFoundError`: é o vermelho mais honesto possível.
```python
from decimal import Decimal

from apps.orders.cupons import Cupom, calcular_desconto


def test_cupom_percentual_de_10_sobre_200_da_20():
    assert calcular_desconto(Cupom(tipo="percentual", valor=Decimal("10")), Decimal("200")) == Decimal("20.00")
```
O código mínimo para o verde? **Fingir.**
```python
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Cupom:
    tipo: str
    valor: Decimal


def calcular_desconto(cupom, subtotal):
    return Decimal("20.00")          # "fingir até conseguir": o mínimo que deixa o teste verde
```
Constante `20.00`: escandaloso e, justamente por isso, o teste seguinte é obrigado a existir.

**Ciclo 2: triangulação.** Outro percentual e outro subtotal (`15%` de `80` = `12,00`). O vermelho mostra a "mentira": `assert Decimal('20.00') == Decimal('12.00')`. Agora a fórmula de verdade: `subtotal * valor / 100`, com `quantize` para 2 casas.

**Ciclo 3: valor fixo.** O vermelho prova que o código antigo trata tudo como percentual (`50.00` em vez de `25.00`). Entra a ramificação por tipo.

**Ciclo 4: o desconto nunca passa do subtotal.** Um cupom fixo de R$ 500 sobre R$ 120: o código devolvia `500.00`. Entra `min(desconto, subtotal)`. Esta é uma **regra de negócio** que ninguém pediria explicitamente e que um comprador esperto descobriria sozinho.

**Ciclo 5: validade, e o relógio vira parâmetro.** O teste quer dizer "o cupom venceu ontem". Se a função chamasse `date.today()`, o teste dependeria do dia em que roda. O **teste obriga o design**: `calcular_desconto(cupom, subtotal, hoje=...)`. Dois testes, a fronteira incluída: **vencido** (`hoje > valido_ate`) e **no último dia ainda vale**. O vermelho aqui foi um `ImportError: cannot import name 'CupomInvalido'`, ou seja, o teste já *especificou* a exceção que o módulo ainda não tinha.

**Ciclo 6: mínimo e arredondamento.** Três testes de uma vez (99,99 recusa, 100,00 vale, meio centavo): `3 failed, 6 passed`. O de arredondamento é o mais traiçoeiro: o `quantize` padrão do `Decimal` usa o arredondamento "do banqueiro" (`0,025` → `0,02`), que não é o que um cliente espera (`0,03`). Validei que o teste **de fato força** `ROUND_HALF_UP`: removi o argumento de propósito e o teste falhou (`test_arredonda_meio_centavo_para_cima`).

**2. Ciclo 7 e refatoração.** Um tipo de cupom inexistente (`"misterioso"`) deveria dar erro claro; o código fazia de conta que era percentual. Vermelho:
```text
E       Failed: DID NOT RAISE CupomInvalido
1 failed, 9 passed in 0.05s
10 passed in 0.02s
```
Com tudo verde, vem o **🔵 refatorar**: o `if tipo == "fixo" ... else ...` vira uma **tabela de funções** (a mesma ideia da aula 8.03, "tipo novo = uma linha"). O resultado final:
```python
"""Regras de desconto de cupons: código PURO (sem banco, sem relógio global), desenvolvido com TDD (aula 10.04)."""
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

CENTAVO = Decimal("0.01")


class CupomInvalido(Exception):
    pass


@dataclass(frozen=True)
class Cupom:
    tipo: str                                  # "percentual" | "fixo"
    valor: Decimal
    valido_ate: date | None = None
    minimo: Decimal = Decimal("0")


# Cada tipo é uma função (cupom, subtotal) -> desconto bruto. Tipo novo = uma linha aqui (e um teste).
TIPOS = {
    "percentual": lambda cupom, subtotal: subtotal * cupom.valor / 100,
    "fixo": lambda cupom, subtotal: cupom.valor,
}


def calcular_desconto(cupom: Cupom, subtotal: Decimal, hoje: date | None = None) -> Decimal:
    """Desconto em reais (2 casas, meio centavo para cima), nunca maior que o subtotal. `hoje` é injetado para testar a validade."""
    if cupom.tipo not in TIPOS:
        raise CupomInvalido(f"tipo de cupom desconhecido: {cupom.tipo!r}")
    if cupom.valido_ate is not None and hoje > cupom.valido_ate:
        raise CupomInvalido(f"O cupom venceu em {cupom.valido_ate:%d/%m/%Y}.")
    if subtotal < cupom.minimo:
        raise CupomInvalido(f"Pedido mínimo de R$ {cupom.minimo} para este cupom.")
    bruto = TIPOS[cupom.tipo](cupom, subtotal)
    return min(bruto, subtotal).quantize(CENTAVO, rounding=ROUND_HALF_UP)
```
E os testes finais (agrupados, com `parametrize` e a propriedade):
```python
"""Regras de cupom desenvolvidas com TDD (aula 10.04): cada teste nasceu ANTES do código que o satisfaz."""
import random
from datetime import date
from decimal import Decimal

import pytest

from apps.orders.cupons import Cupom, CupomInvalido, calcular_desconto

D = Decimal


# ciclo 1 e 2 (triangulação: dois casos obrigam a escrever a fórmula de verdade, não um valor fixo)
@pytest.mark.parametrize("percentual,subtotal,esperado", [("10", "200", "20.00"), ("15", "80", "12.00")], ids=["10pct-de-200", "15pct-de-80"])
def test_cupom_percentual(percentual, subtotal, esperado):
    assert calcular_desconto(Cupom(tipo="percentual", valor=D(percentual)), D(subtotal)) == D(esperado)


# ciclo 3
def test_cupom_de_valor_fixo():
    assert calcular_desconto(Cupom(tipo="fixo", valor=D("25")), D("200")) == D("25.00")


# ciclo 4
def test_desconto_nunca_passa_do_subtotal():
    assert calcular_desconto(Cupom(tipo="fixo", valor=D("500")), D("120")) == D("120.00")


# ciclo 5: o relógio é INJETADO (`hoje`), nada de datetime.now() escondido
def test_cupom_vencido_e_recusado():
    cupom = Cupom(tipo="percentual", valor=D("10"), valido_ate=date(2026, 11, 7))
    with pytest.raises(CupomInvalido, match="venceu"):
        calcular_desconto(cupom, D("200"), hoje=date(2026, 11, 8))


def test_no_ultimo_dia_de_validade_ainda_vale():
    cupom = Cupom(tipo="percentual", valor=D("10"), valido_ate=date(2026, 11, 8))
    assert calcular_desconto(cupom, D("200"), hoje=date(2026, 11, 8)) == D("20.00")


# ciclo 6: fronteira do mínimo (99,99 recusa, 100,00 vale) e arredondamento
def test_subtotal_abaixo_do_minimo_e_recusado():
    cupom = Cupom(tipo="percentual", valor=D("10"), minimo=D("100"))
    with pytest.raises(CupomInvalido, match="mínimo"):
        calcular_desconto(cupom, D("99.99"))


def test_subtotal_exatamente_no_minimo_vale():
    assert calcular_desconto(Cupom(tipo="percentual", valor=D("10"), minimo=D("100")), D("100")) == D("10.00")


def test_arredonda_meio_centavo_para_cima():
    assert calcular_desconto(Cupom(tipo="percentual", valor=D("33.35")), D("10.01")) == D("3.34")
    assert calcular_desconto(Cupom(tipo="percentual", valor=D("50")), D("0.05")) == D("0.03")      # 0,025 -> 0,03 (não 0,02)


# ciclo 7
def test_tipo_de_cupom_desconhecido_e_erro_claro():
    with pytest.raises(CupomInvalido, match="tipo"):
        calcular_desconto(Cupom(tipo="misterioso", valor=D("10")), D("100"))


# propriedade: para QUALQUER entrada válida, 0 <= desconto <= subtotal e o resultado tem 2 casas
def test_propriedade_desconto_entre_zero_e_subtotal():
    sorteio = random.Random(2026)                                  # semente fixa: o teste é determinístico
    for _ in range(500):
        subtotal = D(sorteio.randint(1, 1_000_000)) / 100
        tipo = sorteio.choice(["percentual", "fixo"])
        valor = D(sorteio.randint(0, 20_000)) / 100
        desconto = calcular_desconto(Cupom(tipo=tipo, valor=valor), subtotal)
        assert D("0") <= desconto <= subtotal
        assert desconto == desconto.quantize(D("0.01"))
```
```text
11 passed       (100% das linhas e dos ramos de cupons.py)
```
A refatoração foi feita **sem alterar nenhum teste**, e a rede continuou verde: esse é o benefício que a sessão toda comprou.

**3. A rede é boa? Mutação.** Cinco defeitos plantados de propósito, um por vez, cada um com a rede de testes de pé:
```text
vence no último dia (> vira >=)               → FAILED test_no_ultimo_dia_de_validade_ainda_vale 1 failed, 10 passed in 0.05s 
mínimo exclusivo (< vira <=)                  → FAILED test_subtotal_exatamente_no_minimo_vale 1 failed, 10 passed in 0.06s 
min vira max                                   → FAILED test_cupom_percentual[10pct-de-200] FAILED test_cupom_percentual[15pct-de-80] FAILED test_cupom_de_valor_fixo FAILED test_desconto_nunca_passa_do_subtotal FAILED test_no_ultimo_dia_de_validade_ainda_vale FAILED test_subtotal_exatamente_no_minimo_vale FAILED test_arredonda_meio_centavo_para_cima FAILED test_propriedade_desconto_entre_zero_e_subtotal 8 failed, 3 passed in 0.06s 
percentual divide por 10 em vez de 100         → FAILED test_cupom_percentual[10pct-de-200] FAILED test_cupom_percentual[15pct-de-80] FAILED test_no_ultimo_dia_de_validade_ainda_vale FAILED test_subtotal_exatamente_no_minimo_vale FAILED test_arredonda_meio_centavo_para_cima 5 failed, 6 passed in 0.06s 
arredondamento vira ROUND_DOWN                 → FAILED test_arredonda_meio_centavo_para_cima 1 failed, 10 passed in 0.05s 
```
Os 5 foram **mortos**, e cada um pelo teste que o ciclo correspondente criou: a fronteira da validade morreu no teste do "último dia", a do mínimo no "exatamente o mínimo", o `/10` no teste de percentual, o `ROUND_DOWN` no de arredondamento. Isso mostra que **as fronteiras escolhidas nos ciclos importavam**.
> 🔎 **Uma armadilha do próprio experimento.** Na primeira rodada, o mutante 2 (`<` virar `<=`) parecia ser pego pelo teste **errado** (o da validade). Era mentira: o Python guarda o bytecode compilado (`.pyc`) e o reutiliza se o **tamanho** e a **hora (em segundos)** do arquivo não mudaram; `>=` e `<=` têm o mesmo tamanho e rodei os dois no mesmo segundo, então o segundo mutante executou o código do primeiro. Corrigi usando um diretório de cache novo para cada mutante (`PYTHONPYCACHEPREFIX=$(mktemp -d)`). Por precaução, **reexecutei com essa correção os quatro mutantes de mesmo tamanho da aula 8.07**: o resultado se confirmou (o original passa, os 4 falham). Lição: *ao fazer mutação manual, desligue o cache de bytecode.* Ferramentas como `mutmut` já cuidam disso.

**4. O que aconteceu com a pirâmide?** Os 11 testes de cupons são todos de **unidade** (sem banco, sem relógio, sem rede). Somados aos 6 de unidade da aula 02 (os 3 do `test_mocks_vs_fakes` e os 3 de armadilhas de mock que não tocam o banco), a base da pirâmide da aula 01 passou de 44 para **61 testes** (`pytest -m unidade`), rodando em ~1 s. Esse é o efeito colateral mais valioso do TDD sobre regras de negócio.

**5. De onde vem o próximo passo?** A integração com o `create_order` (aplicar o cupom ao carrinho, guardar qual cupom foi usado) vem **depois**, também guiada por um teste que falha primeiro, e usa o `calcular_desconto` como peça pronta e já protegida. A parte "banco" (modelo `Cupom`, uso máximo por cliente) é um exercício.

**6. Estado final**
```text
291 passed, 1 skipped, 1 xfailed
```

## 🧠 Pausa para lógica
**Problema (um *kata* clássico, em TDD).** Escreva `fretes(subtotal)` seguindo o ciclo: frete grátis a partir de R$ 200,00; entre R$ 100,00 e R$ 199,99, frete de R$ 9,90; abaixo de R$ 100,00, frete de R$ 19,90. Liste, **na ordem**, os testes que você escreveria, e diga qual implementação "fingida" cada vermelho permite.

<details><summary>Dica</summary>Comece pelo caso mais simples e deixe as fronteiras (99,99 / 100,00 / 199,99 / 200,00) para cada ciclo.</details>

<details><summary>Solução comentada</summary>

1. `fretes(50) == 19.90` → fingir: `return 19.90`. 2. `fretes(250) == 0` → obriga um `if`. 3. `fretes(150) == 9.90` → obriga o terceiro caso. 4. Fronteiras, uma por ciclo: `fretes(99.99) == 19.90`, `fretes(100) == 9.90`, `fretes(199.99) == 9.90`, `fretes(200) == 0`; cada uma pega um `<` no lugar de `<=`. 5. Refatorar: as faixas viram uma lista ordenada `[(200, 0), (100, 9.90), (0, 19.90)]` percorrida em ordem, e os testes continuam verdes. 6. Valores monetários em `Decimal`, não `float` (`19.90` em `float` já é um número aproximado).
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| Teste nunca fica vermelho | Passa por acaso ou não testa nada novo | Veja falhar antes de escrever o código |
| Vermelho por motivo errado (erro de digitação no teste) | Pressa | Leia a mensagem; o vermelho tem que ser pelo comportamento que falta |
| Escrever um código enorme para passar um teste | Passo grande demais | Divida o teste; fingir é permitido |
| Generalizar cedo | Antecipar necessidades (YAGNI) | O teste seguinte força a generalização |
| Pular o refatorar | "Já está verde" | Refatore a cada ciclo, com a rede de pé |
| Testes que dependem do relógio ou do banco | Design acoplado | Injetar `hoje`; extrair lógica pura |
| Só testar o "caminho feliz" | Sem fronteiras | Um ciclo por fronteira e por erro |
| TDD em protótipo desconhecido | Ainda não sabe o que quer | *Spike* descartável, depois testes |
| Mudar teste e código juntos para "ficar verde" | Perder a rede | Teste só muda por mudança de requisito |
| Mutação manual com resultado trocado | Bytecode `.pyc` reaproveitado | `PYTHONPYCACHEPREFIX` novo (ou `-B` + limpar) a cada mutante |
| Confiar só em exemplos | Pontos cegos | Acrescentar propriedades (aleatórias com semente fixa ou `hypothesis`) |

- **Passos pequenos, feedback rápido.** O poder do TDD está nos ciclos curtos.
- **O teste é a especificação executável.** Nomeie pelo comportamento.
- **Bug novo? Teste primeiro.** Reproduza, veja vermelho, corrija, veja verde.

## 🧩 Exercícios
**1. Fixação.** (a) Quais são as três fases do ciclo e o que cada uma exige? (b) O que é triangulação e por que "fingir" é aceitável? (c) Por que o teste de validade levou a passar `hoje` por parâmetro? (d) Quando o TDD ajuda menos?

<details><summary>Solução</summary>

(a) Vermelho: escrever um teste pequeno e vê-lo falhar pelo motivo certo; verde: o mínimo para passar; refatorar: melhorar a estrutura com tudo verde, sem mudar o comportamento. (b) Usar um segundo caso com outros valores para forçar a generalização; fingir é aceitável porque o próximo teste vai expor a mentira, e isso evita escrever código sem necessidade. (c) Porque `date.today()` escondido tornaria o resultado dependente do dia; testar com datas fixas exige receber a data. (d) Em protótipos/exploração, interface visual e integrações ainda desconhecidas.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] `apps/orders/cupons.py` desenvolvido em **ciclos pequenos**, com o registro (o seu próprio `roda_ciclos` ou o histórico de commits `test:` → `feat:` → `refactor:`)
- [ ] Pelo menos **uma triangulação**, **duas fronteiras** e **um erro** de negócio com teste
- [ ] A data injetada (nenhum `date.today()` dentro da regra)
- [ ] Um teste de **propriedade** (aleatório com semente fixa ou `hypothesis`)
- [ ] **Cinco mutantes** matados, com o cache de bytecode neutralizado, e a tabela no README
- [ ] Integrar ao `create_order` **guiado por testes** (o pedido guarda o valor do desconto e o código do cupom)
- [ ] Corrigir **um bug** com TDD (teste que reproduz primeiro) e registrar no commit
- [ ] Commits no ritmo `test: ...` → `feat: ...` → `refactor: ...`

**3. Desafio (opcional).** Acrescente um **uso máximo por cliente** (`max_usos`) e um cupom **cumulativo** (`pode_combinar`) seguindo o ciclo. Escreva o teste de propriedade com `hypothesis` (`@given`) e veja que valores extremos ele encontra.

## 🎤 Na entrevista
- **O que é TDD?** Desenvolver em ciclos curtos: escrever um teste que falha, escrever o mínimo de código para passar e refatorar com a rede de testes verde.
- **Quais os benefícios?** Código mais simples e testável, menos funcionalidades desnecessárias, rede de segurança para refatorar e especificação executável.
- **Você pratica TDD sempre?** Uso mais em regras de negócio e correção de bugs; em protótipos faço um *spike* e escrevo os testes depois; o importante é o feedback rápido e os passos pequenos.
- **Como corrigir um bug com TDD?** Escrever primeiro o teste que o reproduz (vermelho), corrigir (verde), refatorar, e deixar o teste como proteção contra a volta.
- **O que é triangulação?** Usar um segundo exemplo com valores diferentes para forçar a implementação real em vez de uma resposta fixa.
- **TDD substitui testes depois?** Não: complementa; testes de integração e de ponta a ponta continuam necessários (pirâmide).

## 📚 Para ir além
- 📄 Artigo: [Martin Fowler — Test-Driven Development](https://martinfowler.com/bliki/TestDrivenDevelopment.html). O ciclo e seus benefícios (em inglês).
- 📚 Livro: *Test-Driven Development: By Example*, de Kent Beck (em inglês). A referência original, com a técnica de "fingir" e triangular.
- 📄 Artigo: [TestDriven.io — Modern TDD](https://testdriven.io/blog/modern-tdd/). TDD pragmático em Python (em inglês).
- 📄 Documentação oficial: [`decimal`](https://docs.python.org/3/library/decimal.html). Modos de arredondamento (`ROUND_HALF_UP`) e dinheiro.
- 📄 Documentação oficial: [pytest — asserções](https://docs.pytest.org/en/stable/how-to/assert.html). `pytest.raises` e comparação de valores.
- 🧰 Biblioteca: [Hypothesis](https://hypothesis.readthedocs.io/en/latest/). Testes baseados em propriedades (em inglês).

## ✅ Checklist da aula
- [ ] Conduzi uma sessão de TDD com ciclos curtos, vendo cada vermelho antes do verde
- [ ] Usei triangulação e testei as fronteiras
- [ ] Deixei o teste guiar o design (data injetada, função pura)
- [ ] Refatorei com a rede de testes de pé
- [ ] Validei a rede com mutantes e neutralizei o cache de bytecode
