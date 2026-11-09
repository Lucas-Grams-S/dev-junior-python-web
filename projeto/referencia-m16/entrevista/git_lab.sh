#!/usr/bin/env bash
# Laboratório de Git para a aula 16.04: repositório descartável em um diretório temporário.
set -euo pipefail
D=$(mktemp -d); cd "$D"
git init -q -b main . && git config user.email a@b.c && git config user.name lab
echo a > f; git add f; git commit -qm "base"
git switch -qc feature; echo b >> f; git commit -qam "feature 1"; echo c >> f; git commit -qam "feature 2"
git switch -q main; echo x > g; git add g; git commit -qm "main avançou"
echo "== merge --no-ff (preserva a bifurcação)"
git switch -qc t-merge feature; git merge -q --no-ff main -m "merge main" ; git log --oneline --graph | cat
echo "== rebase (história linear, hashes novos)"
git switch -qc t-rebase feature; git rebase -q main; git log --oneline --graph | cat
echo "== reset --hard × revert (história já publicada: use revert)"
git switch -q main; echo erro > h; git add h; git commit -qm "commit ruim"
git revert --no-edit HEAD >/dev/null; git log --oneline | head -3 | cat
echo "== reflog salva um reset --hard"
git reset -q --hard HEAD~2; git log --oneline | head -1 | cat; git reflog | head -3 | cat
git reset -q --hard 'HEAD@{1}'; git log --oneline | head -1 | cat
echo "== conflito"
git switch -qc c1 main; echo um > k; git add k; git commit -qm c1
git switch -qc c2 main; echo dois > k; git add k; git commit -qm c2
(git merge c1 2>&1 || true) | tail -2 | cat; git diff --name-only --diff-filter=U | cat; sed -n 1,5p k
git merge --abort; rm -rf "$D"
