import base64, hashlib, hmac, json, time


def b64(dados: bytes) -> str:
    return base64.urlsafe_b64encode(dados).rstrip(b"=").decode()


def desb64(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def assinar(payload, chave, validade=900, agora=None):
    agora = int(agora if agora is not None else time.time())
    payload = {**payload, "iat": agora, "exp": agora + validade}
    cab = b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    corpo = b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = b64(hmac.new(chave, f"{cab}.{corpo}".encode(), hashlib.sha256).digest())
    return f"{cab}.{corpo}.{sig}"


def verificar(token, chave, agora=None):
    try:
        cab, corpo, sig = token.split(".")
    except ValueError:
        raise ValueError("formato inválido")
    if json.loads(desb64(cab)).get("alg") != "HS256":                       # nunca aceite o 'alg' que o token escolhe
        raise ValueError("algoritmo não permitido")
    esperado = b64(hmac.new(chave, f"{cab}.{corpo}".encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(esperado, sig):                              # tempo constante
        raise ValueError("assinatura inválida")
    payload = json.loads(desb64(corpo))
    if payload["exp"] <= int(agora if agora is not None else time.time()):
        raise ValueError("token expirado")
    return payload


CHAVE = b"uma-chave-longa-e-aleatoria-com-32+-bytes"
t = assinar({"user_id": 3}, CHAVE, agora=1_000_000)
print("token:", t[:40] + "…")
print("válido    :", verificar(t, CHAVE, agora=1_000_100))
for titulo, token, agora in [
    ("expirado  ", t, 1_000_000 + 901),
    ("adulterado", t.split(".")[0] + "." + b64(json.dumps({"user_id": 1, "exp": 9_999_999_999}).encode()) + "." + t.split(".")[2], 1_000_100),
    ("chave errada", t, 1_000_100),
]:
    try:
        verificar(token, CHAVE if titulo != "chave errada" else b"outra-chave-totalmente-diferente-123", agora=agora)
    except ValueError as e:
        print(f"{titulo}:", e)
sem_alg = b64(json.dumps({"alg": "none", "typ": "JWT"}).encode()) + "." + b64(json.dumps({"user_id": 1, "exp": 9_999_999_999}).encode()) + "."
try:
    verificar(sem_alg, CHAVE, agora=1_000_100)
except ValueError as e:
    print("alg=none  :", e)
