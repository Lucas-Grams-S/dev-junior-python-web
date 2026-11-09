class Permissao:
    def tem(self, usuario, objeto=None):
        raise NotImplementedError

    def __and__(self, outra):
        return _Op(lambda u, o: self.tem(u, o) and outra.tem(u, o))

    def __or__(self, outra):
        return _Op(lambda u, o: self.tem(u, o) or outra.tem(u, o))

    def __invert__(self):
        return _Op(lambda u, o: not self.tem(u, o))


class _Op(Permissao):
    def __init__(self, fn):
        self.fn = fn

    def tem(self, usuario, objeto=None):
        return self.fn(usuario, objeto)


class Autenticado(Permissao):
    def tem(self, usuario, objeto=None):
        return usuario is not None


class TemPerm(Permissao):
    def __init__(self, codigo):
        self.codigo = codigo

    def tem(self, usuario, objeto=None):
        return usuario is not None and (usuario.get("superuser") or self.codigo in usuario["perms"])


class Dono(Permissao):
    def tem(self, usuario, objeto=None):
        return usuario is not None and objeto is not None and objeto["dono"] == usuario["id"]


cancelar = Autenticado() & Dono()                                   # só o dono
ver = Autenticado() & (Dono() | TemPerm("orders.view_order"))       # dono OU atendimento
excluir = TemPerm("orders.delete_order") & ~Dono()                  # quem tem a permissão, exceto o próprio dono

pedido = {"id": 7, "dono": 1}
atores = {"anônimo": None, "dono": {"id": 1, "perms": set()}, "atendimento": {"id": 2, "perms": {"orders.view_order"}},
          "super": {"id": 3, "perms": set(), "superuser": True}}
print(f"{'ator':<12} {'ver':<6} {'cancelar':<9} {'excluir'}")
for nome, u in atores.items():
    print(f"{nome:<12} {ver.tem(u, pedido)!s:<6} {cancelar.tem(u, pedido)!s:<9} {excluir.tem(u, pedido)}")
