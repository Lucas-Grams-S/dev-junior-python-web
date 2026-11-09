"""Idempotência de POST (Idempotency-Key), independente de HTTP: recebe uma função que executa a operação e devolve (status, corpo)."""
from django.db import IntegrityError, transaction

from .models import IdempotencyKey


def executar_idempotente(user, chave, operacao):
    """Devolve (status, corpo, repetida). `operacao()` roda UMA vez por (usuário, chave); a repetição devolve o resultado guardado."""
    anterior = IdempotencyKey.objects.filter(user=user, key=chave).first()
    if anterior:
        return anterior.response_status, anterior.response_body, True
    try:
        with transaction.atomic():                                  # a operação e o registro da chave: tudo ou nada
            status, corpo = operacao()
            IdempotencyKey.objects.create(user=user, key=chave, response_status=status, response_body=corpo)
        return status, corpo, False
    except IntegrityError:                                          # outra requisição com a mesma chave ganhou a corrida
        anterior = IdempotencyKey.objects.get(user=user, key=chave)
        return anterior.response_status, anterior.response_body, True
