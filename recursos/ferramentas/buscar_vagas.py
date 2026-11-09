# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "beautifulsoup4"]
# ///
"""Coleta vagas públicas (sem login) do LinkedIn e conta tecnologias citadas.

Uso:
    uv run recursos/ferramentas/buscar_vagas.py
    uv run recursos/ferramentas/buscar_vagas.py -k "python django junior" -n 20 -l Brasil

Saídas (em recursos/ferramentas/saida/): vagas.json e analise.md

Atenção: usa os endpoints públicos "guest" do LinkedIn, que não são API oficial.
Os termos de uso do LinkedIn restringem coleta automatizada; use só para pesquisa
pessoal, em volume baixo, como aqui. Se receber HTTP 429, pare e tente mais tarde.
"""
import argparse, json, random, re, time
from collections import Counter
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://www.linkedin.com/jobs-guest/jobs/api"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

# termo -> regex (case-insensitive)
TECHS = {
    "Python": r"\bpython\b", "Django": r"\bdjango\b", "DRF": r"rest framework|\bdrf\b",
    "FastAPI": r"fastapi", "Flask": r"\bflask\b", "SQL": r"\bsql\b",
    "PostgreSQL": r"postgres", "MySQL": r"mysql", "MongoDB": r"mongo",
    "Redis": r"\bredis\b", "Celery": r"celery", "RabbitMQ/Kafka": r"rabbitmq|kafka",
    "Docker": r"docker", "Kubernetes": r"kubernetes|\bk8s\b", "AWS": r"\baws\b|amazon web",
    "Azure": r"azure", "GCP": r"\bgcp\b|google cloud", "Git": r"\bgit\b|github|gitlab",
    "CI/CD": r"ci/cd|\bci\b.*\bcd\b|github actions|jenkins", "Linux": r"linux",
    "REST/API": r"\brest\b|\bapis?\b|restful", "GraphQL": r"graphql",
    "Testes": r"\btestes?\b|\btests?\b|pytest|unittest|tdd", "POO": r"\bpoo\b|orienta..o a objetos|\boop\b",
    "Scrum/Agile": r"scrum|agile|\bágil\b|kanban", "JavaScript/React": r"javascript|react|typescript|\bvue\b",
    "Inglês": r"ingl[eê]s|english", "Microsserviços": r"microsservi|microservi",
    "SOLID/Patterns": r"\bsolid\b|design patterns|padr[õo]es de projeto",
    "IA/LLM": r"\bia\b|\bai\b|llm|machine learning|copilot|claude",
}


def get(url, params=None, tries=3):
    for i in range(tries):
        r = requests.get(url, params=params, headers=HEADERS, timeout=20)
        if r.status_code == 429:
            wait = 60 * (i + 1)
            print(f"  429 recebido; aguardando {wait}s (tentativa {i+1}/{tries})")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.text
    raise SystemExit("LinkedIn continua devolvendo 429. Pare e tente mais tarde (ou de outra rede).")


def pause(lo, hi):
    time.sleep(random.uniform(lo, hi))


def search(keywords, location, n, delay):
    jobs, start = {}, 0
    while len(jobs) < n:
        html = get(f"{BASE}/seeMoreJobPostings/search",
                   {"keywords": keywords, "location": location, "f_E": "2",  # 2 = Júnior (Entry level)
                    "geoId": "106057199",  # Brasil
                    "start": start})
        cards = BeautifulSoup(html, "html.parser").select("li")
        if not cards:
            break
        for li in cards:
            base = li.select_one("div.base-card")
            if not base or not base.get("data-entity-urn"):
                continue
            jid = base["data-entity-urn"].split(":")[-1]
            title = li.select_one(".base-search-card__title")
            comp = li.select_one(".base-search-card__subtitle")
            loc = li.select_one(".job-search-card__location")
            jobs.setdefault(jid, {
                "id": jid,
                "title": title.get_text(strip=True) if title else "",
                "company": comp.get_text(strip=True) if comp else "",
                "location": loc.get_text(strip=True) if loc else "",
                "url": f"https://www.linkedin.com/jobs/view/{jid}",
            })
        start += len(cards)
        print(f"Lista: {len(jobs)} vagas até agora")
        pause(*delay)
    return list(jobs.values())[:n]


def details(job, delay):
    html = get(f"{BASE}/jobPosting/{job['id']}")
    soup = BeautifulSoup(html, "html.parser")
    desc = soup.select_one(".show-more-less-html__markup, .description__text")
    job["description"] = desc.get_text("\n", strip=True) if desc else ""
    pause(*delay)


def analyze(jobs):
    cnt = Counter()
    for j in jobs:
        text = f"{j['title']}\n{j.get('description','')}"
        for name, rx in TECHS.items():
            if re.search(rx, text, re.I):
                cnt[name] += 1
    return cnt


def report(jobs, cnt, keywords):
    n = len(jobs)
    out = [f"# Análise de {n} vagas — busca: `{keywords}`", "",
           f"Coletado em {time.strftime('%Y-%m-%d')}. Percentual = vagas que citam o termo.", "",
           "| Tecnologia | Vagas | % |", "|---|---|---|"]
    for k, v in cnt.most_common():
        out.append(f"| {k} | {v} | {100*v/max(n,1):.0f}% |")
    out += ["", "## Vagas", ""]
    out += [f"- [{j['title']} — {j['company']}]({j['url']}) ({j['location']})" for j in jobs]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-k", "--keywords", default="python junior")
    ap.add_argument("-l", "--location", default="Brazil")
    ap.add_argument("-n", "--num", type=int, default=20)
    ap.add_argument("--min-delay", type=float, default=6.0, help="segundos")
    ap.add_argument("--max-delay", type=float, default=12.0, help="segundos")
    a = ap.parse_args()
    delay = (a.min_delay, a.max_delay)

    jobs = search(a.keywords, a.location, a.num, delay)
    if not jobs:
        raise SystemExit("Nenhuma vaga encontrada (o LinkedIn pode ter mudado o HTML).")
    for i, j in enumerate(jobs, 1):
        print(f"[{i}/{len(jobs)}] {j['title']} — {j['company']}")
        details(j, delay)

    outdir = Path(__file__).parent / "saida"
    outdir.mkdir(exist_ok=True)
    (outdir / "vagas.json").write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
    (outdir / "analise.md").write_text(report(jobs, analyze(jobs), a.keywords), encoding="utf-8")
    print(f"Pronto: {outdir/'analise.md'}")


if __name__ == "__main__":
    main()
