"""O beat 'recupera' uma execução perdida? Depende de onde fica o arquivo/tabela com o last_run_at."""
import os
import re
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path

LAB = Path(os.environ["LAB"])
BIN = LAB / ".venv/bin/celery"
env = {**os.environ, "BEAT_DEMO": "cron"}
ARQ = LAB / "beat-catchup-schedule"


def limpar():
    for f in LAB.glob("beat-catchup-schedule*"):
        f.unlink()


def beat(log):
    return subprocess.Popen([str(BIN), "-A", "config", "beat", "-l", "info", "--schedule", str(ARQ)], cwd=LAB, env=env,
                            stdout=open(LAB / log, "w"), stderr=subprocess.STDOUT, start_new_session=True)


def parar(p):
    os.killpg(p.pid, signal.SIGTERM); p.wait(timeout=20)


def envios(log):
    return [re.match(r"\[\d{4}-\d{2}-\d{2} (\d\d:\d\d:\d\d)", l).group(1) for l in (LAB / log).read_text().splitlines() if "Sending due task" in l]


def esperar_virada_do_minuto(folga=2):
    agora = datetime.now()
    time.sleep(60 - agora.second - agora.microsecond / 1e6 + folga)


limpar()
print("=== PASSO 1: beat com crontab 'todo minuto' e arquivo de agenda PERSISTENTE; deixa disparar uma vez")
p = beat("bc1.log")
esperar_virada_do_minuto()
parar(p)
print("disparou em:", envios("bc1.log"), "| beat PARADO às", datetime.now().strftime("%H:%M:%S"))

print("\n=== PASSO 2: o beat fica 'fora do ar' durante uma virada de minuto (uma execução perdida)")
esperar_virada_do_minuto()
print("(uma execução deveria ter ocorrido às", datetime.now().strftime("%H:%M:00"), "com o beat desligado)")

print("\n=== PASSO 3a: religa o beat COM o mesmo arquivo de agenda")
p = beat("bc2.log")
time.sleep(6)
parar(p)
print("disparou logo ao subir (recuperou a execução perdida)?", envios("bc2.log") or "NÃO", "| subiu às", datetime.now().strftime("%H:%M:%S"))

print("\n=== PASSO 3b: religa o beat SEM o arquivo (como num contêiner novo depois de um deploy)")
limpar()
p = beat("bc3.log")
time.sleep(6)
parar(p)
print("disparou logo ao subir?", envios("bc3.log") or "NÃO (espera a próxima virada do minuto)")
limpar()
