def mesma_origem(a, b):
    return a == b                                   # esquema + host + porta, tudo igual


def decidir(config, origem, metodo, pede_metodo=None, pede_cabecalhos=()):
    """Devolve os cabeçalhos CORS que o servidor responderia (vazio = o navegador bloqueia a leitura)."""
    if origem not in config["origens"]:
        return {}
    cab = {"Access-Control-Allow-Origin": origem, "Vary": "Origin"}
    if metodo == "OPTIONS" and pede_metodo:                                   # preflight
        if pede_metodo not in config["metodos"]:
            return {}
        extra = {h.lower() for h in pede_cabecalhos} - set(config["cabecalhos"])
        if extra:
            return {}
        cab |= {"Access-Control-Allow-Methods": ", ".join(config["metodos"]),
                "Access-Control-Allow-Headers": ", ".join(config["cabecalhos"]), "Access-Control-Max-Age": "600"}
    return cab


cfg = {"origens": {"http://127.0.0.1:8200"}, "metodos": ["GET", "POST", "PATCH", "DELETE"],
       "cabecalhos": ["authorization", "content-type"]}
casos = [
    ("GET de origem permitida", ("http://127.0.0.1:8200", "GET")),
    ("GET de origem estranha", ("https://site-malicioso.example", "GET")),
    ("preflight POST + Authorization", ("http://127.0.0.1:8200", "OPTIONS", "POST", ["Authorization", "Content-Type"])),
    ("preflight com cabeçalho não listado", ("http://127.0.0.1:8200", "OPTIONS", "POST", ["X-Segredo"])),
    ("preflight de PUT (não listado)", ("http://127.0.0.1:8200", "OPTIONS", "PUT", [])),
]
for titulo, args in casos:
    r = decidir(cfg, *args)
    print(f"{titulo:<38} → {'LIBERA ' + r['Access-Control-Allow-Origin'] if r else 'BLOQUEIA'}")
print("mesma origem?", mesma_origem("http://127.0.0.1:8200", "http://127.0.0.1:8131"), "(a porta conta)")
