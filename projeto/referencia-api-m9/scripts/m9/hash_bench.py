"""Quanto custa UM hash de senha? Lento de propósito = caro para quem tenta adivinhar. Mede neste computador."""
import hashlib
import os
import statistics
import sys
import time

import bcrypt
import django
from argon2 import PasswordHasher

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.environ["LAB"])
django.setup()
from django.contrib.auth.hashers import PBKDF2PasswordHasher, check_password, make_password  # noqa: E402

senha = "correto-cavalo-bateria-grampo"


def medir(f, n=5):
    tempos = []
    for _ in range(n):
        t = time.perf_counter()
        f()
        tempos.append(time.perf_counter() - t)
    return statistics.median(tempos)


salt = os.urandom(16)
alvos = [
    ("SHA-256 puro (ERRADO para senhas)", lambda: hashlib.sha256(senha.encode()).hexdigest(), 2000),
    ("SHA-256 com salt (ainda ERRADO)", lambda: hashlib.sha256(salt + senha.encode()).hexdigest(), 2000),
    (f"PBKDF2-SHA256, {PBKDF2PasswordHasher.iterations:,} iterações (padrão Django 5.2)", lambda: make_password(senha, hasher="pbkdf2_sha256"), 3),
    ("bcrypt, custo 12", lambda: bcrypt.hashpw(senha.encode(), bcrypt.gensalt(12)), 3),
    ("scrypt (n=2^15, r=8, p=1)", lambda: hashlib.scrypt(senha.encode(), salt=salt, n=2**15, r=8, p=1, maxmem=64 * 1024 * 1024), 3),
    ("Argon2id (padrões do argon2-cffi)", lambda: PasswordHasher().hash(senha), 3),
]
print(f"{'algoritmo':<62} {'tempo por hash':>16} {'tentativas/s (1 núcleo)':>26}")
base = None
for nome, f, n in alvos:
    t = medir(f, n)
    if "puro" in nome:
        base = t
    tempo = f"{t * 1000:,.3f} ms" if t >= 0.001 else f"{t * 1e6:,.1f} µs"
    print(f"{nome:<62} {tempo:>16} {1 / t:>26,.0f}")

print("\nFormato guardado no banco (mesma senha, duas vezes → hashes diferentes por causa do SALT):")
a, b = make_password(senha, hasher="pbkdf2_sha256"), make_password(senha, hasher="pbkdf2_sha256")
print("  ", a[:60] + "...")
print("  ", b[:60] + "...")
print("   mesma senha, mesmo hash?", a == b, "· check_password(certa) =", check_password(senha, a), "· check_password(errada) =", check_password("errada", a))
h = PasswordHasher().hash(senha)
print("   Argon2id:", h)
