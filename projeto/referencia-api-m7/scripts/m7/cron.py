"""Um interpretador de cron de 5 campos (min hora dia mês dia_da_semana), verificado contra o crontab do Celery."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def campo(texto, minimo, maximo):
    """'*/15' → {0,15,30,45}; '1-5' → {1..5}; '0,30' → {0,30}; '*' → todos; '10-20/5' → {10,15,20}"""
    valores = set()
    for parte in texto.split(","):
        faixa, barra, passo = parte.partition("/")
        passo = int(passo) if barra else 1
        if faixa == "*":
            ini, fim = minimo, maximo
        elif "-" in faixa:
            ini, fim = (int(x) for x in faixa.split("-"))
        else:
            ini = int(faixa)
            fim = maximo if barra else ini                      # "5/10" = a partir do 5, de 10 em 10
        valores |= set(range(ini, fim + 1, passo))
    return valores


class Cron:
    def __init__(self, expr):
        m, h, dom, mon, dow = expr.split()
        self.min, self.hora = campo(m, 0, 59), campo(h, 0, 23)
        self.dia, self.mes = campo(dom, 1, 31), campo(mon, 1, 12)
        self.sem = {d % 7 for d in campo(dow, 0, 7)}          # 0 e 7 = domingo
        self.dia_livre, self.sem_livre = dom == "*", dow == "*"

    def casa(self, dt):
        dow = (dt.weekday() + 1) % 7                           # segunda=0 → domingo=0
        if dt.minute not in self.min or dt.hour not in self.hora or dt.month not in self.mes:
            return False
        if self.dia_livre or self.sem_livre:                   # um dos dois é "*": vale o outro
            return dt.day in self.dia and dow in self.sem
        return dt.day in self.dia or dow in self.sem           # os dois definidos: vale QUALQUER um (regra clássica do cron)

    def proximas(self, desde, n=3):
        dt = desde.replace(second=0, microsecond=0) + timedelta(minutes=1)
        achadas = []
        while len(achadas) < n:
            if self.casa(dt):
                achadas.append(dt)
            dt += timedelta(minutes=1)
        return achadas


if __name__ == "__main__":
    from celery.schedules import crontab

    inicio = datetime(2026, 11, 8, 15, 27, tzinfo=timezone.utc)          # domingo
    casos = {
        "*/15 * * * *": dict(minute="*/15"),
        "0 3 * * *": dict(minute=0, hour=3),
        "5 * * * *": dict(minute=5),
        "30 8 * * 1-5": dict(minute=30, hour=8, day_of_week="1-5"),
        "0 9 1 * *": dict(minute=0, hour=9, day_of_month=1),
        "0,30 */6 * * *": dict(minute="0,30", hour="*/6"),
    }
    print(f"agora (UTC): {inicio:%Y-%m-%d %H:%M} ({['seg','ter','qua','qui','sex','sáb','dom'][inicio.weekday()]})")
    todos_batem = True
    for expr, kwargs in casos.items():
        minhas = Cron(expr).proximas(inicio, 3)
        celery_prox = inicio + crontab(**kwargs).remaining_delta(inicio)[1]     # próxima execução segundo o Celery
        bate = minhas[0] == celery_prox
        todos_batem &= bate
        print(f"{expr:<16} → " + " | ".join(f"{d:%a %d/%m %H:%M}" for d in minhas) + f"   {'✔ igual ao Celery' if bate else '✘ DIFERE: ' + str(celery_prox)}")
    print("todas as primeiras execuções coincidem com o crontab do Celery:", todos_batem)

    print("\nFUSO HORÁRIO: '02:30' em Nova York no dia em que o horário de verão começa (2026-03-08)")
    ny = ZoneInfo("America/New_York")
    d = datetime(2026, 3, 8, 2, 30, tzinfo=ny)
    ida_e_volta = d.astimezone(timezone.utc).astimezone(ny)
    print(f"  datetime(2026-03-08 02:30, NY) → em UTC: {d.astimezone(timezone.utc):%H:%M} → de volta a NY: {ida_e_volta:%H:%M}  (02:30 NÃO EXISTE nesse dia)")
    print("  → um job 'todo dia às 02:30 locais' pularia (ou duplicaria, no outono) nesse dia. Em UTC não há saltos.")
