class Campo:
    def __init__(self, tipo, obrigatorio=True, validar=None):
        self.tipo, self.obrigatorio, self.validar = tipo, obrigatorio, validar


class MiniSerializer:
    campos = {}

    def __init__(self, dados):
        self.dados, self.errors, self.validated = dados, {}, {}

    def is_valid(self):
        for nome, campo in self.campos.items():
            if nome not in self.dados:
                if campo.obrigatorio:
                    self.errors[nome] = ["Este campo é obrigatório."]
                continue
            try:
                valor = campo.tipo(self.dados[nome])
            except (TypeError, ValueError):
                self.errors[nome] = [f"Valor inválido para {campo.tipo.__name__}."]
                continue
            if campo.validar and (msg := campo.validar(valor)):
                self.errors[nome] = [msg]
                continue
            self.validated[nome] = valor
        return not self.errors


class ProdutoSer(MiniSerializer):
    campos = {
        "name": Campo(str, validar=lambda v: None if v.strip() else "Não pode ficar em branco."),
        "price": Campo(float, validar=lambda v: None if v > 0 else "Deve ser maior que zero."),
        "stock": Campo(int, obrigatorio=False, validar=lambda v: None if v >= 0 else "Não pode ser negativo."),
    }


for entrada in [{"name": "Mouse", "price": "59.9", "stock": "3"}, {"name": " ", "price": "abc"}, {"price": -1, "stock": -2}]:
    s = ProdutoSer(entrada)
    print(entrada, "→", "ok" if s.is_valid() else s.errors, s.validated if not s.errors else "")
