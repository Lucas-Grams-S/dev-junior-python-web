# 02. Instalando Python, ambientes virtuais, pip e uv

> ⏱️ ~1h30 · Módulo 0 · Pré-requisitos: [01](01-terminal-e-arquivos.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Explicar por que cada projeto precisa do seu próprio ambiente virtual
- Criar e ativar um ambiente com `venv` e instalar pacotes com `pip`
- Criar um projeto com `uv`, instalar uma dependência e rodar código nele
- Ler `pyproject.toml`, `.python-version` e `uv.lock`
- Diagnosticar `ModuleNotFoundError` e `externally-managed-environment`

## 🤔 Por que isso importa
O projeto A precisa de `Django 5.2` e o projeto B de `Django 6.1`. Se tudo é instalado no mesmo lugar, um quebra o outro. Em um time, “na minha máquina funciona” vem quase sempre de versões diferentes. Ambiente isolado + arquivo de dependências travado resolvem isso.

## 💡 Intuição (explicação simples)
Um ambiente virtual é uma **caixa de ferramentas por projeto**. Em vez de uma garagem única com todas as ferramentas do mundo misturadas, cada obra leva só as ferramentas (e versões) de que precisa. E o `uv.lock` é a **lista de compras exata** da caixa: quem montar a caixa a partir dela obtém as mesmas ferramentas.

## 🔬 Como funciona por dentro
- Um **ambiente virtual** é uma pasta (`.venv`) com um `python` próprio e uma pasta `site-packages/` onde os pacotes são instalados. Não é uma máquina virtual: é só uma pasta e um atalho para o interpretador.
- **Ativar** (`source .venv/bin/activate`) apenas coloca `.venv/bin` na frente do `PATH`. Por isso, `python` e `pip` passam a ser os da caixa. `deactivate` desfaz.
- Dentro de um ambiente, `sys.prefix` aponta para a `.venv`; fora, `sys.prefix == sys.base_prefix`.
- **pip** instala pacotes do PyPI (o repositório público de pacotes Python). **uv** é um gerenciador moderno que faz o trabalho de `pip` + `venv` + instalação de versões do Python + travamento de dependências, bem mais rápido.

| Arquivo | Para que serve | Vai para o Git? |
|---|---|---|
| `pyproject.toml` | Metadados do projeto e **o que** ele precisa (`requests>=...`) | Sim |
| `uv.lock` | **Versões exatas** de tudo, inclusive dependências indiretas | Sim |
| `.python-version` | Qual Python o projeto usa | Sim |
| `.venv/` | A caixa de ferramentas em si | **Não** (é gerada) |

Versões adotadas no curso: **Python 3.13** e uv atual (ver [versões](../00-guia/versoes.md)). Instalação do uv: siga a [documentação oficial](https://docs.astral.sh/uv/); o instalador padrão no Linux/macOS é um script, então abra a página e leia o que ele faz antes de executar um `curl ... | sh`.

## 🛠️ Exemplo prático
Testado com uv 0.13.7 e Python 3.13. As versões de pacotes na saída mudam com o tempo.

**1. `venv` + `pip` (o jeito “de fábrica”)**
```bash
mkdir v && cd v
python3 -m venv .venv
source .venv/bin/activate
which python
deactivate
```
```text
/…/v/.venv/bin/python
```
Depois de ativar, o prompt costuma ganhar o prefixo `(.venv)`. Instalar: `pip install requests`; listar: `pip list`; congelar: `pip freeze > requirements.txt`.

**2. Projeto com `uv`**
```bash
cd ~/projetos/minishop      # criada na aula 01
uv init --no-package --python 3.13
ls -a
```
```text
.  ..  .git  .gitignore  .python-version  README.md  docs  main.py  pyproject.toml  src
```
O `uv init` já cria um repositório Git e um `.gitignore` com `.venv`. Se a pasta já tinha um `README.md`, ele é mantido. Rodar:
```bash
uv run main.py
```
```text
Using CPython 3.13.18
Creating virtual environment at: .venv
Hello from minishop!
```
O `uv` baixou o Python 3.13 (se faltasse), criou a `.venv` e rodou o arquivo. Sem ativar nada.

**3. Adicionar dependência**
```bash
uv add requests
uv run python -c "import sys, requests; print(sys.version.split()[0], requests.__version__)"
```
```text
 + requests==2.34.2
 + urllib3==2.8.0
3.13.18 2.34.2
```
Agora `pyproject.toml` lista `requests` em `dependencies` e o `uv.lock` foi criado. Para recriar o ambiente em outra máquina: `uv sync`.

**4. Provar o isolamento**
```bash
python3 -c "import sys; print(sys.prefix == sys.base_prefix)"        # True  (fora)
uv run python -c "import sys; print(sys.prefix == sys.base_prefix)"  # False (dentro da .venv)
```

**5. Dependência de desenvolvimento e remoção**
```bash
uv add --dev pytest
uv remove requests
```

## ⚠️ Erros comuns e boas práticas
| Mensagem | Causa | Solução |
|---|---|---|
| `ModuleNotFoundError: No module named 'flask'` | O pacote não está instalado **neste** ambiente | `uv add flask` (ou `pip install` com a venv ativa); confira qual `python` roda com `which python` |
| `error: externally-managed-environment` | O Python do sistema (Debian/Ubuntu) recusa `pip install` global | Use um ambiente virtual ou o `uv`. Nunca force com `--break-system-packages` |
| `command not found: python` | No Ubuntu o comando pode ser `python3` | Use `python3`, ou rode via `uv run` |
| Instalou mas o editor não reconhece | Editor usando outro interpretador | Selecione o interpretador `.venv` (aula 05) |

- **Nunca** versione a `.venv`. **Sempre** versione `pyproject.toml` e `uv.lock`.
- Um ambiente por projeto. Se estragar, apague `.venv` e rode `uv sync`.
- Instale pacotes de fontes conhecidas e confira o nome (existem pacotes maliciosos com nomes parecidos, o *typosquatting*).

## 🧩 Exercícios
**1. Fixação**
a) O que `source .venv/bin/activate` realmente muda?
b) Qual a diferença de papel entre `pyproject.toml` e `uv.lock`?

<details><summary>Solução</summary>

a) Só coloca `.venv/bin` no início do `PATH` (e ajusta o prompt), de modo que `python` e `pip` passem a ser os da `.venv`.
b) `pyproject.toml` declara o que o projeto pede (com faixas de versão); `uv.lock` registra as versões exatas resolvidas, para que todos instalem o mesmo.
</details>

**2. Aplicação no projeto MiniShop**
Transforme `~/projetos/minishop` em um projeto `uv`.

Critérios de pronto:
- [ ] `pyproject.toml`, `.python-version` (3.13) e `uv.lock` existem
- [ ] `uv run main.py` imprime a saudação
- [ ] `requests` está nas dependências e `uv run python -c "import requests"` não dá erro
- [ ] `.venv/` está no `.gitignore` (confira, não suponha)
- [ ] Você apagou `.venv` e recriou com `uv sync`

<details><summary>Solução de referência</summary>

```bash
cd ~/projetos/minishop
uv init --no-package --python 3.13
uv add requests
cat .gitignore | grep venv      # .venv
rm -rf .venv && uv sync && uv run main.py
```
</details>

**3. Desafio (opcional)**
Crie o mesmo ambiente com `venv` + `pip`, gere `requirements.txt` e instale-o em um segundo ambiente. Compare o que `pip freeze` mostra com o que `uv.lock` guarda.

## 🎤 Na entrevista
- **Por que usar ambiente virtual?** Para isolar versões de dependências por projeto e evitar conflitos entre eles e com o Python do sistema; torna o projeto reproduzível.
- **Qual a diferença entre `pip install` e `pip freeze`?** `install` coloca pacotes no ambiente; `freeze` lista os instalados com versões exatas, normalmente salvo em `requirements.txt`.
- **Para que serve um lockfile?** Garantir que todos (e o servidor) instalem exatamente as mesmas versões, inclusive de dependências indiretas.

## 📚 Para ir além
- 📄 Documentação oficial: [uv](https://docs.astral.sh/uv/). Guia de projetos e comandos; leia “Working on projects”.
- 📄 Documentação oficial: [Tutorial de venvs (docs.python.org)](https://docs.python.org/3/tutorial/venv.html). Explicação oficial do `venv` e do `pip`.
- 🎥 Vídeo (PT-BR): canal [Curso em Vídeo](https://www.youtube.com/@cursoemvideo). Procure a playlist de Python do Gustavo Guanabara para revisar instalação. ⚠️ Link direto da playlist não verificado.
- 🏋️ Prática extra: crie dois projetos com versões diferentes de `requests` e prove (com `uv run`) que não se misturam.

## ✅ Checklist da aula
- [ ] `uv --version` funciona
- [ ] Criei um ambiente com `venv` e outro com `uv`
- [ ] Sei dizer o que vai e o que não vai para o Git
- [ ] Provoquei um `ModuleNotFoundError` e o resolvi
