"""No Django, cada thread tem a SUA conexão com o banco (connections é thread-local)."""
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from django.db import connection, connections
from apps.catalog.models import Product


def consulta(i):
    n = Product.objects.count()                            # abre uma conexão NESTA thread, na primeira consulta
    return threading.current_thread().name, id(connection.connection), n


principal = (threading.current_thread().name, id(connection.connection), Product.objects.count())
print(f"thread principal: {principal[0]} | conexão {principal[1]} | produtos: {principal[2]}")
with ThreadPoolExecutor(4, thread_name_prefix="w") as ex:
    resultados = list(ex.map(consulta, range(12)))         # 12 tarefas em 4 threads
por_thread = defaultdict(set)
for nome, conn, _ in resultados:
    por_thread[nome].add(conn)
for nome in sorted(por_thread):
    print(f"  {nome}: {len(por_thread[nome])} conexão(ões) → {sorted(por_thread[nome])}")
todas = {c for s in por_thread.values() for c in s}
print(f"conexões distintas entre os workers: {len(todas)} | a da principal é uma delas? {principal[1] in todas}")
connections.close_all()
