# 7. Retentativas e idempotência

> ⏱️ ~1h30 · Módulo 7 · Pré-requisitos: [7.04](04-httpx-timeouts-retries.md), [7.06](06-filas-celery.md), [6.01](../06-apis-rest/01-principios-rest.md) e [6.13](../06-apis-rest/13-graphql-grpc-api-completa.md) (idempotência na API), [5.17](../05-django/17-pedidos-estoque-transacao.md) (atualizações atômicas)

> ✅ **Verificação.** Código executado em 2026-11-08 com **Celery 5.7.0**, Redis 8, Django 5.2.19 e um **worker de verdade** (processo separado). **As saídas dos cenários são reais**: o script sobe o worker com `-c 1`, enfileira as mensagens, espera os desfechos e imprime o log do worker. Os horários mostram os intervalos reais do *backoff*. 77 testes do laboratório passaram (6 novos nesta aula).

## 🎯 Objetivos
Ao final desta aula você consegue:
- Explicar por que **retentativa + entrega *at-least-once*** exigem tarefas **idempotentes**, e o que é “efeito exatamente uma vez”
- Configurar retentativas no Celery (`autoretry_for`, `retry_backoff`, `retry_jitter`, `max_retries`) e **separar erro transitório de permanente**
- Tornar uma tarefa idempotente com um **registro de execução** (`EmailLog`) e um **reclamo atômico** (*claim*)
- Tratar a **desistência** (tentativas esgotadas) registrando a falha: a “fila de mortos”
- Testar cada caminho (duplicata, falha transitória, permanente, desistência) com e sem broker

## 🤔 Por que isso importa
Na aula 06 o e-mail virou tarefa, e vimos que o broker **pode entregar a mesma mensagem mais de uma vez** (um worker cai, um *deploy* reinicia). Sem cuidado, o cliente recebe **dois e-mails**; numa tarefa de **cobrança**, ele é **cobrado duas vezes**. Ao mesmo tempo, o mundo falha: o SMTP cai por 5 segundos e a tarefa **deve tentar de novo**, mas sem martelar o serviço doente. Retentativa e idempotência são **um par inseparável**: sem a primeira, perde-se trabalho; sem a segunda, duplica-se.

## 💡 Intuição (explicação simples)
Pense no **“atendente de banco” que recebe um bilhete duplicado**. Cada bilhete tem um número de protocolo. Antes de agir, ele consulta o **livro de registro**: “protocolo 7: já feito?”. Se **sim**, só responde “já está resolvido” (idempotente). Se **ninguém tocou**, **anota seu nome ao lado** (reclama) e faz o serviço; se a luz cai no meio, a anotação **vence com o tempo** e o colega seguinte retoma. Se o cofre está trancado (erro transitório), ele **volta daqui a pouco**, esperando cada vez mais; se o cliente pediu algo impossível (erro permanente), ele **recusa de vez** e anota o motivo em vez de tentar para sempre.

## 🔬 Como funciona por dentro
- **Semântica de entrega:**
  | Garantia | Significa | Preço |
  |---|---|---|
  | *at-most-once* | no máximo uma vez | **pode perder** (se o worker cai, a tarefa some) |
  | ***at-least-once*** | **pelo menos uma vez** (o do Celery com `acks_late`) | **pode duplicar** |
  | *exactly-once* | exatamente uma vez | **não existe** de ponta a ponta numa rede que falha |
  O que se faz na prática é **efeito exatamente uma vez = entrega *at-least-once* + consumidor idempotente**.
- **Idempotente** (aula 6.01): executar **N vezes** produz o mesmo estado que **uma vez**. Técnicas, da mais simples à mais robusta:
  | Técnica | Exemplo | Quando |
  |---|---|---|
  | Operação naturalmente idempotente | `UPDATE pedido SET status='pago'` (e não `total = total + x`) | sempre que possível |
  | **Restrição `UNIQUE`** | `unique(order, kind)` no `EmailLog`; o 2º `INSERT` falha | dedupe simples |
  | **Registro de execução + reclamo atômico** | `UPDATE ... WHERE status='pending'` (só um vence) | efeitos externos (e-mail, cobrança) |
  | **Chave de idempotência do provedor** | `Idempotency-Key` no gateway de pagamento | quando o terceiro suporta |
  | Estado + **versão** (*optimistic lock*) | `WHERE version = N` | atualizações concorrentes |
- **O reclamo (*claim*)** desta aula: `EmailLog` tem uma linha por `(pedido, tipo)` e um *status*: `pending` → `sending` → `sent` (ou `failed`). O trabalhador faz um **`UPDATE ... WHERE status='pending' (ou 'sending' vencido)`**: o banco garante que **só um** `UPDATE` “vence” (devolve 1 linha afetada). Quem não vence **não envia**: o e-mail já foi feito ou outro worker está com ele. É a mesma ideia do `UPDATE ... WHERE stock >= n` da aula 5.17.
- **O reclamo expira (*lease*):** se o worker morrer com o reclamo (`sending`), a mensagem será reentregue, mas ficaria **bloqueada para sempre** se o reclamo não vencesse; por isso reclamos antigos (aqui, 5 min) podem ser retomados. Há uma **janela inevitável**: se o worker cai **depois** de enviar o e-mail e **antes** de marcar `sent`, o e-mail pode sair duas vezes. Para eliminá-la de vez, só com a **chave de idempotência do provedor**; por isso o “exatamente uma vez” é sempre “o melhor possível”.
- **Retentativas no Celery:**
  | Opção | Efeito |
  |---|---|
  | `autoretry_for=(Erro,)` | repete automaticamente **apenas** estes erros |
  | `retry_backoff=1` | espera exponencial: 1 s, 2 s, 4 s… (base em segundos) |
  | `retry_backoff_max=30` | teto da espera |
  | `retry_jitter=True` | sorteia a espera entre 0 e o valor calculado (evita a “manada”, aula 04) |
  | `retry_kwargs={"max_retries": 4}` | **limite** de retentativas |
  | `acks_late=True` | só confirma a mensagem **depois** de executar (sobrevive à queda do worker) |
  | `soft_time_limit` / `time_limit` | levanta `SoftTimeLimitExceeded` / mata a tarefa que passou do tempo |
- **Transitório × permanente:** repetir só adianta se o erro **pode passar** (rede, SMTP indisponível, `503`). `ErroPermanente` (e-mail vazio, dado inválido, bug) **não** entra em `autoretry_for`: falha **uma vez**, é registrado e alguém olha. Repetir um erro permanente gasta recursos e **atrasa** o resto da fila.
- **Desistência (*dead letter*):** depois de `max_retries`, a tarefa **falha de vez**. O gancho `on_failure` marca o `EmailLog` como `failed` e registra o motivo: o MiniShop tem então uma lista consultável de e-mails que **não saíram** (e um alerta possível). Brokers como RabbitMQ e SQS têm **filas de mensagens mortas** (DLQ) nativas (aula 10).
- **Mensagem “venenosa” (*poison message*):** uma mensagem que **sempre** falha (e derruba o worker) entra num laço de reentregas. Defesas: limite de tentativas, `on_failure`, tratar o permanente como definitivo, e monitorar a DLQ.
- **Retentativa dentro da tarefa × reentrega do broker:** `autoretry` **agenda uma nova mensagem** com atraso (`Retry in 2s`); a **reentrega** ocorre quando o worker some sem confirmar. As duas somam-se: **ambas** precisam de idempotência.
- **O que a retentativa não resolve:** carga excessiva do serviço do outro lado (use limites e disjuntor, aula 04), nem erros de lógica (corrija o código).

## 🛠️ Exemplo prático
**1. O registro de execução** (a base da idempotência)
```python
# apps/orders/models.py
class EmailLog(models.Model):
    """Registro de cada e-mail por (pedido, tipo): é o que torna a tarefa IDEMPOTENTE."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        SENDING = "sending", "Enviando"
        SENT = "sent", "Enviado"
        FAILED = "failed", "Falhou"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="emails")
    kind = models.CharField(max_length=40)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    attempts = models.PositiveIntegerField(default=0)
    claimed_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=200, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["order", "kind"], name="emaillog_order_kind_unique")]
```
```bash
uv run python manage.py makemigrations orders -n emaillog && uv run python manage.py migrate
```
**2. A tarefa idempotente, com retentativas e desistência registrada**
```python
# apps/orders/tasks.py
import logging
from datetime import timedelta

from celery import Task, shared_task
from django.core.mail import send_mail
from django.db.models import F, Q
from django.utils import timezone

from .models import EmailLog, Order

logger = logging.getLogger(__name__)
KIND = "order_confirmation"
RECLAMO_EXPIRA = timedelta(minutes=5)


class MarcaFalha(Task):
    """Quando a tarefa DESISTE (erro permanente ou tentativas esgotadas), registra no banco: é a 'fila de mortos' do MiniShop."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        EmailLog.objects.filter(order_id=args[0], kind=KIND).exclude(status=EmailLog.Status.SENT).update(
            status=EmailLog.Status.FAILED, last_error=f"{type(exc).__name__}: {exc}"[:200])
        logger.error("email_desistiu order=%s erro=%s", args[0], exc)


class ErroTransitorio(Exception):
    """Falha que pode passar sozinha (rede, SMTP indisponível): vale repetir."""


class ErroPermanente(Exception):
    """Falha que repetir não conserta (e-mail inválido): não repetir."""


def reclamar(order_id):
    """Tenta ficar com o 'direito' de enviar. Devolve (registro, True) se este worker deve enviar; (registro, False) se não."""
    log, _ = EmailLog.objects.get_or_create(order_id=order_id, kind=KIND)
    agora = timezone.now()
    ganhou = EmailLog.objects.filter(pk=log.pk).filter(
        Q(status=EmailLog.Status.PENDING) | Q(status=EmailLog.Status.SENDING, claimed_at__lt=agora - RECLAMO_EXPIRA)   # ou um reclamo ABANDONADO
    ).update(status=EmailLog.Status.SENDING, claimed_at=agora, attempts=F("attempts") + 1)    # UPDATE atômico: só UM vence
    return log, ganhou == 1


@shared_task(
    bind=True,
    base=MarcaFalha,
    name="orders.send_order_confirmation_email",
    autoretry_for=(ErroTransitorio,),          # só estes erros são repetidos automaticamente
    retry_backoff=1,                           # 1 s, 2 s, 4 s, ... (base do backoff exponencial)
    retry_backoff_max=30,                      # teto
    retry_jitter=True,                         # sorteia a espera entre 0 e o valor calculado
    retry_kwargs={"max_retries": 4},
    acks_late=True,                            # só confirma a mensagem DEPOIS de terminar (sobrevive a worker que cai)
    soft_time_limit=20,
)
def send_order_confirmation_email(self, order_id):
    try:
        order = Order.objects.select_related("user").prefetch_related("items__product").get(pk=order_id)
    except Order.DoesNotExist:
        logger.warning("email_skip order=%s motivo=pedido_inexistente", order_id)
        return "pedido_inexistente"                                   # repetir não faz o pedido aparecer
    log, minha = reclamar(order_id)
    if not minha:
        logger.info("email_skip order=%s status=%s (já enviado ou em andamento)", order_id, log.status)
        return "ja_tratado"                                           # IDEMPOTÊNCIA: a repetição não envia de novo
    try:
        if not order.user.email:
            raise ErroPermanente("usuário sem e-mail")
        linhas = "\n".join(f"- {i.quantity} × {i.product.name}: R$ {i.subtotal}" for i in order.items.all())
        try:
            send_mail(subject=f"MiniShop: pedido #{order.pk} recebido",
                      message=f"Olá, {order.user.username}!\n\nRecebemos o seu pedido #{order.pk}:\n{linhas}\n\nTotal: R$ {order.total}\n",
                      from_email=None, recipient_list=[order.user.email])
        except (ConnectionError, TimeoutError, OSError) as e:        # rede/SMTP: transitório
            raise ErroTransitorio(str(e)) from e
    except ErroTransitorio as e:
        EmailLog.objects.filter(pk=log.pk).update(status=EmailLog.Status.PENDING, last_error=str(e)[:200])   # solta o reclamo
        logger.warning("email_retry order=%s tentativa=%s erro=%s", order_id, self.request.retries + 1, e)
        raise
    except Exception as e:                                            # permanente (ou bug): falha de vez
        EmailLog.objects.filter(pk=log.pk).update(status=EmailLog.Status.FAILED, last_error=str(e)[:200])
        logger.error("email_failed order=%s erro=%s", order_id, e)
        raise
    EmailLog.objects.filter(pk=log.pk).update(status=EmailLog.Status.SENT, sent_at=timezone.now(), last_error="")
    logger.info("email_sent order=%s to=%s", order.pk, order.user.email)
    return "enviado"
```
Leia o fluxo da função: (1) recarrega o pedido; (2) **reclama** o direito de enviar (`UPDATE` atômico); quem perde sai com `"ja_tratado"`; (3) valida; (4) envia, traduzindo falhas de rede em `ErroTransitorio`; (5) em falha transitória **solta o reclamo** (`pending`) e deixa o `autoretry_for` agendar a nova tentativa; (6) em falha permanente marca `failed`; (7) só no fim marca `sent`.

**3. Quatro cenários com um worker de verdade** (`retry_demo.py`; sobe o worker com `-c 1` para a ordem ser legível e controla o SMTP simulado por `EMAIL_FAIL_FIRST`)
```bash
LAB=$PWD uv run python retry_demo.py
```
```text

=== 1) SMTP cai nas 3 primeiras tentativas → retentativas com backoff exponencial + jitter
  15:23:05 Task tarefa[…] received
  15:23:05 email_retry order=1 tentativa=1 erro=SMTP indisponível (falha simulada 1)
  15:23:05 Task tarefa[…] received
  15:23:05 Task tarefa[…] retry: Retry in 0s: ErroTransitorio('SMTP indisponível (falha simulada 1)')
  15:23:05 email_retry order=1 tentativa=2 erro=SMTP indisponível (falha simulada 2)
  15:23:05 Task tarefa[…] received
  15:23:05 Task tarefa[…] retry: Retry in 0s: ErroTransitorio('SMTP indisponível (falha simulada 2)')
  15:23:05 email_retry order=1 tentativa=3 erro=SMTP indisponível (falha simulada 3)
  15:23:05 Task tarefa[…] received
  15:23:05 Task tarefa[…] retry: Retry in 0s: ErroTransitorio('SMTP indisponível (falha simulada 3)')
  15:23:05 email_sent order=1 to=cliente@minishop.local
  15:23:05 Task tarefa[…] succeeded in 0.10320718100410886s: 'enviado'
  → e-mails realmente enviados: 1 | EmailLog: status=sent, tentativas=4, erro=''

=== 2) a mesma mensagem chega 3 vezes → só 1 e-mail (idempotência)
  15:23:10 Task tarefa[…] received
  15:23:10 Task tarefa[…] received
  15:23:10 Task tarefa[…] received
  15:23:10 email_sent order=2 to=cliente@minishop.local
  15:23:10 Task tarefa[…] succeeded in 0.10926880399347283s: 'enviado'
  15:23:10 email_skip order=2 status=sent (já enviado ou em andamento)
  15:23:10 Task tarefa[…] succeeded in 0.003119683009572327s: 'ja_tratado'
  15:23:10 email_skip order=2 status=sent (já enviado ou em andamento)
  15:23:10 Task tarefa[…] succeeded in 0.0032672090164851397s: 'ja_tratado'
  → e-mails realmente enviados: 1 | EmailLog: status=sent, tentativas=1, erro=''

=== 3) erro PERMANENTE (usuário sem e-mail) → não repete, registra a falha
  15:23:15 Task tarefa[…] received
  15:23:15 email_failed order=3 erro=usuário sem e-mail
  15:23:15 email_desistiu order=3 erro=usuário sem e-mail
  15:23:15 Task tarefa[…] raised unexpected: ErroPermanente('usuário sem e-mail')
  → e-mails realmente enviados: 0 | EmailLog: status=failed, tentativas=1, erro='ErroPermanente: usuário sem e-mail'

=== 4) o SMTP nunca volta → esgota as 4 retentativas e desiste
  15:23:20 Task tarefa[…] received
  15:23:20 email_retry order=4 tentativa=1 erro=SMTP indisponível (falha simulada 1)
  15:23:20 Task tarefa[…] received
  15:23:20 Task tarefa[…] retry: Retry in 0s: ErroTransitorio('SMTP indisponível (falha simulada 1)')
  15:23:20 email_retry order=4 tentativa=2 erro=SMTP indisponível (falha simulada 2)
  15:23:20 Task tarefa[…] received
  15:23:20 Task tarefa[…] retry: Retry in 2s: ErroTransitorio('SMTP indisponível (falha simulada 2)')
  15:23:22 email_retry order=4 tentativa=3 erro=SMTP indisponível (falha simulada 3)
  15:23:22 Task tarefa[…] received
  15:23:22 Task tarefa[…] retry: Retry in 2s: ErroTransitorio('SMTP indisponível (falha simulada 3)')
  15:23:24 email_retry order=4 tentativa=4 erro=SMTP indisponível (falha simulada 4)
  15:23:24 Task tarefa[…] received
  15:23:24 Task tarefa[…] retry: Retry in 3s: ErroTransitorio('SMTP indisponível (falha simulada 4)')
  15:23:27 email_retry order=4 tentativa=5 erro=SMTP indisponível (falha simulada 5)
  15:23:27 email_desistiu order=4 erro=SMTP indisponível (falha simulada 5)
  15:23:27 Task tarefa[…] raised unexpected: ErroTransitorio('SMTP indisponível (falha simulada 5)')
  → e-mails realmente enviados: 0 | EmailLog: status=failed, tentativas=5, erro='ErroTransitorio: SMTP indisponível (falha simulada 5)'
```
Como ler:
1. **SMTP cai nas 3 primeiras tentativas.** Cada falha gera um `retry: Retry in Ns` e uma **nova mensagem** agendada; a **4ª tentativa envia**. Resultado: **1 e-mail**, `EmailLog` `sent` com **4 tentativas**. O valor de `N` é **sorteado** (*jitter*) entre 0 e o limite exponencial (1 s, 2 s, 4 s, ...), então **muda a cada execução**: em uma execução anterior os atrasos foram 1 s, 2 s e 2 s (horários `:12`, `:13`, `:15`, `:17`); na execução impressa acima foram todos baixos. O que **não** muda é o limite crescente e o desfecho: em algum momento o SMTP volta e **exatamente um** e-mail sai.
2. **A mesma mensagem 3 vezes** (simulando reentregas): o 1º `received` **enviou**; os outros dois fizeram `email_skip ... status=sent` e terminaram em milissegundos com `'ja_tratado'`. **Um só e-mail**, `tentativas=1`. É a idempotência funcionando.
3. **Erro permanente** (usuário sem e-mail): **uma** execução, sem nenhum “Retry”: `email_failed`, `email_desistiu`, `EmailLog` = `failed` com o motivo. Repetir não adiantaria.
4. **O SMTP nunca volta**: cinco tentativas (a 1ª e as **4 retentativas** permitidas), com esperas sorteadas sob tetos de 1 s, 2 s, 4 s e 8 s, e então a **desistência**: `raised unexpected: ErroTransitorio` e o `on_failure` marcando `failed` com o último erro. O `EmailLog` fica como uma **lista de e-mails que não saíram**, pronta para um alerta ou reprocessamento manual.

**4. O reclamo com prazo, em Python puro** (`claim.py`: relógio injetado)
```python
class Reclamos:
    """Consumidor idempotente com 'reclamo' (lease): quem reclama a mensagem tem prazo para terminar; se sumir, outro assume."""

    def __init__(self, prazo, relogio):
        self.prazo, self.relogio, self.estado = prazo, relogio, {}      # id -> {"status", "desde", "dono"}

    def reclamar(self, mid, worker):
        reg = self.estado.get(mid)
        agora = self.relogio()
        if reg is None or reg["status"] == "livre" or (reg["status"] == "reclamado" and agora - reg["desde"] >= self.prazo):
            self.estado[mid] = {"status": "reclamado", "desde": agora, "dono": worker}      # este worker pode agir
            return True
        return False                                                    # já feita, ou outro worker está com ela

    def concluir(self, mid, worker):
        if self.estado.get(mid, {}).get("dono") == worker:
            self.estado[mid]["status"] = "feito"

    def soltar(self, mid, worker):                                      # falha transitória: devolve para tentar de novo
        if self.estado.get(mid, {}).get("dono") == worker:
            self.estado[mid]["status"] = "livre"


t = [0]
r = Reclamos(prazo=10, relogio=lambda: t[0])
efeitos = []


def processar(worker, mid, cai=False, falha=False):
    if not r.reclamar(mid, worker):
        print(f"t={t[0]:>2} {worker}: mensagem {mid} → ignorada (já feita ou com outro worker)")
        return
    if cai:
        print(f"t={t[0]:>2} {worker}: reclamou {mid} e CAIU no meio (sem concluir nem soltar)")
        return
    if falha:
        r.soltar(mid, worker)
        print(f"t={t[0]:>2} {worker}: falha transitória em {mid} → soltou o reclamo para a próxima tentativa")
        return
    efeitos.append((worker, mid))
    r.concluir(mid, worker)
    print(f"t={t[0]:>2} {worker}: processou {mid} (efeito aplicado) e concluiu")


processar("A", "m1")                      # normal
processar("B", "m1")                      # duplicata da mesma mensagem
processar("A", "m2", falha=True)          # falha transitória
processar("B", "m2")                      # a nova tentativa funciona
processar("A", "m3", cai=True)            # A morre com m3 reclamada
t[0] = 4;  processar("B", "m3")           # cedo demais: o reclamo de A ainda vale
t[0] = 11; processar("B", "m3")           # reclamo expirou: B assume
print("efeitos aplicados:", efeitos, "→ cada mensagem teve efeito exatamente UMA vez")
```
```text
t= 0 A: processou m1 (efeito aplicado) e concluiu
t= 0 B: mensagem m1 → ignorada (já feita ou com outro worker)
t= 0 A: falha transitória em m2 → soltou o reclamo para a próxima tentativa
t= 0 B: processou m2 (efeito aplicado) e concluiu
t= 0 A: reclamou m3 e CAIU no meio (sem concluir nem soltar)
t= 4 B: mensagem m3 → ignorada (já feita ou com outro worker)
t=11 B: processou m3 (efeito aplicado) e concluiu
efeitos aplicados: [('A', 'm1'), ('B', 'm2'), ('B', 'm3')] → cada mensagem teve efeito exatamente UMA vez
```
Cada mensagem teve efeito **exatamente uma vez**: a duplicata de `m1` foi ignorada; a falha transitória de `m2` **soltou** o reclamo e a nova tentativa funcionou; o worker A **caiu** com `m3` reclamada e, em `t=4`, B ainda **não podia** (o reclamo valia 10 s); em `t=11` o reclamo venceu e B assumiu. É a mesma lógica do `EmailLog`, sem o banco.

**5. Testes (executados)**
```python
# tests/test_email_idempotente.py (trechos)
def test_executar_duas_vezes_envia_um_email(pedido):
    assert send_order_confirmation_email(pedido.pk) == "enviado"
    assert send_order_confirmation_email(pedido.pk) == "ja_tratado"          # a repetição não faz nada
    assert len(mail.outbox) == 1
    log = EmailLog.objects.get(order=pedido)
    assert (log.status, log.attempts) == ("sent", 1)


def test_pedido_inexistente_nao_repete(db):
    assert send_order_confirmation_email(999999) == "pedido_inexistente"


def test_sem_email_e_erro_permanente(pedido):
    pedido.user.email = ""
    pedido.user.save()
    with pytest.raises(Exception, match="sem e-mail"):
        send_order_confirmation_email(pedido.pk)
    assert EmailLog.objects.get(order=pedido).status == "failed" and len(mail.outbox) == 0
```
```bash
uv run pytest -q
```
```text
77 passed
```
Os 6 testes novos (os três acima, mais os de falha transitória, de “nova tentativa depois da falha” e do reenvio manual) cobrem **todos os caminhos** da tarefa **sem broker e sem esperar**: a tarefa é uma função que se pode chamar diretamente. O teste com o worker real é o `retry_demo.py`, que prova o que a chamada direta não prova (o *backoff* real e a reentrega pelo broker).

## 🧠 Pausa para lógica
**Problema (consumidor idempotente com reclamo).** Implemente `Reclamos(prazo, relogio)` com `reclamar(mid, worker)`, `concluir(mid, worker)` e `soltar(mid, worker)`. Regras: só **um** worker consegue reclamar uma mensagem; uma mensagem `feita` nunca é reprocessada; `soltar` a devolve para novas tentativas; e um reclamo **abandonado** (passou do `prazo`) pode ser **retomado** por outro worker. Simule: duplicata, falha transitória e um worker que cai.

<details><summary>Dica</summary>
Guarde por mensagem <code>{"status", "desde", "dono"}</code>. <code>reclamar</code> concede o direito se não há registro, se está <code>livre</code> ou se está <code>reclamado</code> há mais de <code>prazo</code>. <code>concluir</code> e <code>soltar</code> só valem para o <code>dono</code> atual.
</details>

<details><summary>Solução comentada</summary>

É o `claim.py` do exemplo 4 (executado). No banco, cada linha do dicionário é uma linha do `EmailLog`, e o `if` de `reclamar` vira um **`UPDATE ... WHERE`** (a atomicidade vem do banco, não de um `if` em Python): sem isso, dois workers poderiam ambos “achar que ganharam”, a mesma corrida das aulas 02 e 5.17. Observe a verificação de **dono** em `concluir`/`soltar`: um worker que perdeu o reclamo (venceu o prazo) não pode, tarde demais, marcar a mensagem como feita.
</details>

## ⚠️ Erros comuns e boas práticas
| Mensagem / sintoma | Causa | Solução |
|---|---|---|
| E-mail/cobrança duplicados após *deploy* ou queda | Tarefa não idempotente + reentrega | Registro de execução + reclamo atômico |
| Tarefa repete para sempre um erro inútil | `autoretry_for=(Exception,)` | Só erros **transitórios**; permanentes falham de vez |
| Todos os clientes retomam no mesmo segundo | Backoff sem *jitter* | `retry_jitter=True` |
| Fila entupida de tentativas | Muitas retentativas, espera curta, sem teto | `max_retries`, `retry_backoff_max` e disjuntor (aula 04) |
| `MaxRetriesExceededError` sem rastro | Desistência sem registro | `on_failure` gravando o motivo/alertando |
| Mensagem perdida quando o worker cai | `acks_late=False` (confirma ao receber) | `acks_late=True` (com tarefa idempotente) |
| Reclamo “preso” em `sending` | Worker morreu e o reclamo nunca expira | Prazo (*lease*) e reclamo retomável |
| Dois workers “ganham” o reclamo | `if` em Python (ler e depois gravar) | `UPDATE ... WHERE` atômico (ou `select_for_update`) |
| `INSERT` duplicado → `IntegrityError` na 2ª execução | `create()` sem tratar a restrição | `get_or_create`/`update_or_create` ou capturar `IntegrityError` |
| Tarefa idempotente “na teoria”, mas o provedor cobra duas vezes | Janela entre enviar e marcar | Chave de idempotência **do provedor** (`Idempotency-Key`) |
| `SoftTimeLimitExceeded` | Tarefa passou do tempo | Tratar e limpar; revisar *timeouts* das chamadas internas |
| Teste só no caminho feliz | Retentativa/duplicata sem teste | Um teste por caminho (duplicata, transitório, permanente, esgotado) |

- **Regra de ouro:** *toda* tarefa assume que **pode rodar de novo**, **fora de ordem** e **concorrentemente com uma cópia de si mesma**.
- **Operações idempotentes por natureza** (definir um estado) são preferíveis a incrementais (somar).
- **Efeito externo** (e-mail, pagamento) = registro **antes**/depois + chave do provedor quando existir.
- Registre **tentativas, erro e horário**: sem isso, diagnosticar “por que o e-mail não chegou” vira adivinhação.
- Alerte sobre **fila crescendo** e **muitas tarefas em `failed`**; revise a “fila de mortos” periodicamente.
- Repetir é caro: o *backoff* existe para **proteger o serviço doente**, não só para “dar um tempo”.

## 🧩 Exercícios
**1. Fixação**
(a) Por que *exactly-once* “puro” não existe e o que se faz no lugar? (b) Qual a diferença entre erro transitório e permanente e o que fazer com cada um? (c) Por que o reclamo é um `UPDATE ... WHERE` e não um `if` em Python? (d) Por que o reclamo precisa de prazo?

<details><summary>Solução</summary>

(a) Em redes que falham, o remetente nunca sabe se a mensagem chegou e foi processada; garante-se *at-least-once* e torna-se o consumidor **idempotente** para obter efeito único. (b) Transitório pode passar (rede, 503): repetir com *backoff*; permanente não (dado inválido): falhar de vez e registrar. (c) O `UPDATE ... WHERE` é atômico no banco, então só um worker o vence; com `if`, dois workers podem ler “livre” e ambos agir. (d) Se o worker cair com o reclamo, a mensagem reentregue ficaria bloqueada para sempre; o prazo permite retomar.
</details>

**2. Aplicação no projeto MiniShop**
Torne o e-mail de confirmação **confiável**.

Critérios de pronto:
- [ ] `EmailLog` (pedido, tipo, status, tentativas, erro) com `UNIQUE(order, kind)` e migração
- [ ] Tarefa com **reclamo atômico**, `autoretry_for` (só transitórios), `retry_backoff`, `retry_jitter`, `max_retries=4` e `acks_late=True`
- [ ] Erro **permanente** (usuário sem e-mail) não repete; esgotamento das tentativas marca `failed` (`on_failure`)
- [ ] Um comando `manage.py reenviar_emails_falhos` que recoloca `failed` na fila (e um teste)
- [ ] Testes: duplicata (1 e-mail), pedido inexistente, falha transitória, permanente e reenvio manual
- [ ] Uma execução com **worker real** (`-c 1`) e SMTP falhando, com o log e a tabela de tentativas em `docs/retentativas.md`
- [ ] Commit `feat(orders): idempotent email task with retries and failure log`

<details><summary>Solução de referência (reenvio manual)</summary>

```python
# apps/orders/management/commands/reenviar_emails_falhos.py
from django.core.management.base import BaseCommand

from apps.orders.models import EmailLog
from apps.orders.tasks import send_order_confirmation_email


class Command(BaseCommand):
    help = "Recoloca na fila os e-mails que falharam (depois de corrigir a causa)."

    def handle(self, *args, **opts):
        ids = list(EmailLog.objects.filter(status=EmailLog.Status.FAILED).values_list("order_id", flat=True))
        EmailLog.objects.filter(order_id__in=ids, status=EmailLog.Status.FAILED).update(status=EmailLog.Status.PENDING, attempts=0)
        for i in ids:
            send_order_confirmation_email.delay(i)
        self.stdout.write(f"{len(ids)} e-mail(s) reenfileirado(s)")
```
</details>

**3. Desafio (opcional)**
Elimine a **janela** entre “enviar” e “marcar `sent`” usando um identificador estável por mensagem (por exemplo, o cabeçalho `Message-ID` derivado de `(pedido, tipo)`) e um provedor que **deduplica** por esse identificador. Escreva um provedor falso que simula isso e um teste que derruba o worker **depois** do envio e mostra que o cliente continua recebendo **um** e-mail.

## 🎤 Na entrevista
- **O que é idempotência e por que importa em filas?** Executar a mesma operação várias vezes tem o mesmo efeito que uma; importa porque filas entregam *pelo menos uma vez* e workers/redes falham, então reentregas e retentativas acontecem; sem idempotência, há e-mails e cobranças duplicadas.
- **Como tornar uma tarefa idempotente?** Registrar a execução por uma chave estável (`UNIQUE`), “reclamar” o trabalho com uma atualização atômica, usar operações de estado (e não incrementais) e, para terceiros, a chave de idempotência do provedor.
- **Como configurar retentativas com o Celery?** `autoretry_for` com erros transitórios, `retry_backoff` + `retry_jitter`, `max_retries`, `acks_late`, e `on_failure` para tratar a desistência; erros permanentes não são repetidos.
- **O que é uma *dead letter queue*?** Uma fila para mensagens que **esgotaram as tentativas** ou são inválidas, permitindo inspeção e reprocessamento sem bloquear a fila principal.
- **Exatamente uma vez existe?** Não de ponta a ponta; obtém-se o **efeito** exatamente uma vez combinando entrega *at-least-once* com consumidores idempotentes.

## 📚 Para ir além
- 📄 Documentação: [Celery — Retentativas](https://docs.celeryq.dev/en/stable/userguide/tasks.html#retrying). `retry`, `autoretry_for`, `retry_backoff`, `retry_jitter`.
- 📄 Documentação: [Celery — `acks_late`](https://docs.celeryq.dev/en/stable/userguide/tasks.html#Task.acks_late). O que muda quando o worker cai.
- 📄 Documentação: [Celery — FAQ](https://docs.celeryq.dev/en/stable/faq.html). Idempotência, `acks_late` e “a tarefa rodou duas vezes”.
- 📄 Documentação: [Celery — chamando tarefas](https://docs.celeryq.dev/en/stable/userguide/calling.html). `apply_async`, `countdown`, `eta`, `expires`.
- 📄 Documentação oficial: [Django — `update_or_create`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#update-or-create). Operações idempotentes de escrita.
- 📑 Artigo/tutorial: [Brandur — Implementing Stripe-like idempotency keys in Postgres](https://brandur.org/idempotency-keys). Um projeto completo e cuidadoso (em inglês).
- 📑 Artigo/tutorial: [Stripe — Requisições idempotentes](https://docs.stripe.com/api/idempotent_requests). A chave de idempotência do lado do provedor.
- 📑 Artigo/tutorial: [AWS Builders' Library — Timeouts, retries and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/). A teoria do *backoff* (em inglês).
- 🏋️ Prática extra: mate o worker com `kill -9` no meio de uma tarefa lenta e observe a mensagem ser reentregue (com `acks_late=True`) e o reclamo evitar o envio duplo.

> Links verificados em 2026-11-08 (HTTP 200).

## ✅ Checklist da aula
- [ ] Sei por que *at-least-once* + retentativa exigem idempotência
- [ ] A tarefa reclama o trabalho com um `UPDATE` atômico e ignora duplicatas
- [ ] Separei erros transitórios (com *backoff* e *jitter*) de permanentes
- [ ] A desistência é registrada (`failed`) e há como reenviar
- [ ] Vi os quatro cenários com um worker real e testei cada caminho
