"""RabbitMQ na prática (pika): fila de trabalho, ack, reentrega, exchange 'topic', fila de mortos e confirmação de publicação."""
import threading
import time

import pika
from pika.exceptions import UnroutableError

PARAMS = pika.ConnectionParameters("127.0.0.1", 5680, heartbeat=30)


def conectar():
    c = pika.BlockingConnection(PARAMS)
    return c, c.channel()


def limpar(*filas, trocas=()):
    c, ch = conectar()
    for f in filas:
        ch.queue_delete(f)
    for t in trocas:
        ch.exchange_delete(t)
    c.close()


# ------------------------------------------------------------------ 1) fila de trabalho: consumidores concorrentes
def fila_de_trabalho(prefetch):
    limpar("tarefas")
    c, ch = conectar()
    ch.queue_declare("tarefas", durable=True)                         # sobrevive a reinício do broker
    for i in range(1, 11):
        ch.basic_publish("", "tarefas", f"tarefa-{i}".encode(), pika.BasicProperties(delivery_mode=2))   # 2 = mensagem persistente
    c.close()
    feitas = {"rapido": [], "lento": []}

    def consumidor(nome, duracao):
        cc, cch = conectar()
        if prefetch:
            cch.basic_qos(prefetch_count=prefetch)                      # "só me dê N mensagens não confirmadas por vez"
        for metodo, props, corpo in cch.consume("tarefas", inactivity_timeout=1):
            if metodo is None:
                break
            time.sleep(duracao)                                         # processa
            feitas[nome].append(corpo.decode())
            cch.basic_ack(metodo.delivery_tag)                          # CONFIRMA só depois de terminar
        cc.close()

    ts = [threading.Thread(target=consumidor, args=("rapido", 0.05)), threading.Thread(target=consumidor, args=("lento", 0.3))]
    [t.start() for t in ts]; [t.join() for t in ts]
    return {k: len(v) for k, v in feitas.items()}


print("--- 1) fila de trabalho, 2 consumidores (um rápido, um lento), 10 mensagens")
print("sem prefetch (o broker empurra TUDO para quem conectou primeiro):", fila_de_trabalho(prefetch=0))
print("com prefetch=1 (cada consumidor só recebe a próxima quando confirma a atual):  ", fila_de_trabalho(prefetch=1))

# ------------------------------------------------------------------ 2) ack e reentrega
print("\n--- 2) consumidor A recebe a mensagem e CAI antes do ack")
limpar("pagamentos")
c, ch = conectar(); ch.queue_declare("pagamentos", durable=True)
ch.basic_publish("", "pagamentos", b"cobrar pedido #7", pika.BasicProperties(delivery_mode=2)); c.close()
ca, cha = conectar()
metodo, props, corpo = cha.basic_get("pagamentos", auto_ack=False)
print(f"A recebeu {corpo.decode()!r} (redelivered={metodo.redelivered}) e vai cair sem confirmar...")
ca.close()                                                             # conexão cai: sem ack
time.sleep(0.5)
cb, chb = conectar()
metodo, props, corpo = chb.basic_get("pagamentos", auto_ack=False)
print(f"B recebeu {corpo.decode()!r} (redelivered={metodo.redelivered})  ← o broker devolveu a mensagem para a fila")
chb.basic_ack(metodo.delivery_tag); cb.close()

# ------------------------------------------------------------------ 3) exchange topic (publicar/assinar)
print("\n--- 3) exchange 'topic': UM evento publicado, vários interessados, cada um com a sua fila")
limpar("q.email", "q.estoque", "q.auditoria", trocas=("minishop.eventos",))
c, ch = conectar()
ch.exchange_declare("minishop.eventos", exchange_type="topic", durable=True)
for fila, padrao in (("q.email", "order.paid"), ("q.estoque", "order.*"), ("q.auditoria", "#")):
    ch.queue_declare(fila, durable=True)
    ch.queue_bind(fila, "minishop.eventos", routing_key=padrao)
    print(f"  fila {fila:<12} assina o padrão {padrao!r}")
for chave in ("order.created", "order.paid", "order.cancelled", "payment.failed"):
    ch.basic_publish("minishop.eventos", chave, chave.encode())
for fila in ("q.email", "q.estoque", "q.auditoria"):
    ch.queue_declare(fila, passive=True)
    recebidas = []
    while True:
        m, p, b = ch.basic_get(fila, auto_ack=True)
        if m is None:
            break
        recebidas.append(b.decode())
    print(f"  {fila:<12} recebeu: {recebidas}")
c.close()

# ------------------------------------------------------------------ 4) fila de mortos
print("\n--- 4) fila de mortos (dead letter): uma mensagem 'venenosa' é rejeitada sem reentrega")
limpar("emails", "emails.mortos", trocas=("minishop.mortos",))
c, ch = conectar()
ch.exchange_declare("minishop.mortos", exchange_type="fanout", durable=True)
ch.queue_declare("emails.mortos", durable=True); ch.queue_bind("emails.mortos", "minishop.mortos")
ch.queue_declare("emails", durable=True, arguments={"x-dead-letter-exchange": "minishop.mortos", "x-message-ttl": 3000})
ch.basic_publish("", "emails", b"e-mail com dados invalidos"); ch.basic_publish("", "emails", b"e-mail normal")
m, p, b = ch.basic_get("emails")
ch.basic_nack(m.delivery_tag, requeue=False)                           # "não consigo processar e não adianta repetir": vai para os mortos
m, p, b = ch.basic_get("emails"); ch.basic_ack(m.delivery_tag)         # a mensagem normal é processada
m, p, b = ch.basic_get("emails.mortos", auto_ack=True)
motivo = p.headers["x-death"][0]
print(f"na fila de mortos: {b.decode()!r} | motivo: {motivo['reason']} | fila de origem: {motivo['queue']}")
ch.basic_publish("", "emails", b"mensagem que ninguem consumiu")
print("outra mensagem fica 3 s na fila (TTL) sem consumidor, expira e também vai para os mortos...")
time.sleep(3.5)
m, p, b = ch.basic_get("emails.mortos", auto_ack=True)
print(f"na fila de mortos: {b.decode()!r} | motivo: {p.headers['x-death'][0]['reason']}")
c.close()

# ------------------------------------------------------------------ 5) confirmação de publicação
print("\n--- 5) confirmação do publicador: como saber que o broker REALMENTE aceitou e roteou a mensagem?")
c, ch = conectar()
ch.confirm_delivery()
ch.exchange_declare("sem_destino", exchange_type="direct")
try:
    ch.basic_publish("sem_destino", "ninguem", b"evento perdido", mandatory=True)
    print("publicou (sem erro)")
except UnroutableError:
    print("UnroutableError: o broker recebeu, mas NENHUMA fila estava ligada, e devolveu (mandatory=True)")
ch.queue_declare("destino", durable=True); ch.queue_bind("destino", "sem_destino", routing_key="chave")
ch.basic_publish("sem_destino", "chave", b"evento entregue", mandatory=True)
print("com uma fila ligada à chave: publicado e confirmado sem erro")
c.close()
limpar("tarefas", "pagamentos", "q.email", "q.estoque", "q.auditoria", "emails", "emails.mortos", "destino",
       trocas=("minishop.eventos", "minishop.mortos", "sem_destino"))
