import logging
from datetime import timedelta

from celery import Task, shared_task
from celery.exceptions import MaxRetriesExceededError
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


# --------------------------------------------------------------------------- tarefas AGENDADAS (aula 7.08)
@shared_task(name="orders.cancelar_pedidos_pendentes_antigos")
def cancelar_pedidos_pendentes_antigos(horas=24):
    """Cancela (devolvendo o estoque) pedidos pendentes há mais de `horas`. Idempotente e 'nível': processa TUDO o que está atrasado."""
    from . import services

    limite = timezone.now() - timedelta(hours=horas)
    ids = list(Order.objects.filter(status=Order.Status.PENDING, created_at__lt=limite).values_list("pk", "user_id"))
    cancelados = 0
    for pk, user_id in ids:
        try:
            services.cancel_order(Order.objects.get(pk=pk).user, pk)    # o serviço revalida o status DENTRO da transação
            cancelados += 1
        except services.OrderError:                                      # já foi pago/cancelado por outro caminho: tudo bem
            continue
    logger.info("pendentes_antigos candidatos=%s cancelados=%s", len(ids), cancelados)
    return cancelados


@shared_task(name="orders.limpar_chaves_de_idempotencia")
def limpar_chaves_de_idempotencia(horas=24):
    from .models import IdempotencyKey

    apagadas, _ = IdempotencyKey.objects.filter(created_at__lt=timezone.now() - timedelta(hours=horas)).delete()
    logger.info("chaves_apagadas=%s", apagadas)
    return apagadas


@shared_task(name="orders.batimento")
def batimento():
    logger.info("batimento %s", timezone.now().strftime("%H:%M:%S.%f")[:-3])
    return "ok"


@shared_task(name="orders.reenviar_emails_falhos")
def reenviar_emails_falhos():
    ids = list(EmailLog.objects.filter(status=EmailLog.Status.FAILED).values_list("order_id", flat=True))
    EmailLog.objects.filter(order_id__in=ids, status=EmailLog.Status.FAILED).update(status=EmailLog.Status.PENDING, attempts=0)
    for i in ids:
        send_order_confirmation_email.delay(i)
    return len(ids)
