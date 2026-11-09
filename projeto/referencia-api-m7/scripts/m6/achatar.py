def achatar(erros, prefixo=""):
    """{'items': [{'quantity': ['x']}, {}], 'detail': 'y'} -> ['items[0].quantity: x', 'detail: y']"""
    linhas = []
    if isinstance(erros, dict):
        for campo, valor in erros.items():
            linhas += achatar(valor, f"{prefixo}.{campo}" if prefixo else campo)
    elif isinstance(erros, list):
        if erros and all(isinstance(e, str) for e in erros):
            linhas += [f"{prefixo}: {e}" for e in erros]
        else:
            for i, item in enumerate(erros):
                linhas += achatar(item, f"{prefixo}[{i}]")
    else:
        linhas.append(f"{prefixo}: {erros}")
    return linhas


exemplo = {"sku": ["Formato inválido.", "Já existe."], "items": [{}, {"quantity": ["Deve ser >= 1."]}], "detail": "Falha geral."}
print("\n".join(achatar(exemplo)))
