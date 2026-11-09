"""Logs estruturados (aula 14.01): uma linha JSON por evento, com correlação por `request_id`.

Sem dependências externas. O formato JSON é para MÁQUINAS (CloudWatch Logs Insights, Loki, ELK): campos fixos e consultáveis.
"""

import contextvars
import json
import logging
import re
from datetime import UTC, datetime

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

# campos que NUNCA devem sair em log, mesmo que alguém os passe em `extra=` por descuido
SENSIVEIS = re.compile(r"(passw|senha|secret|token|authorization|cookie|api[-_]?key|dsn)", re.I)
PADRAO_LOGRECORD = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime", "request_id"}


class RequestContextFilter(logging.Filter):
    """Acrescenta o `request_id` (do contexto da requisição atual) a TODO registro, de qualquer logger."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def redigir(valor):
    """Troca valores de chaves sensíveis por [REDACTED], recursivamente."""
    if isinstance(valor, dict):
        return {k: "[REDACTED]" if SENSIVEIS.search(str(k)) else redigir(v) for k, v in valor.items()}
    if isinstance(valor, list | tuple):
        return [redigir(v) for v in valor]
    return valor


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        registro = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        extras = {k: v for k, v in record.__dict__.items() if k not in PADRAO_LOGRECORD and not k.startswith("_")}
        registro.update(redigir(extras))
        if record.exc_info:
            registro["exc"] = self.formatException(record.exc_info)
        return json.dumps(registro, ensure_ascii=False, default=str)
