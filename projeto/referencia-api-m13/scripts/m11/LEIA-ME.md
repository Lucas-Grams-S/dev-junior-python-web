# Scripts auxiliares do módulo 11
| Arquivo | Aula | Uso |
|---|---|---|
| `versao.py` | 11.01 | usa `match` (Python 3.10+): roda no 3.13 e dá `SyntaxError` no 3.8 |
| `tick.py` | 11.05 | imprime 1 linha por segundo (efeito do `PYTHONUNBUFFERED`) |
| `carga.py` | 11.06 | `python3 carga.py URL [N]`: N requisições simultâneas e o tempo total |
| `slow.py` | 11.06 | app WSGI mínimo que dorme o tempo da URL (`/5` = 5 s), para `--timeout` e `HUP` |
| `login.py` | 11.06 | `python login.py URL N`: N logins errados (mostra 401/429), com `Host: localhost` |
| `ws.py` | 11.06 | abre o WebSocket do pedido #1 por `wss://127.0.0.1:8443` (precisa do pacote `websockets`: `uv run python scripts/m11/ws.py`) |
