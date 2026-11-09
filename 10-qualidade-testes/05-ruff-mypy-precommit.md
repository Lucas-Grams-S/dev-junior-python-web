# 5. `ruff`, `mypy` e `pre-commit`

> ⏱️ ~1h30 · Módulo 10 · Pré-requisitos: [10.01](01-piramide-fixtures.md), [10.04](04-tdd.md), [8.03 (complexidade)](../08-arquitetura/03-solid-dry-kiss-yagni.md), [9.06 (segredos)](../09-seguranca/06-segredos-dependencias-headers-rate-limit.md)

> ✅ **Verificação.** Tudo executado em 2026-11-08 no laboratório do MiniShop (Python 3.13, `ruff` 0.17.4, `mypy` 2.4, `django-stubs` 6.1, `pre-commit`, Git). **As saídas são reais.** Para mostrar commits de verdade, o laboratório passou a ser um **repositório Git de trabalho** (local, só para a aula), e cada passo abaixo é um commit seu. A suíte terminou em **292 passed, 1 skipped, 1 xfailed**.

## 🎯 Objetivos
- Configurar o **`ruff`** como linter e formatador, escolhendo regras com critério e justificando as exceções
- Introduzir um formatador num código existente **sem misturar** com mudanças de comportamento, e **provar** que não mudou o programa
- Adotar o **`mypy`** de forma **gradual**: permissivo no geral, rígido nos módulos puros
- Montar o **`pre-commit`** para barrar erros *antes* do commit, e saber suas armadilhas
- Distinguir o que cada ferramenta pega: **estilo, bug provável, tipo, segredo**

## 🤔 Por que isso importa
Discutir aspas, vírgulas e imports em code review é um desperdício de energia humana: **máquina** faz isso melhor, mais rápido e sem melindre. Já os **tipos** pegam uma classe inteira de erros (dinheiro como `float`, `None` onde se esperava um valor) sem rodar o código. Juntas, essas ferramentas deixam o review para o que importa: design, regras de negócio, segurança. É também o que empresas esperam ver no repositório de um júnior: `ruff`, `mypy` e `pre-commit` configurados.

## 💡 Intuição (explicação simples)
Pense num **corretor ortográfico com revisor técnico e porteiro**. O **formatador** (`ruff format`) deixa todo o texto no mesmo padrão tipográfico, sem opinião. O **linter** (`ruff check`) sublinha o que provavelmente é erro (variável não usada, import sobrando, `except: pass`). O **verificador de tipos** (`mypy`) confere se você está *somando laranjas com bananas* (passar `float` onde cabe `Decimal`). E o **`pre-commit`** é o porteiro: ninguém entra no repositório com o texto sujo.

## 🔬 Como funciona por dentro
- **Linter × formatador:** o formatador só mexe em **aparência** (espaços, quebras, aspas); o linter aponta **problemas** (alguns corrigíveis sozinhos com `--fix`, outros exigem decisão). `ruff` faz as duas coisas, em milissegundos, em Rust.
- **Regras do `ruff`:** são agrupadas por letra (`E`/`W` estilo, `F` erros de lógica simples, `I` ordem de imports, `B` armadilhas, `UP` modernização, `SIM` simplificações, `S` segurança, `DJ` Django, `C90` complexidade…). Escolha o conjunto **pelo risco**, comece pequeno, e documente cada exceção.
- **Correção segura × insegura:** `--fix` aplica só o que não muda o significado; o resto aparece como "unsafe fix" e pede revisão.
- **Introduzir formatador em código existente:** gera um diff gigante. A boa prática: **um commit só de formatação**, sem nenhuma outra mudança, **registrado em `.git-blame-ignore-revs`** para que o `git blame` continue apontando quem escreveu a lógica. E, se quiser certeza, **compare a árvore sintática (AST)** antes e depois.
- **Tipos em Python são opcionais e verificados por ferramenta:** as anotações (`def f(x: int) -> str`) não mudam a execução; o `mypy` as lê e acusa inconsistências. **Gradual:** comece com `check_untyped_defs` e adicione rigor módulo a módulo (`disallow_untyped_defs`, …).
- **Stubs:** para bibliotecas sem tipos, instalam-se pacotes de *stubs* (`django-stubs`, `types-*`) ou se ignora o módulo com justificativa.
- **`# type: ignore[código]`** silencia **um** erro; use sempre com o código do erro e um comentário do motivo, e ligue `warn_unused_ignores` para que o silenciador morra quando deixar de ser necessário.
- **`pre-commit`:** instala um *hook* do Git que roda comandos sobre os arquivos do commit. Se qualquer hook falha (ou **modifica** arquivos), o commit é **abortado** e você revê. Hooks `local` usam as ferramentas do seu `uv.lock` (mesmas versões do CI); os de repositórios remotos fixam uma `rev`.
- **Em que estágio rodar o quê:** `pre-commit` (a cada commit): rápido (formatar, lint, tipos, segredos). `pre-push`: mais lento (testes de unidade). **CI** (módulo 12): tudo, de novo (hook local é conveniência; o CI é a garantia, porque hooks podem ser pulados com `--no-verify`).

## 🛠️ Exemplo prático
**1. Medir antes de decidir: o estado do código** (`ruff check --statistics`, só com as regras escolhidas, sem mudar nada):
```text
650  E501  line-too-long         ← 88 colunas é o padrão; o projeto usa linhas de ~140
 38  RUF012 mutable-class-default
 29  I001  unsorted-imports
 10  DJ008 django-model-without-dunder-str
  4  E741  ambiguous-variable-name
  4  E702  multiple-statements-on-one-line-semicolon
  ... (758 no total)
```
650 dos 758 avisos eram só `E501`. Em vez de reformatar a base inteira para caber em 88 colunas, a decisão foi **ajustar a régua ao projeto** (`line-length = 140`), o que derrubou o total de 758 para 246; tirando da medição os scripts de experimento antigos da raiz do laboratório (eles não fazem parte do projeto de referência) restaram **145**. **Escolher a configuração com critério** vale mais que aceitar os padrões.

**2. A configuração** (`pyproject.toml`):
```toml
[tool.ruff]
line-length = 140                       # o estilo do projeto usa linhas longas com comentários; 140 evita reformatar tudo sem ganho
target-version = "py313"
force-exclude = true                    # respeita o exclude MESMO quando o pre-commit passa os arquivos um a um
extend-exclude = ["migrations", ".venv", "grpc_demo/*_pb2.py", "grpc_demo/*_pb2_grpc.py"]   # código GERADO não se lint-a

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "UP", "SIM", "C4", "PIE", "RUF", "S", "DJ", "C90"]
ignore = [
    "RUF001", "RUF002", "RUF003",       # caracteres "ambíguos" (×, –, ’) são texto legítimo em português
    "RUF012",                           # atributos de classe do Django/DRF (permission_classes, fields...) são configuração lida pelo framework
]

[tool.ruff.lint.mccabe]
max-complexity = 10                     # a mesma régua da aula 8.03

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "S105", "S106", "S311", "S603", "S108", "RUF012", "B017"]   # assert, senhas de teste, semente fixa, subprocess
"seclab/**" = ["S608"]                  # anti-padrão proposital (aula 9.02)
"scripts/**" = ["S603", "S607", "S311"]
"conftest.py" = ["S101"]               # asserts em fixtures de apoio
"config/settings*.py" = ["F403", "F405"]   # `from .settings import *` é o padrão de configurações por ambiente
```
Cada exceção tem motivo escrito: `RUF012` (atributos de classe do Django/DRF são configuração lida pelo framework), `RUF001–003` (símbolos como `×` são texto normal em português), `S101` só em testes, e **código gerado** (`*_pb2.py`) fora da análise.

**3. Formatar sem medo: um commit só de formatação, com prova.** O laboratório tinha **91 arquivos fora do formato**. Antes de formatar, `pytest` (verde). O commit `style: ruff format (somente formatação)` alterou 91 arquivos (+758/−419 linhas). A prova de que **o programa não mudou** foi comparar a AST, sem docstrings, de cada arquivo antes e depois (`ast_igual.py`):
```text
arquivos alterados: 91 · AST idêntica: 91 · AST diferente: 0
```
Os 91 arquivos têm **AST idêntica**, e os 292 testes seguem iguais. Depois, o hash desse commit entra no `.git-blame-ignore-revs`, e o `git blame` volta a apontar quem escreveu a linha de verdade. Uma linha que a formatação tocou (`apps/orders/tasks.py`, linha 21):
```text
SEM o arquivo de revisões ignoradas: c5ae121f (…)  ← o commit de formatação
COM  .git-blame-ignore-revs:         ^5c42cad (…)  ← o commit onde a lógica nasceu
```
(`git config blame.ignoreRevsFile .git-blame-ignore-revs`; o GitHub reconhece o arquivo com esse nome.)

**4. Corrigir o que o linter achou, em commits separados.**
- `style: ruff --fix`: 28 correções **seguras** automáticas (imports ordenados e removidos os não usados).
- `refactor: corrige avisos do ruff`: as que exigem decisão. Exemplos: `l` (parece `1`) virou `linha`; `try/except/pass` virou `contextlib.suppress(...)` com comentário do motivo; imports espalhados em `settings.py` foram para o topo; um `item_id` e um `nova` nunca usados saíram; linhas longas foram quebradas; e **10 modelos sem `__str__`** ganharam um (o admin e os logs passam a mostrar "Pedido #12 (pending)" em vez de "Order object (12)"). Os `__str__` não alteram o banco: `makemigrations --check` confirmou "No changes detected". Um detalhe de estilo: meu primeiro `__str__` ficou depois dos métodos, e a regra `DJ012` (ordem dos elementos do modelo) acusou; movi para o lugar certo.
Resultado: `ruff check` → **All checks passed!**, `ruff format --check` → tudo formatado.

**5. `mypy`: adoção gradual.** Instalei `mypy`, `django-stubs`, `djangorestframework-stubs` e os stubs de `celery`, `channels` e `django-filter`:
```toml
[tool.mypy]
python_version = "3.13"
plugins = ["mypy_django_plugin.main", "mypy_drf_plugin.main"]
files = ["apps", "config", "legado"]
exclude = ["migrations", "tests"]
check_untyped_defs = true           # confere o CORPO de funções sem anotação também
warn_unused_ignores = true
warn_redundant_casts = true
no_implicit_optional = true

[tool.django-stubs]
django_settings_module = "config.settings_test"

[[tool.mypy.overrides]]
module = ["pika", "pika.*"]
ignore_missing_imports = true           # o pika não publica tipos nem pacote de stubs

[[tool.mypy.overrides]]
# Módulos PUROS e de regra de negócio: tipagem estrita (nenhuma função sem anotação, nada de Any implícito)
module = ["apps.orders.domain", "apps.orders.cupons", "apps.orders.selectors", "legado.precificacao"]
# `strict = true` só existe no nível global; por módulo é preciso listar as opções:
disallow_untyped_defs = true
disallow_incomplete_defs = true
disallow_untyped_calls = true
disallow_any_generics = true
warn_return_any = true
```
A primeira execução, **permissiva** (só `check_untyped_defs`), achou 17 erros em 15 arquivos. Alguns eram ruído de bibliotecas sem tipos; outros eram **reais**:
```text
apps/orders/cupons.py:33: error: Unsupported operand types for < ("date" and "None")
apps/realtime/receivers.py:17: error: Item "None" of "BaseChannelLayer | None" has no attribute "group_send"
apps/cart/api.py:44: error: Incompatible type for lookup 'cart__user': (got "User | AnonymousUser", ...)
legado/pedidos_legado.py:7: error: Need type annotation for "LOG"
config/settings.py:204: error: Incompatible types in assignment (expression has type "int", target has type "Collection[str]")
```
O primeiro é um **bug de verdade no código que escrevi com TDD na aula 04**: `calcular_desconto(cupom_com_validade, subtotal)` sem informar `hoje` fazia `None > date` e levantava `TypeError`. Aplicando TDD ao próprio conserto: escrevi o teste que reproduz (`test_sem_informar_hoje_usa_a_data_de_hoje`), vi falhar com `TypeError: '>' not supported between instances of 'NoneType' and 'datetime.date'`, corrigi (`hoje = hoje or date.today()`) e vi passar (12 testes de cupom). O segundo achado era a camada de Channels não configurada (`get_channel_layer()` pode ser `None`): agora há um *guard* explícito com log em vez de um `AttributeError` engolido por um `except Exception`. Os demais:
- `request.user` pode ser `AnonymousUser` para o tipo; a view já exige `IsAuthenticated`, então usei `cast("User", self.request.user)` com o motivo no comentário;
- `LOG: list[str] = []`; `REST_FRAMEWORK: dict[str, Any]`;
- o `pika` não tem stubs: `ignore_missing_imports` **só para ele**;
- o conflito de tipos entre `django-stubs` e Channels em `path()`/`URLRouter` virou **um** `# type: ignore[arg-type]` por local, com o motivo ao lado.
> 🔎 **Um tropeço de configuração.** Minha primeira tentativa de ser estrito só nos módulos puros usou `strict = true` numa seção por módulo. **`strict` só existe no nível global**: o `mypy` o aplicou ao projeto inteiro e eu vi 200 erros em 48 arquivos. Em seções por módulo é preciso listar as opções (`disallow_untyped_defs`, `disallow_untyped_calls`, `disallow_any_generics`, `warn_return_any`…). Depois disso, o rigor ficou só em `domain`, `cupons`, `selectors` e `precificacao`, e eles passaram a exigir anotações completas (as funções ganharam tipos como `montar_linhas(itens: Sequence[ItemCarrinho], produtos: Mapping[int, ProdutoInfo]) -> list[LinhaCompra]`).
Resultado: `Success: no issues found in 80 source files`. O que ele passa a **barrar** (um arquivo de teste temporário, removido depois):
```text
apps/orders/zz_erro_de_tipo.py:10: error: Argument 2 to "calcular_desconto" has incompatible type "float"; expected "Decimal"  [arg-type]
apps/orders/zz_erro_de_tipo.py:11: error: Argument "hoje" to "calcular_desconto" has incompatible type "str"; expected "date | None"  [arg-type]
apps/orders/zz_erro_de_tipo.py:12: error: List item 0 has incompatible type "int"; expected "LinhaCompra"  [list-item]
apps/orders/zz_erro_de_tipo.py:12: error: List item 1 has incompatible type "int"; expected "LinhaCompra"  [list-item]
apps/orders/zz_erro_de_tipo.py:12: error: List item 2 has incompatible type "int"; expected "LinhaCompra"  [list-item]
Found 5 errors in 1 file (checked 81 source files)
```
Dinheiro como `float`, data como texto e lista de inteiros no lugar de objetos: três erros que só apareceriam em produção, agora apontados antes de rodar.

**6. `pre-commit`: o porteiro** (`.pre-commit-config.yaml`; hooks **locais**, com as versões do `uv.lock`):
```yaml
# Hooks LOCAIS: usam as ferramentas e AS VERSÕES travadas no uv.lock (nada é baixado de repositórios de terceiros).
# Instalar:  uv run pre-commit install --install-hooks && uv run pre-commit install --hook-type commit-msg
repos:
  - repo: local
    hooks:
      - id: ruff-lint
        name: ruff (lint)
        entry: uv run ruff check --fix --exit-non-zero-on-fix
        language: system
        types: [python]
      - id: ruff-format
        name: ruff (formatação)
        entry: uv run ruff format
        language: system
        types: [python]
      - id: mypy
        name: mypy (tipos)
        entry: uv run mypy
        language: system
        types: [python]
        pass_filenames: false          # o mypy analisa o projeto inteiro (precisa do contexto dos imports)
      - id: secrets
        name: detect-secrets (segredos)
        entry: uv run detect-secrets-hook --baseline .secrets.baseline
        language: system
        types: [text]
        exclude: ^(uv\.lock|schema\.yml|\.secrets\.baseline)$
      - id: testes-rapidos
        name: pytest (somente os de unidade)
        entry: uv run pytest -q -m unidade -x -p no:randomly
        language: system
        pass_filenames: false
        types: [python]
        stages: [pre-push]               # roda no push, não a cada commit: o commit precisa ser rápido
```
O `detect-secrets` usa o *baseline* (4 achados já triados na aula 9.06, todos placeholders). Instalação: `uv run pre-commit install` (e `--hook-type pre-push`). Com o código limpo:
```text
ruff (lint)..............................................................Passed
ruff (formatação)........................................................Passed
mypy (tipos).............................................................Passed
detect-secrets (segredos)................................................Passed
```
Tempo de `--all-files`: ~1,5 s com cache do `mypy`. Agora, um **commit ruim de propósito** (import não usado, formatação torta, tipo errado e a chave de exemplo da AWS):
```text
ruff (lint)..............................................................Failed
- hook id: ruff-lint
- files were modified by this hook      (removeu imports não usados e reordenou: "Found 4 errors (4 fixed)")
ruff (formatação)........................................................Failed
- files were modified by this hook      (ajustou espaços e quebras de linha)
mypy (tipos).............................................................Failed
apps/orders/ruim.py:7: error: Incompatible return value type (got "Decimal", expected "int")  [return-value]
detect-secrets (segredos)................................................Failed
Secret Type: AWS Access Key
Location:    apps/orders/ruim.py:3
```
**Quatro hooks falharam e nenhum commit foi criado**: os dois primeiros corrigiram o arquivo (e por isso "falham": você precisa revisar e dar `git add` de novo), o `mypy` achou o tipo errado e o `detect-secrets` achou a chave. Limpei o arquivo depois.
> 🔎 **A armadilha do `exclude`.** Na primeira rodada em todos os arquivos, os hooks **reformataram as migrações e o código gerado do gRPC**, mesmo eles estando em `extend-exclude`. Motivo: o `pre-commit` passa os arquivos **um a um na linha de comando**, e nesse caso o `ruff` ignora o `exclude`. A correção é `force-exclude = true` no `pyproject.toml`. Desfiz as alterações indevidas e, depois do ajuste, as duas rodadas seguintes passaram sem modificar nada. Sempre rode `pre-commit run --all-files` **duas vezes**: a segunda tem de passar limpa.
O estágio `pre-push` roda também os **testes de unidade** (`pytest -m unidade`, ~1 s):
```text
ruff (lint)..............................................................Passed
ruff (formatação)........................................................Passed
mypy (tipos).............................................................Passed
detect-secrets (segredos)................................................Passed
pytest (somente os de unidade)...........................................Passed
```

**7. O histórico que ficou** (cada linha é um passo reversível e revisável):
```text
681347c fix(ruff): force-exclude para o pre-commit respeitar migrações e código gerado
b427de1 build: pre-commit com ruff, mypy e detecção de segredos
1e75f42 feat(types): mypy com django-stubs (estrito nos módulos puros) e correção do bug de 'hoje' nos cupons
b7e66b3 refactor: corrige avisos do ruff (__str__ nos modelos, nomes claros, imports no topo)
226f642 style: ruff --fix (imports ordenados e removidos os não usados)
f4502e9 chore: .git-blame-ignore-revs para o commit de formatação
c5ae121 style: ruff format (somente formatação)
```
Repare que a formatação e a lógica estão em commits **separados**: é isso que permite revisar e reverter cada um.

**8. Estado final**
```text
292 passed, 1 skipped, 1 xfailed     ruff check: All checks passed!     mypy: Success, 80 source files
lint-imports: 3 contratos cumpridos  makemigrations --check: No changes detected
```

## 🧠 Pausa para lógica
**Problema.** Um colega propõe: "vamos rodar `ruff format` e, no mesmo commit, corrigir os avisos do linter e renomear algumas funções para ficar mais claro". (a) Por que isso é uma má ideia? (b) Qual a ordem correta de commits? (c) Como provar que o commit de formatação não mudou o programa?

<details><summary>Dica</summary>Pense em quem vai revisar um diff de 90 arquivos, e no que acontece se um bug entrar no meio.</details>

<details><summary>Solução comentada</summary>

(a) Um commit que mistura formatação, correções e renomeações tem um diff enorme em que a mudança de lógica **se esconde**; o revisor não consegue ver o que mudou de verdade, e reverter uma parte é impossível sem desfazer tudo. O `git blame` também passa a apontar o commit de formatação para todas as linhas. (b) 1) só formatação; 2) correções automáticas seguras; 3) correções manuais/renomeações; cada um com os testes verdes. (c) Compare a AST (sem docstrings) de cada arquivo entre o commit anterior e o de formatação, como no `ast_igual.py`, e confirme que os testes passam iguais. Registre o commit em `.git-blame-ignore-revs`.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| Diff gigante de formatação misturado com lógica | Formatar junto com outras mudanças | Commit só de formatação + `.git-blame-ignore-revs` |
| 650 avisos de linha longa | Régua padrão que não é a do projeto | Ajustar `line-length` conscientemente |
| `# noqa`/`# type: ignore` espalhados sem motivo | Silenciar para "passar" | Código do erro + comentário do motivo; `warn_unused_ignores` |
| Regras demais de uma vez | Entusiasmo | Começar pequeno, ampliar por risco |
| `strict = true` em seção por módulo | `strict` é global | Listar as opções individuais |
| `pre-commit` reformatando arquivos que deveriam ser excluídos | `exclude` ignorado ao passar arquivos | `force-exclude = true` |
| Hook que "falha" só porque corrigiu o arquivo | Comportamento normal | Revisar, `git add`, commitar de novo |
| Commit lento e as pessoas usam `--no-verify` | Hooks pesados a cada commit | Rápidos no commit; testes no `pre-push`; tudo no CI |
| Confiar só no hook local | Hook pode ser pulado | O CI repete as mesmas verificações |
| Anotar tudo com `Any` para calar o `mypy` | Fuga | Anotar de verdade, módulo a módulo |
| Bibliotecas sem tipos geram ruído | Falta de stubs | `types-*`/`*-stubs`, ou `ignore_missing_imports` só para elas |
| Dinheiro em `float` | Sem tipos | `Decimal` e anotação; o `mypy` acusa a mistura |

- **Máquina para estilo, gente para design.**
- **Versões das ferramentas travadas** (`uv.lock`) para o hook local e o CI darem o mesmo resultado.
- **Adote tipos gradualmente:** primeiro onde há mais regra de negócio.

## 🧩 Exercícios
**1. Fixação.** (a) Qual a diferença entre linter e formatador? (b) O que é uma correção "insegura"? (c) Por que o `pre-commit` considera "falha" um hook que modificou arquivos? (d) Por que o CI precisa repetir as verificações do hook?

<details><summary>Solução</summary>

(a) O formatador muda só a aparência; o linter aponta problemas prováveis (e alguns têm correção automática). (b) Uma que pode mudar o comportamento, então exige revisão humana. (c) Porque o arquivo no commit já não é o que foi revisado; é preciso conferir o resultado e adicionar de novo. (d) Hooks podem ser pulados (`--no-verify`) ou não estarem instalados na máquina de quem contribui; o CI é a garantia.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] `[tool.ruff]` com `line-length` justificado, regras escolhidas e **cada exceção com comentário**
- [ ] Um commit **só de formatação**, com a prova de AST idêntica e o hash em `.git-blame-ignore-revs`
- [ ] `ruff check` e `ruff format --check` limpos; commits separados para `--fix` e correções manuais
- [ ] `mypy` com `django-stubs`, `check_untyped_defs`, rigor nos módulos puros e **nenhum** `# type: ignore` sem código e motivo
- [ ] Pelo menos **um bug real** achado pelo `mypy`, corrigido com um teste que o reproduz antes (TDD)
- [ ] `.pre-commit-config.yaml` com ruff, mypy, detect-secrets e testes de unidade no `pre-push`; `force-exclude` conferido
- [ ] Demonstração de um commit **bloqueado** e a saída anexada
- [ ] Documentar no README como instalar os hooks (`uv run pre-commit install`)
- [ ] Commits `style:`, `refactor:`, `build:`, `feat(types):`

**3. Desafio (opcional).** Torne também o módulo `apps.cart.services` e `apps.payments.services` **estritos** no `mypy`. Anote tudo, resolva os erros sem `Any` e meça quantos novos achados reais aparecem.

## 🎤 Na entrevista
- **Para que servem `ruff`, `mypy` e `pre-commit`?** `ruff` formata e aponta problemas de código; `mypy` confere tipos estaticamente; `pre-commit` roda essas verificações antes de cada commit para barrar erros cedo.
- **Como introduzir um formatador num projeto existente?** Num commit separado só de formatação, comprovando que o comportamento não mudou, e registrando esse commit no `.git-blame-ignore-revs`.
- **Tipos em Python mudam a execução?** Não; as anotações são verificadas por ferramentas como o `mypy` e servem de documentação e de rede de proteção.
- **Como adotar tipos em um código legado?** Gradualmente: `check_untyped_defs` no geral, rigor módulo a módulo começando pelo núcleo de regras de negócio, e stubs para as bibliotecas.
- **Por que ter CI se já tem `pre-commit`?** Porque o hook local é opcional (pode ser pulado ou não instalado); o CI garante que nada entra sem passar.
- **Por que `Decimal` e não `float` para dinheiro?** Porque `float` é binário e aproximado; o `mypy` ajuda a impedir a mistura acidental.

## 📚 Para ir além
- 📄 Documentação: [Ruff](https://docs.astral.sh/ruff/), o [formatador](https://docs.astral.sh/ruff/formatter/), o [catálogo de regras](https://docs.astral.sh/ruff/rules/) e a [opção `force-exclude`](https://docs.astral.sh/ruff/settings/#force-exclude) (em inglês).
- 📄 Documentação: [mypy](https://mypy.readthedocs.io/en/stable/) e [adotando tipos em código existente](https://mypy.readthedocs.io/en/stable/existing_code.html) (em inglês).
- 📄 Repositórios: [django-stubs](https://github.com/typeddjango/django-stubs) e [djangorestframework-stubs](https://github.com/typeddjango/djangorestframework-stubs). Tipos para Django e DRF (em inglês).
- 📄 Documentação: [pre-commit](https://pre-commit.com/). Hooks, estágios e repositórios (em inglês).
- 📄 Documentação: [`git blame --ignore-revs-file`](https://git-scm.com/docs/git-blame#Documentation/git-blame.txt---ignore-revs-fileltfilegt). Como ignorar commits de formatação.
- 📄 Documentação oficial: [`typing`](https://docs.python.org/3/library/typing.html) e a [referência de tipos do Python](https://typing.python.org/en/latest/) (em inglês).

## ✅ Checklist da aula
- [ ] Configurei o `ruff` com critério e justifiquei cada exceção
- [ ] Formatei o código num commit à parte, provei que o programa não mudou e registrei o commit no `.git-blame-ignore-revs`
- [ ] Adotei o `mypy` gradualmente e corrigi pelo menos um bug real que ele achou
- [ ] Montei o `pre-commit`, vi um commit ruim ser barrado e conferi o `force-exclude`
- [ ] Sei por que o CI repete as verificações
