import json
from datetime import datetime, timezone
from decimal import Decimal

preco = Decimal("59.90")
try:
    json.dumps({"price": preco})
except TypeError as e:
    print("Decimal direto no JSON →", type(e).__name__, ":", e)

print("float no JSON    :", json.dumps({"total": 0.1 + 0.2}))          # erro de ponto flutuante vai para o cliente
print("string decimal   :", json.dumps({"total": str(Decimal("0.1") + Decimal("0.2"))}))
print("centavos inteiros:", json.dumps({"total_cents": 30}))

agora = datetime(2026, 11, 8, 14, 30, tzinfo=timezone.utc)
print("data ISO 8601    :", json.dumps({"created_at": agora.isoformat().replace("+00:00", "Z")}))
print("data ambígua     :", json.dumps({"created_at": "08/11/26"}), "← 8 de novembro ou 11 de agosto?")
