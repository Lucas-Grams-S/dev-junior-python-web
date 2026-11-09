def status_para(metodo, resultado):
    """Escolhe o status HTTP conforme a convenção REST. `resultado` descreve o que aconteceu."""
    tabela = {
        ("GET", "ok"): 200,
        ("GET", "nao_existe"): 404,
        ("POST", "criado"): 201,
        ("POST", "dados_invalidos"): 400,
        ("POST", "regra_de_negocio"): 422,
        ("POST", "conflito"): 409,
        ("PUT", "substituido"): 200,
        ("PATCH", "alterado"): 200,
        ("DELETE", "removido"): 204,
        ("DELETE", "nao_existe"): 404,
        ("*", "sem_login"): 401,
        ("*", "sem_permissao"): 403,
        ("*", "metodo_nao_permitido"): 405,
        ("*", "muitas_requisicoes"): 429,
    }
    return tabela.get((metodo, resultado)) or tabela.get(("*", resultado))


for m, r in [("GET", "ok"), ("POST", "criado"), ("POST", "regra_de_negocio"), ("DELETE", "removido"),
             ("PATCH", "sem_login"), ("PUT", "sem_permissao"), ("GET", "muitas_requisicoes")]:
    print(f"{m:<6} {r:<18} → {status_para(m, r)}")
