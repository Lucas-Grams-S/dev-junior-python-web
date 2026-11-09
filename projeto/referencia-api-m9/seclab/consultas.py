"""Duas versões da MESMA busca por nome. A primeira é o ANTI-PADRÃO (existe só para as ferramentas apontarem); nunca é roteada."""
from django.db import connection

from apps.catalog.models import Product


def buscar_vulneravel(termo):
    # ANTI-PADRÃO: o texto do usuário vira parte do comando SQL.
    sql = f"SELECT sku, name FROM catalog_product WHERE is_active = 1 AND name LIKE '%{termo}%'"
    with connection.cursor() as c:
        c.execute(sql)
        return c.fetchall()


def _escapa_like(termo):
    return termo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def buscar_segura(termo):
    # ORM: o valor viaja como PARÂMETRO, separado do comando.
    return list(Product.objects.filter(is_active=True, name__icontains=termo).values_list("sku", "name"))


def buscar_segura_sql_cru(termo):
    # SQL cru: marcadores %s e lista de parâmetros (nunca f-string). Portável: TRUE (não 1) e LOWER() dos dois lados, pois o LIKE do PostgreSQL distingue maiúsculas.
    with connection.cursor() as c:
        c.execute("SELECT sku, name FROM catalog_product WHERE is_active = TRUE AND LOWER(name) LIKE LOWER(%s) ESCAPE '\\'", [f"%{_escapa_like(termo)}%"])
        return c.fetchall()
