import hashlib
import json


class ArmazemDeChaves:
    """Chave de idempotência com TTL e detecção de reuso com corpo diferente."""

    def __init__(self, ttl=24 * 3600, relogio=None):
        self.ttl, self.relogio, self.dados = ttl, relogio, {}

    @staticmethod
    def _hash(corpo):
        return hashlib.sha256(json.dumps(corpo, sort_keys=True).encode()).hexdigest()

    def executar(self, usuario, chave, corpo, acao):
        agora = self.relogio()
        registro = self.dados.get((usuario, chave))
        if registro and agora - registro["em"] > self.ttl:
            registro = None                                        # expirou: trata como chave nova
        if registro:
            if registro["hash"] != self._hash(corpo):
                return 422, {"code": "idempotency_key_reuse", "detail": "Esta chave já foi usada com outro conteúdo."}
            return registro["status"], registro["resposta"] | {"replayed": True}
        status, resposta = acao(corpo)
        if status < 400:                                           # só guarda sucesso: falha pode ser repetida
            self.dados[(usuario, chave)] = {"hash": self._hash(corpo), "status": status, "resposta": resposta, "em": agora}
        return status, resposta


t = [0]
armazem = ArmazemDeChaves(ttl=100, relogio=lambda: t[0])
criados = []


def criar(corpo):
    if corpo.get("qtd", 1) <= 0:
        return 400, {"detail": "quantidade inválida"}
    criados.append(corpo)
    return 201, {"id": len(criados), **corpo}


print(armazem.executar("ana", "k1", {"sku": "A", "qtd": 2}, criar))
print(armazem.executar("ana", "k1", {"sku": "A", "qtd": 2}, criar), "← repetição")
print(armazem.executar("ana", "k1", {"sku": "A", "qtd": 9}, criar), "← mesma chave, outro corpo")
print(armazem.executar("bia", "k1", {"sku": "A", "qtd": 2}, criar)[1]["id"], "← outro usuário, mesma chave: pedido novo")
print(armazem.executar("ana", "k2", {"sku": "A", "qtd": 0}, criar), "← falha não é guardada")
print(armazem.executar("ana", "k2", {"sku": "A", "qtd": 1}, criar), "← mesma chave, agora válida")
t[0] = 500
print(armazem.executar("ana", "k1", {"sku": "A", "qtd": 2}, criar), "← depois do TTL: nova execução")
print("pedidos criados:", len(criados))
