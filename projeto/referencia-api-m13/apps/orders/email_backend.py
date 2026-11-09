"""Um 'SMTP' de mentira: demora como um servidor real e grava cada e-mail num arquivo (visível para qualquer processo)."""

import json
import os
import time

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

FALHAS = {"n": 0}  # contador por processo (use `worker -c 1` na demonstração)


class SmtpLentoEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        for m in email_messages:
            time.sleep(settings.EMAIL_SIMULATED_DELAY)  # a ESPERA de rede do SMTP
            if FALHAS["n"] < int(os.environ.get("EMAIL_FAIL_FIRST", "0")):  # simula um SMTP que cai nas primeiras tentativas
                FALHAS["n"] += 1
                raise ConnectionError(f"SMTP indisponível (falha simulada {FALHAS['n']})")
            with open(settings.EMAIL_OUTBOX_FILE, "a") as f:
                f.write(json.dumps({"to": m.to, "subject": m.subject, "body": m.body}, ensure_ascii=False) + "\n")
        return len(email_messages)
