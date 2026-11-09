"""celery beat: o relógio que ENFILEIRA as tarefas na hora certa; o worker as executa. E o perigo de dois beats."""
import os
import re
import signal
import subprocess
import time
from pathlib import Path

import redis

LAB = Path(os.environ["LAB"])
BIN = LAB / ".venv/bin/celery"
R = redis.Redis(port=6390)
env = {**os.environ, "BEAT_DEMO": "1"}


def iniciar(*args, log):
    return subprocess.Popen([str(BIN), "-A", "config", *args], cwd=LAB, env=env, stdout=open(LAB / log, "w"),
                            stderr=subprocess.STDOUT, start_new_session=True)


def parar(*ps):
    for p in ps:
        os.killpg(p.pid, signal.SIGTERM)
    for p in ps:
        p.wait(timeout=30)


def linhas(arq, padrao):
    return [l for l in (LAB / arq).read_text().splitlines() if re.search(padrao, l)]


for f in ("celerybeat-schedule", "celerybeat-schedule.db", "beat1.log", "beat2.log", "w4.log"):
    (LAB / f).unlink(missing_ok=True)

print("=== 1) um worker + UM beat (agenda: a tarefa 'pulso' a cada 2 s)")
R.flushdb()
w = iniciar("worker", "-l", "info", "-c", "2", "--without-gossip", "--without-mingle", log="w4.log")
b = iniciar("beat", "-l", "info", "--schedule", str(LAB / "celerybeat-schedule"), log="beat1.log")
time.sleep(11)
parar(b, w)
envios = linhas("beat1.log", r"Sending due task")
execs = linhas("w4.log", r"batimento \d")
print(f"o beat enfileirou {len(envios)} vezes (≈ 1 a cada 2 s em ~10 s) e o worker executou {len(execs)}")
print("horários dos batimentos:", [re.search(r"batimento (\S+)", l).group(1)[:8] for l in execs][:5], "…")

print("\n=== 2) o mesmo, mas com DOIS beats rodando ao mesmo tempo (erro de implantação clássico)")
R.flushdb()
for f in ("celerybeat-schedule", "celerybeat-schedule.db"):
    (LAB / f).unlink(missing_ok=True)
w = iniciar("worker", "-l", "info", "-c", "2", "--without-gossip", "--without-mingle", log="w4.log")
b1 = iniciar("beat", "-l", "info", "--schedule", str(LAB / "celerybeat-schedule-1"), log="beat1.log")
b2 = iniciar("beat", "-l", "info", "--schedule", str(LAB / "celerybeat-schedule-2"), log="beat2.log")
time.sleep(11)
parar(b1, b2, w)
e1, e2 = len(linhas("beat1.log", r"Sending due task")), len(linhas("beat2.log", r"Sending due task"))
execs = linhas("w4.log", r"batimento \d")
print(f"beat 1 enfileirou {e1}, beat 2 enfileirou {e2}; o worker executou {len(execs)} (o dobro do esperado)")
for f in ("celerybeat-schedule", "celerybeat-schedule.db", "celerybeat-schedule-1", "celerybeat-schedule-2", "celerybeat-schedule-1.db", "celerybeat-schedule-2.db"):
    (LAB / f).unlink(missing_ok=True)
