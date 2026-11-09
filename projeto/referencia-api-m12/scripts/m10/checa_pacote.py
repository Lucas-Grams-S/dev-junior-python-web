"""Antes de `uv add` num pacote sugerido por IA (ou por qualquer fonte): ele existe? tem histórico? Consulta ao PyPI (somente leitura)."""
import json, sys, urllib.error, urllib.request
from datetime import datetime

def checar(nome):
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{nome}/json", timeout=20) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        return f"{nome:<34} ❌ NÃO EXISTE no PyPI (HTTP {e.code}): provavelmente nome inventado; NÃO instale"
    datas = sorted(a["upload_time"] for versoes in d["releases"].values() for a in versoes)
    primeira, ultima = datas[0][:10], datas[-1][:10]
    return (f"{nome:<34} ✅ existe · {len(d['releases'])} versões · primeira publicação {primeira} · última {ultima} · "
            f"página do projeto: {d['info'].get('home_page') or (d['info'].get('project_urls') or {}).get('Source') or '-'}")

for n in sys.argv[1:]:
    print(checar(n))
