# 19. Mini-projeto: CLI de estoque (parte 2)

> ⏱️ ~1h30 · Módulo 1 · Pré-requisitos: [18](18-projeto-cli-estoque-1.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Construir uma interface de linha de comando com subcomandos usando `argparse`
- Importar produtos de CSV em modo gerador, relatando as linhas inválidas
- Mapear exceções de domínio para mensagens e códigos de saída
- Testar a CLI com `capsys` e `main(argv)`
- Fechar o módulo com README, tag Git e documentação de uso

## 🤔 Por que isso importa
Ferramentas de linha de comando (scripts de manutenção, comandos `manage.py` do Django, jobs de importação) são parte do trabalho diário. Saber receber argumentos, falar com o usuário e devolver o código de saída correto é o que torna um script utilizável em automações e no CI.

## 💡 Intuição (explicação simples)
A CLI é o **balcão da loja**: o cliente faz pedidos curtos (“quero repor 5 mouses”), o balcão traduz em chamadas ao atendente (serviço) e devolve uma resposta educada. Se der problema, o balcão não mostra os bastidores (traceback): diz o que houve e **sinaliza com um código** que o sistema entende (0 = tudo certo; ≠ 0 = problema).

## 🔬 Como funciona por dentro
- `argparse` lê `sys.argv` (a lista de palavras digitadas) e monta um objeto com os valores já convertidos e validados. Gera `--help` automaticamente.
- **Subcomandos** (`estoque add`, `estoque list`) são parsers filhos escolhidos pela primeira palavra.
- **Código de saída** (*exit code*): 0 = sucesso, 1 = erro de negócio, 2 = uso incorreto (padrão do `argparse`). Scripts de shell e CI usam isso (`comando && próximo`).
- Funções `main(argv=None)` que **recebem** os argumentos e **devolvem** o código de saída são testáveis sem abrir processo.
- Convenção: mensagens normais em `stdout`, erros em `stderr`.

## 🛠️ Exemplo prático
Esta aula continua o projeto da aula 18 (os arquivos de `minishop_cli/` e `tests/` já existem).

**1. Importação de CSV (gerador da aula 15)**
```python
import csv
from collections.abc import Iterator
from pathlib import Path

from .erros import DadosInvalidos, MiniShopError
from .modelos import Produto


def ler_csv(caminho: str | Path) -> Iterator[tuple[int, Produto | None, str | None]]:
    """Gera (linha, produto, erro). Não carrega o arquivo inteiro."""
    with open(caminho, newline="", encoding="utf-8") as f:
        for n, row in enumerate(csv.DictReader(f), start=2):
            try:
                yield n, Produto(row["sku"], row["nome"], row["preco"], int(row["qtd"])), None
            except (KeyError, ValueError, DadosInvalidos) as e:
                yield n, None, f"{type(e).__name__}: {e}"


def importar(estoque, caminho: str | Path) -> tuple[int, list[tuple[int, str]]]:
    """Adiciona ao estoque. Devolve (quantos importados, [(linha, erro)])."""
    ok, erros = 0, []
    for n, produto, erro in ler_csv(caminho):
        if erro:
            erros.append((n, erro))
            continue
        try:
            estoque.adicionar(produto.sku, produto.nome, produto.preco, produto.qtd)
            ok += 1
        except MiniShopError as e:
            erros.append((n, str(e)))
    return ok, erros
```

**2. A CLI**
```python
import argparse
import os
import sys
from decimal import Decimal

from .erros import MiniShopError
from .importacao import importar
from .repositorio import RepositorioJSON
from .servico import Estoque


def montar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="minishop", description="CLI de estoque do MiniShop")
    p.add_argument("--arquivo", default=os.environ.get("ESTOQUE_ARQUIVO", "estoque.json"),
                   help="arquivo JSON do estoque (padrão: estoque.json ou $ESTOQUE_ARQUIVO)")
    sub = p.add_subparsers(dest="comando", required=True)

    add = sub.add_parser("add", help="cadastra um produto")
    add.add_argument("sku"); add.add_argument("nome")
    add.add_argument("preco"); add.add_argument("--qtd", type=int, default=0)

    for nome, ajuda in (("repor", "entrada de estoque"), ("retirar", "saída de estoque")):
        s = sub.add_parser(nome, help=ajuda)
        s.add_argument("sku"); s.add_argument("qtd", type=int)

    ls = sub.add_parser("listar", help="lista produtos")
    ls.add_argument("--busca", default="")
    ls.add_argument("--ordem", choices=["nome", "preco", "qtd"], default="nome")

    sub.add_parser("relatorio", help="valor total e produtos com pouco estoque").add_argument(
        "--minimo", type=int, default=5)
    sub.add_parser("importar", help="importa produtos de um CSV").add_argument("csv")
    return p


def linha(p) -> str:
    return f"{p.sku:<8} {p.nome:<18} R$ {p.preco:>9.2f} {p.qtd:>5}"


def executar(args, estoque: Estoque) -> None:
    if args.comando == "add":
        p = estoque.adicionar(args.sku, args.nome, args.preco, args.qtd)
        print(f"cadastrado: {p.sku} - {p.nome}")
    elif args.comando == "repor":
        print(f"{args.sku.upper()} agora com {estoque.repor(args.sku, args.qtd).qtd}")
    elif args.comando == "retirar":
        print(f"{args.sku.upper()} agora com {estoque.retirar(args.sku, args.qtd).qtd}")
    elif args.comando == "listar":
        itens = estoque.listar(args.busca, args.ordem)
        if not itens:
            print("Nenhum produto encontrado")
        for p in itens:
            print(linha(p))
    elif args.comando == "relatorio":
        print(f"Produtos: {len(estoque)}  Valor em estoque: R$ {estoque.valor_total():.2f}")
        for p in estoque.abaixo_do_minimo(args.minimo):
            print(f"  ATENÇÃO {p.sku}: apenas {p.qtd}")
    elif args.comando == "importar":
        ok, erros = importar(estoque, args.csv)
        print(f"{ok} importados, {len(erros)} com erro")
        for n, msg in erros:
            print(f"  linha {n}: {msg}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = montar_parser().parse_args(argv)
    try:
        executar(args, Estoque(RepositorioJSON(args.arquivo)))
    except MiniShopError as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    return 0
```
```python
import sys

from .cli import main

sys.exit(main())
```

**3. Usando**
```bash
export ESTOQUE_ARQUIVO=demo.json
python -m minishop_cli add MS-01 Mouse 49.90 --qtd 10
python -m minishop_cli add TC-02 Teclado 120.00 --qtd 4
python -m minishop_cli add CB-03 "Cabo USB" 9.90 --qtd 2
python -m minishop_cli retirar MS-01 3
python -m minishop_cli listar --ordem preco
python -m minishop_cli listar --busca usb
python -m minishop_cli relatorio
```
```text
cadastrado: MS-01 - Mouse
cadastrado: TC-02 - Teclado
cadastrado: CB-03 - Cabo USB
MS-01 agora com 7
CB-03    Cabo USB           R$      9.90     2
MS-01    Mouse              R$     49.90     7
TC-02    Teclado            R$    120.00     4
CB-03    Cabo USB           R$      9.90     2
Produtos: 3  Valor em estoque: R$ 849.10
  ATENÇÃO CB-03: apenas 2
  ATENÇÃO TC-02: apenas 4
```

**4. Erros: mensagem amigável e código de saída**
```bash
export ESTOQUE_ARQUIVO=demo.json
python -m minishop_cli retirar TC-02 99 2>&1; echo "código: $?"
python -m minishop_cli add MS-01 Outro 1 2>&1; echo "código: $?"
python -m minishop_cli retirar ZZ 1 2>&1; echo "código: $?"
python -m minishop_cli repor TC-02 abc 2>&1; echo "código: $?"
python -m minishop_cli --help
```
```text
erro: TC-02: pedido 99, disponível 4
código: 1
erro: SKU MS-01 já existe
código: 1
erro: SKU ZZ não existe
código: 1
usage: minishop repor [-h] sku qtd
minishop repor: error: argument qtd: invalid int value: 'abc'
código: 2
usage: minishop [-h] [--arquivo ARQUIVO]
                {add,repor,retirar,listar,relatorio,importar} ...

CLI de estoque do MiniShop

positional arguments:
  {add,repor,retirar,listar,relatorio,importar}
    add                 cadastra um produto
    repor               entrada de estoque
    retirar             saída de estoque
    listar              lista produtos
    relatorio           valor total e produtos com pouco estoque
    importar            importa produtos de um CSV

options:
  -h, --help            show this help message and exit
  --arquivo ARQUIVO     arquivo JSON do estoque (padrão: estoque.json ou
                        $ESTOQUE_ARQUIVO)
```

**5. Importando um CSV com linhas ruins**
```csv
sku,nome,preco,qtd
LP-10,Laptop,3500.00,2
MS-01,Mouse repetido,50,1
HB-05,Hub USB,abc,3
WC-07,Webcam,199.90,-4
FN-08,Fone,89.90,7
```
```bash
export ESTOQUE_ARQUIVO=demo.json
python -m minishop_cli importar produtos.csv 2>&1; echo "código: $?"
python -m minishop_cli relatorio --minimo 3
```
```text
2 importados, 3 com erro
  linha 3: SKU MS-01 já existe
  linha 4: DadosInvalidos: preço inválido: 'abc'
  linha 5: DadosInvalidos: quantidade deve ser um inteiro >= 0
código: 0
Produtos: 5  Valor em estoque: R$ 8478.40
  ATENÇÃO CB-03: apenas 2
  ATENÇÃO LP-10: apenas 2
```
(Usamos `2>&1` só para ver `stderr` junto da saída; sem ele, no terminal as mensagens de erro aparecem do mesmo jeito, mas você pode separá-las com `2>erros.txt`.)

**6. Testes da CLI**
```python
from minishop_cli.cli import main


def rodar(argv, capsys):
    codigo = main(argv)
    saida = capsys.readouterr()
    return codigo, saida.out, saida.err


def test_fluxo_basico(tmp_path, capsys):
    arq = ["--arquivo", str(tmp_path / "e.json")]
    assert rodar(arq + ["add", "A", "Mouse", "10", "--qtd", "5"], capsys)[0] == 0
    codigo, out, _ = rodar(arq + ["retirar", "A", "2"], capsys)
    assert codigo == 0 and "agora com 3" in out


def test_erro_de_negocio_devolve_codigo_1(tmp_path, capsys):
    arq = ["--arquivo", str(tmp_path / "e.json")]
    rodar(arq + ["add", "A", "Mouse", "10", "--qtd", "1"], capsys)
    codigo, _, err = rodar(arq + ["retirar", "A", "5"], capsys)
    assert codigo == 1 and "disponível 1" in err


def test_importar_csv_com_erros(tmp_path, capsys):
    csv = tmp_path / "p.csv"
    csv.write_text("sku,nome,preco,qtd\nA,Mouse,10,1\nB,Cabo,xx,1\n", encoding="utf-8")
    codigo, out, err = rodar(["--arquivo", str(tmp_path / "e.json"), "importar", str(csv)], capsys)
    assert codigo == 0 and "1 importados, 1 com erro" in out and "linha 3" in err


def test_listar_vazio(tmp_path, capsys):
    _, out, _ = rodar(["--arquivo", str(tmp_path / "e.json"), "listar"], capsys)
    assert "Nenhum produto" in out
```
```bash
python -m pytest -q -p no:cacheprovider
```
```text
......................                                                   [100%]
22 passed in 0.03s
```

## ⚠️ Erros comuns e boas práticas
| Mensagem | Causa | Solução |
|---|---|---|
| `error: the following arguments are required: preco` | Faltou argumento posicional | Veja `--help` do subcomando |
| `error: argument qtd: invalid int value: 'abc'` | `type=int` recusou o valor | Passe um inteiro |
| `error: unrecognized arguments: ...` | Opção digitada errada ou na posição errada (global antes do subcomando) | `--arquivo` vai **antes** do subcomando |
| `Traceback` para o usuário final | Exceção de domínio não tratada | Capture `MiniShopError` na CLI |
| Código de saída sempre 0 | `main` não devolve o código | `sys.exit(main())` |

- Nunca use `input()` em comandos que precisam rodar em automação; receba argumentos.
- Separe `stdout` (resultado) de `stderr` (avisos e erros).
- `main(argv)` testável + `__main__.py` fino = padrão profissional.

## 🧠 Pausa para lógica
**Problema (ranking e alerta).** Estenda `relatorio` com os **3 produtos de maior valor em estoque**. Qual a complexidade usando `sorted` vs `heapq.nlargest`? Para 1 milhão de produtos qual é melhor?

<details><summary>Dica</summary>
<code>sorted</code> ordena tudo: O(n log n). <code>heapq.nlargest(k, itens, key=...)</code> mantém só <code>k</code> candidatos: O(n log k).
</details>

<details><summary>Solução comentada</summary>

```python
import heapq
from decimal import Decimal

itens = [("A", Decimal("10"), 3), ("B", Decimal("99"), 2), ("C", Decimal("5"), 100), ("D", Decimal("40"), 4)]
valor = lambda t: t[1] * t[2]
print([t[0] for t in sorted(itens, key=valor, reverse=True)[:3]])
print([t[0] for t in heapq.nlargest(3, itens, key=valor)])
```
```text
['C', 'B', 'D']
['C', 'B', 'D']
```
Com k = 3 e n = 1.000.000, `nlargest` faz ~1 milhão de comparações simples contra ~20 milhões de `sorted`. Para n pequeno, a diferença é irrelevante e `sorted` é mais legível: meça antes de otimizar.
</details>

**Variação mais difícil:** como o banco de dados faz isso? (Pista: `ORDER BY ... LIMIT 3` com índice.)

## 🧩 Exercícios
**1. Fixação**
Acrescente o subcomando `remover SKU` na CLI (use o `remover` do exercício da aula 18) com um teste.

<details><summary>Solução</summary>

```python
# no montar_parser:
#   sub.add_parser("remover", help="remove produto").add_argument("sku")
# em executar:
#   elif args.comando == "remover":
#       estoque.remover(args.sku); print(f"removido: {args.sku.upper()}")
```
</details>

**2. Aplicação no projeto MiniShop (entrega do módulo)**
Finalize a CLI e publique a versão `v0.1-python-cli`.

Critérios de pronto:
- [ ] `python -m minishop_cli --help` lista todos os subcomandos
- [ ] Todos os erros de negócio terminam com `erro: ...` em `stderr` e código 1
- [ ] `uv run pytest` verde com ≥ 22 testes; `uv run ruff check` sem erros (instale com `uv add --dev ruff`)
- [ ] README com: o que é, como instalar (`uv sync`), exemplos de cada comando e como rodar os testes
- [ ] Arquivo `seed/produtos.csv` com 20 produtos de exemplo e importação funcionando
- [ ] Tag: `git tag v0.1-python-cli && git push --tags`

<details><summary>Solução de referência</summary>

```bash
uv add --dev pytest ruff
uv run ruff check . && uv run pytest -q
uv run python -m minishop_cli --arquivo estoque.json importar seed/produtos.csv
git add -A && git commit -m "feat: finish stock cli with csv import"
git tag v0.1-python-cli && git push --tags
```
Os 20 produtos do seed serão reutilizados no banco SQL (Módulo 3) e nas fixtures do Django (Módulo 5).
</details>

**3. Desafio (opcional)**
Exporte o estoque para CSV (`exportar saida.csv`) e prove o round-trip: exportar, apagar o JSON, importar de volta e comparar o `relatorio`.

## 🎤 Na entrevista
- **O que é código de saída e por que importa?** Número devolvido pelo processo (0 = sucesso). Shells e CI decidem o que fazer com base nele.
- **Por que `main(argv)` em vez de ler `sys.argv` dentro?** Torna a função testável sem subprocesso, passando argumentos diretamente.
- **Como você trata erros em uma CLI?** Captura exceções de domínio, imprime mensagem objetiva em `stderr` e devolve código ≠ 0; reserva tracebacks para bugs inesperados.

## 📚 Para ir além
- 📄 Documentação oficial: [`argparse`](https://docs.python.org/3/library/argparse.html). Referência e tutorial.
- 📄 Documentação oficial: [Tutorial argparse](https://docs.python.org/3/howto/argparse.html). Passo a passo com exemplos.
- 📄 Documentação oficial: [pytest: capturando saída](https://docs.pytest.org/en/stable/how-to/capture-stdout-stderr.html). `capsys` e `capfd`.
- 🏋️ Prática extra: acrescente `--formato json` ao `listar` para uso em scripts.

## ✅ Checklist da aula
- [ ] CLI com subcomandos funcionando
- [ ] Importação de CSV reporta erros por linha
- [ ] Testes de CLI com `capsys`
- [ ] Tag `v0.1-python-cli` criada
