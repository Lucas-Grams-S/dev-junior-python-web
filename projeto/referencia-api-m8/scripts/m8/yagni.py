from decimal import Decimal

from frete_enterprise import CalculadoraDeFrete
from frete_simples import calcular_frete

casos = [Decimal(x) for x in ("0", "50.00", "199.99", "200.00", "999.99")]
print("mesmas respostas nas duas versões?", all(calcular_frete(c) == CalculadoraDeFrete().calcular(c) for c in casos))
print("exemplos:", {str(c): str(calcular_frete(c)) for c in casos})
