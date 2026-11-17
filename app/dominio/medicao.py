from dataclasses import dataclass, field
from datetime import datetime

from app.dominio.cliente import Cliente, SituacaoDemanda
from app.dominio.erros import RegraViolada

DEMANDA_MAXIMA_SENSOR_KW = 10000


@dataclass
class Medicao:
    cliente: Cliente
    momento: datetime
    demanda_kw: float
    situacao: SituacaoDemanda = field(init=False)
    excedente_kw: float = field(init=False)

    def __post_init__(self):
        if self.demanda_kw < 0:
            raise RegraViolada("Demanda negativa indica falha do medidor, leitura descartada")
        if self.demanda_kw > DEMANDA_MAXIMA_SENSOR_KW:
            raise RegraViolada(f"Demanda acima de {DEMANDA_MAXIMA_SENSOR_KW} kW está fora da faixa do sensor")
        self.situacao = self.cliente.classificar_demanda(self.demanda_kw)
        self.excedente_kw = self.cliente.excedente_kw(self.demanda_kw)
