# Setup do ambiente

> Rascunho do plano; comandos exatos serão verificados e testados na geração do Módulo 0.

## O que será instalado
| Ferramenta | Para quê | Módulo |
|---|---|---|
| Terminal Linux (WSL2 no Windows) | Shell | 0 |
| Git + conta GitHub | Versionamento | 0 |
| `uv` (instala Python 3.13) | Python, venv e dependências | 0 |
| VS Code + extensões Python, Ruff | Editor/debugger | 0 |
| Docker Engine/Desktop | PostgreSQL e Redis locais | 3 |
| Bruno ou HTTPie, `curl` | Testar APIs | 2 |
| Node.js LTS | Só para ferramentas do front (opcional) | 4 |
| AWS CLI v2 | Nuvem | 13 |

## Por sistema operacional
- **Linux (Ubuntu/Debian):** gerenciador de pacotes `apt`; Docker Engine oficial.
- **Windows:** instalar **WSL2 + Ubuntu** e trabalhar *dentro* do WSL (projeto na home do Linux, não em `/mnt/c`); Docker Desktop com integração WSL.
- **macOS:** Homebrew; Docker Desktop.

## Verificação final
```bash
git --version && uv --version && uv python list | head && docker --version
```
