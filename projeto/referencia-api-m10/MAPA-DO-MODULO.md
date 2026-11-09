# Mapa do módulo 10 (material do curso)

Este diretório é o **laboratório usado para executar e verificar** as aulas do módulo 10. O `README.md` é o do próprio MiniShop (um dos entregáveis). O histórico Git do laboratório (7 commits de ferramentas, o PR do CSV e os de documentação) está resumido em `docs/historico-git.txt`; o diretório `.git` não é distribuído.

| Onde | Aula |
|---|---|
| `conftest.py` (marcadores, fábricas, `hasher_de_producao`), `config/settings_test.py`, `scripts/m10/perfil_seed.py`, `tests/test_fabricas.py` | 10.01 |
| `tests/test_parametrize_mocks.py`, `test_armadilhas_de_mock.py`, `test_mocks_vs_fakes.py`, `scripts/m10/mutar_servico.sh` | 10.02 |
| `pyproject.toml` (`[tool.coverage]`), `scripts/cobertura_negocio.sh`, `tests/test_servico_carrinho.py`, `test_pagamentos_servico.py`, `test_outbox_rele.py`, `test_comandos_e_tarefas.py` | 10.03 |
| `apps/orders/cupons.py`, `tests/test_cupons.py`, `scripts/m10/tdd/` (a sessão de ciclos reproduzida) | 10.04 |
| `pyproject.toml` (`[tool.ruff]`, `[tool.mypy]`), `.pre-commit-config.yaml`, `.git-blame-ignore-revs`, `scripts/m10/ast_igual.py` | 10.05 |
| `apps/orders/export.py`, `tests/test_exportar_pedidos.py` (o PR), `CONTRIBUTING.md`, `.github/pull_request_template.md`, `docs/code-review.md`, `README.md` | 10.06 |
| `docs/historias/cupom.md`, `tests/test_aceitacao_cupom.py`, `scripts/definicao_de_pronto.sh`, `docs/uso-de-ia.md`, `scripts/m10/sugestao_ia.py` e `teste_da_sugestao_ia.py`, `checa_pacote.py` | 10.07 |
| `scripts/m10/saidas/` | as saídas reais coladas nas aulas |

Para usar os *hooks*: `git init && git add -A && git commit -m "chore: baseline"` e depois `uv run pre-commit install --install-hooks && uv run pre-commit install --hook-type commit-msg --hook-type pre-push`.
