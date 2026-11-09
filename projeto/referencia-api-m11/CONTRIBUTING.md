# Como contribuir

## Fluxo
1. Crie uma branch a partir da `main`: `feat/nome-curto`, `fix/nome-curto`.
2. Escreva o **teste primeiro** quando for uma regra de negócio ou um bug (veja a aula de TDD): vermelho → verde → refatorar.
3. Faça commits pequenos no padrão abaixo. Os *hooks* do `pre-commit` rodam sozinhos.
4. Abra o Pull Request usando o modelo. Ele só entra com os **portões automáticos verdes** (testes, `ruff`, `mypy`, cobertura das camadas de negócio) **e** com a aprovação de uma pessoa.

## Mensagens de commit (Conventional Commits)
`tipo(escopo): descrição no imperativo, sem ponto final`

| Tipo | Quando |
|---|---|
| `feat` | funcionalidade nova (sobe o MINOR) |
| `fix` | correção de bug (sobe o PATCH) |
| `refactor` | muda a estrutura sem mudar o comportamento |
| `perf` | melhoria de desempenho |
| `test` | só testes |
| `docs` | só documentação |
| `style` | só formatação |
| `build`, `ci`, `chore` | ferramentas, pipeline, manutenção |

Mudança que quebra compatibilidade: acrescente `!` (`feat(orders)!: ...`) e explique no corpo. **Formatação e lógica nunca no mesmo commit.**

## Antes de pedir revisão
```bash
uv run pytest && uv run ruff check && uv run ruff format --check && uv run mypy && uv run lint-imports && bash scripts/cobertura_negocio.sh
```
