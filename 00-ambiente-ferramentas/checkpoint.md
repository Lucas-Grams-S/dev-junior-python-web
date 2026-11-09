# Checkpoint — Módulo 0: Ambiente e ferramentas

> ⏱️ ~1h30 · Faça **sem consultar** as aulas na primeira tentativa.

## 📝 Quiz (10 questões)
1. Qual a diferença entre caminho absoluto e relativo? Dê um exemplo de cada.
2. O que `chmod 640 arquivo` define para dono, grupo e outros?
3. Para que servem `>`, `>>` e `|`?
4. O que o `activate` de um ambiente virtual muda, na prática?
5. Quais arquivos de um projeto `uv` vão para o Git e quais não?
6. Cite as três áreas do Git e o comando que move uma alteração de uma para a próxima.
7. Por que apagar uma senha em um novo commit não resolve o vazamento?
8. Qual a diferença entre `git fetch` e `git pull`?
9. Como resolver um conflito de merge, passo a passo?
10. Em que ordem você lê um traceback e por quê?

<details><summary>Gabarito</summary>

1. Absoluto começa em `/` (`/home/ana/projetos`); relativo parte da pasta atual (`projetos/minishop`, `../docs`).
2. Dono `rw-` (6), grupo `r--` (4), outros nenhuma (0).
3. `>` redireciona a saída para arquivo (sobrescreve); `>>` acrescenta; `|` liga a saída de um comando à entrada do próximo.
4. Coloca `.venv/bin` no início do `PATH`, de modo que `python`/`pip` sejam os do ambiente.
5. Vão: `pyproject.toml`, `uv.lock`, `.python-version`, código, `.gitignore`. Não vão: `.venv/`, `.env`, caches.
6. Diretório de trabalho → (`git add`) → staging → (`git commit`) → repositório.
7. O segredo continua no histórico e em clones; é preciso revogar/trocar o segredo.
8. `fetch` baixa sem integrar; `pull` baixa e faz merge.
9. Abrir o arquivo, escolher/combinar as versões entre os marcadores, remover os marcadores, testar, `git add`, `git commit`.
10. De baixo para cima: primeiro tipo/mensagem do erro, depois a última linha do seu código, depois quem chamou.
</details>

## 🛠️ Entrega prática
Repositório `minishop` no GitHub com:
- [ ] `README.md` com título, descrição e seção “Como rodar” (`uv sync` e `uv run main.py`)
- [ ] `.gitignore` com `.venv/` e `.env`
- [ ] `pyproject.toml`, `.python-version` (3.13) e `uv.lock`
- [ ] Histórico com ≥ 5 commits no padrão Conventional Commits
- [ ] 1 PR mesclado (branch → `main`)
- [ ] Tag criada: `git tag v0.0-ambiente && git push --tags`

## 🪞 Autoavaliação
Dê uma nota de 0 a 3 (0 = não sei; 3 = explico para alguém) em cada item. Se algum for **0 ou 1**, refaça a aula indicada antes de seguir.

| Habilidade | Aula | Nota |
|---|---|---|
| Navegar e manipular arquivos no terminal | 01 | |
| Ler permissões e usar `chmod` | 01 | |
| Criar e usar ambiente com `uv` | 02 | |
| Commitar e ler o histórico | 03 | |
| Branch, PR e conflito | 04 | |
| Depurar e ler tracebacks | 05 | |
| Pedir ajuda e usar IA com responsabilidade | 05 | |

➡️ Próximo: [Módulo 1 — Python e lógica de programação](../01-python-logica/README.md).
