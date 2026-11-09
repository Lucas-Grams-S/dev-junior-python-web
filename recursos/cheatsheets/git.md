# Cheatsheet: Git

| Objetivo | Comando |
|---|---|
| Identificar-se | `git config --global user.name "Nome"` · `user.email "e@x.com"` |
| Iniciar / clonar | `git init` · `git clone <url>` |
| Estado | `git status -s` |
| Ver mudanças | `git diff` · `git diff --staged` |
| Adicionar / commitar | `git add <arq>` · `git add -A` · `git commit -m "feat: ..."` |
| Histórico | `git log --oneline --graph --all` · `git show <hash>` |
| Descartar alteração | `git restore <arq>` (irreversível) · `git restore --staged <arq>` |
| Desfazer um commit | `git revert <hash>` |
| Parar de rastrear | `git rm --cached <arq>` |
| Branch | `git switch -c <nome>` · `git switch <nome>` · `git branch -d <nome>` |
| Integrar | `git merge <branch>` · `git merge --abort` |
| Remoto | `git remote add origin <url>` · `git push -u origin <branch>` · `git fetch` · `git pull` |
| Guardar temporário | `git stash` · `git stash pop` |
| PR (GitHub CLI) | `gh pr create --fill` · `gh pr merge --squash --delete-branch` |

Prefixos Conventional Commits: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `perf`.
