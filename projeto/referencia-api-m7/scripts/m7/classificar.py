import hashlib
import json
import re
import tempfile
import time


def classificar(fn, limite=0.5):
    """Mede o tempo de parede e de CPU e classifica a função."""
    p0, c0 = time.perf_counter(), time.process_time()
    fn()
    parede, cpu = time.perf_counter() - p0, time.process_time() - c0
    razao = cpu / parede if parede else 0
    return ("CPU-bound" if razao >= limite else "I/O-bound"), round(razao, 2), round(parede, 2)


def le_arquivo_grande():
    with tempfile.NamedTemporaryFile() as f:
        f.write(b"x" * 50_000_000); f.flush()
        open(f.name, "rb").read()


casos = {
    "time.sleep(0.3)": lambda: time.sleep(0.3),
    "sha256 de 30 MB": lambda: hashlib.sha256(b"x" * 30_000_000).hexdigest(),
    "json.dumps de 200 mil itens": lambda: json.dumps([{"id": i, "nome": f"p{i}"} for i in range(200_000)]),
    "regex em texto de 5 MB": lambda: re.findall(r"\d+", "abc 123 " * 600_000),
    "ler arquivo de 50 MB (no cache do SO)": le_arquivo_grande,
    "esperar por resposta (select/sleep curto ×20)": lambda: [time.sleep(0.02) for _ in range(20)],
}
for nome, fn in casos.items():
    tipo, razao, parede = classificar(fn)
    print(f"{nome:<46} → {tipo:<9} (cpu/parede = {razao:4.2f}, parede = {parede:4.2f} s)")
