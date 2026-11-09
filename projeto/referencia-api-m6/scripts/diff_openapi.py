import copy
import yaml

METODOS = ("get", "post", "put", "patch", "delete")


def quebras(antigo, novo):
    """Mudanças que QUEBRAM clientes existentes: rota/método/propriedade removidos, tipo alterado, campo novo obrigatório."""
    achados = []
    for caminho, ops in antigo["paths"].items():
        for m in (m for m in ops if m in METODOS):
            if caminho not in novo["paths"] or m not in novo["paths"][caminho]:
                achados.append(f"removido: {m.upper()} {caminho}")
    for nome, sch in antigo["components"]["schemas"].items():
        nsch = novo["components"]["schemas"].get(nome)
        if nsch is None:
            achados.append(f"schema removido: {nome}")
            continue
        for prop, definicao in sch.get("properties", {}).items():
            if prop not in nsch.get("properties", {}):
                achados.append(f"propriedade removida: {nome}.{prop}")
            elif definicao.get("type") != nsch["properties"][prop].get("type") and "$ref" not in definicao:
                achados.append(f"tipo alterado: {nome}.{prop} {definicao.get('type')} → {nsch['properties'][prop].get('type')}")
        for r in set(nsch.get("required", [])) - set(sch.get("required", [])):
            achados.append(f"campo agora obrigatório: {nome}.{r}")
    return achados


v1 = yaml.safe_load(open("schema.yml"))
v2 = copy.deepcopy(v1)
del v2["paths"]["/api/v1/orders/{id}/cancel/"]                         # rota removida
del v2["components"]["schemas"]["Category"]["properties"]["slug"]        # campo removido
v2["components"]["schemas"]["Order"]["properties"]["total"]["type"] = "number"   # tipo alterado
v2["components"]["schemas"]["AddToCart"]["required"].append("note")       # campo novo obrigatório
v2["components"]["schemas"]["Product"]["properties"]["promo"] = {"type": "string"}  # acréscimo opcional: compatível

print("v1 → v1:", quebras(v1, v1) or "nenhuma quebra")
print("v1 → v2 modificado:")
for a in quebras(v1, v2): print("  -", a)
