"""Princípio de Liskov: um substituto NÃO PODE quebrar o que o contrato promete. O teste de contrato pega o infrator."""
from decimal import Decimal

from apps.orders.domain import ItemCarrinho, ProdutoInfo
from apps.orders.repositories import MemoriaPedidoRepository


def contrato(fabrica):
    """Roda as promessas da porta contra QUALQUER implementação. Devolve a lista de promessas quebradas."""
    quebradas = []
    def checa(nome, fn):
        try:
            if not fn():
                quebradas.append(nome)
        except Exception as e:
            quebradas.append(f"{nome} (levantou {type(e).__name__}: {e})")

    r = fabrica()
    with r.transacao():
        checa("baixar_estoque devolve True quando há estoque", lambda: r.baixar_estoque(1, 5) is True)
        checa("baixar_estoque devolve False quando NÃO há estoque (nunca fica negativo)", lambda: r.baixar_estoque(1, 1) is False)
    r = fabrica()
    checa("travar_produtos ignora ids inexistentes", lambda: set(r.travar_produtos([1, 999])) == {1})
    r = fabrica()
    try:
        with r.transacao():
            r.baixar_estoque(1, 3)
            raise RuntimeError("falha")
    except RuntimeError:
        pass
    checa("a transação desfaz tudo se houver erro", lambda: r.travar_produtos([1])[1].estoque == 5)
    return quebradas


def fabrica_ok():
    return MemoriaPedidoRepository(carrinhos={}, produtos={1: ProdutoInfo(1, "Mouse", Decimal("59.90"), 5, True)})


class Guloso(MemoriaPedidoRepository):
    """VIOLA a pós-condição: aceita baixar mais do que existe (estoque negativo)."""
    def baixar_estoque(self, product_id, quantidade):
        p = self.produtos[product_id]
        self.produtos[product_id] = ProdutoInfo(p.id, p.nome, p.preco, p.estoque - quantidade, p.ativo)
        return True


class SomenteLeitura(MemoriaPedidoRepository):
    """VIOLA o contrato: 'é um repositório', mas não sabe escrever."""
    def baixar_estoque(self, product_id, quantidade):
        raise NotImplementedError("somente leitura")


class SemRollback(MemoriaPedidoRepository):
    """VIOLA a promessa de atomicidade."""
    def transacao(self):
        from contextlib import nullcontext
        return nullcontext()


def com(cls):
    return lambda: cls(carrinhos={}, produtos={1: ProdutoInfo(1, "Mouse", Decimal("59.90"), 5, True)})


for nome, fab in [("MemoriaPedidoRepository (o original)", fabrica_ok), ("Guloso", com(Guloso)),
                  ("SomenteLeitura", com(SomenteLeitura)), ("SemRollback", com(SemRollback))]:
    q = contrato(fab)
    print(f"{nome:<38} → {'cumpre o contrato' if not q else 'QUEBRA ' + str(len(q)) + ' promessa(s)'}")
    for item in q:
        print(f"      ✘ {item}")
