# Cheatsheet: pytest

| Objetivo | Como |
|---|---|
| Instalar / rodar | `uv add --dev pytest` · `uv run pytest` |
| Parar no 1º erro / filtrar / detalhar | `-x` · `-k expr` · `-v` |
| Um teste | `pytest tests/test_x.py::test_nome` |
| Exceção esperada | `with pytest.raises(ValueError, match="texto"):` |
| Vários dados | `@pytest.mark.parametrize("a,b,esp", [(1,2,3), ...])` |
| Pasta temporária | parâmetro `tmp_path` (um `Path` novo por teste) |
| Capturar `print` | parâmetro `capsys` → `capsys.readouterr().out` |
| Config mínima | `[tool.pytest.ini_options]` `pythonpath=["."]` `testpaths=["tests"]` |
| Padrão | Arrange → Act → Assert; nomes que descrevem comportamento |
