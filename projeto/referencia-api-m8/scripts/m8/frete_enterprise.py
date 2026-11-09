from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class ConfiguracaoDeFrete:
    valor_padrao: Decimal = Decimal("19.90")
    limite_gratis: Decimal = Decimal("200.00")


class EstrategiaDeFrete(ABC):
    def __init__(self, configuracao: ConfiguracaoDeFrete) -> None:
        self._configuracao = configuracao

    @abstractmethod
    def calcular(self, subtotal: Decimal) -> Decimal:
        raise NotImplementedError


class EstrategiaDeFreteGratis(EstrategiaDeFrete):
    def calcular(self, subtotal: Decimal) -> Decimal:
        return Decimal("0")


class EstrategiaDeFretePadrao(EstrategiaDeFrete):
    def calcular(self, subtotal: Decimal) -> Decimal:
        return self._configuracao.valor_padrao


class FabricaDeEstrategiasDeFrete:
    def __init__(self, configuracao: Optional[ConfiguracaoDeFrete] = None) -> None:
        self._configuracao = configuracao or ConfiguracaoDeFrete()

    def criar(self, subtotal: Decimal) -> EstrategiaDeFrete:
        if subtotal >= self._configuracao.limite_gratis:
            return EstrategiaDeFreteGratis(self._configuracao)
        return EstrategiaDeFretePadrao(self._configuracao)


class CalculadoraDeFrete:
    def __init__(self, fabrica: Optional[FabricaDeEstrategiasDeFrete] = None) -> None:
        self._fabrica = fabrica or FabricaDeEstrategiasDeFrete()

    def calcular(self, subtotal: Decimal) -> Decimal:
        return self._fabrica.criar(subtotal).calcular(subtotal)
