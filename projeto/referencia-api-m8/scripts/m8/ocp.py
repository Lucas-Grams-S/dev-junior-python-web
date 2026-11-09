"""Aberto para extensão, fechado para modificação: adicionar uma forma de pagamento SEM editar o código existente."""
from decimal import Decimal

D = Decimal


# ---------------------------------------------------------------- ANTES: if/elif (cada novidade EDITA esta função)
def desconto_antes(forma, total):
    if forma == "pix":
        return total * D("0.05")
    elif forma == "cartao":
        return D("0")
    elif forma == "boleto":
        return D("-2.50")                       # na verdade uma taxa de R$ 2,50
    else:
        raise ValueError(f"forma de pagamento inválida: {forma}")


# ---------------------------------------------------------------- DEPOIS: estratégias registradas
REGRAS = {}


def forma_de_pagamento(nome):
    def registrar(fn):
        REGRAS[nome] = fn
        return fn
    return registrar


@forma_de_pagamento("pix")
def _pix(total):
    return total * D("0.05")


@forma_de_pagamento("cartao")
def _cartao(total):
    return D("0")


@forma_de_pagamento("boleto")
def _boleto(total):
    return D("-2.50")


def desconto(forma, total):                      # NÃO muda nunca mais
    try:
        return REGRAS[forma](total)
    except KeyError:
        raise ValueError(f"forma de pagamento inválida: {forma}") from None


# 1) o comportamento é IDÊNTICO ao de antes?
casos = [(f, D(t)) for f in ("pix", "cartao", "boleto") for t in ("10.00", "199.99", "1234.56")]
iguais = all(desconto_antes(f, t) == desconto(f, t) for f, t in casos)
print(f"equivalência em {len(casos)} casos (3 formas × 3 totais): {iguais}")
for f in ("pix", "cartao", "boleto"):
    print(f"  {f:<7} sobre R$ 200,00 → desconto {desconto(f, D('200')):>7}")
try:
    desconto("cheque", D("10"))
except ValueError as e:
    print("forma desconhecida →", e)

# 2) EXTENSÃO: um módulo NOVO acrescenta a forma 'fidelidade', sem tocar em `desconto` nem nas outras
@forma_de_pagamento("fidelidade")
def _fidelidade(total):
    return total * D("0.03")


print("\napós registrar 'fidelidade' em OUTRO lugar do código:")
print("  formas conhecidas:", sorted(REGRAS))
print(f"  fidelidade sobre R$ 200,00 → desconto {desconto('fidelidade', D('200'))}  (nenhuma linha existente foi editada)")
