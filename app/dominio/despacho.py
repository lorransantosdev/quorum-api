from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.dominio.equipamento import Equipamento
from app.dominio.erros import RegraViolada

DURACAO_MINIMA_MIN = 15
DURACAO_MAXIMA_MIN = 120


class StatusDespacho(str, Enum):
    ATENDIDO = "ATENDIDO"
    PARCIAL = "PARCIAL"
    SEM_CAPACIDADE = "SEM_CAPACIDADE"


@dataclass
class Despacho:
    potencia_solicitada_kw: float
    inicio: datetime
    duracao_min: int
    descricao: str | None = None

    def __post_init__(self):
        if self.potencia_solicitada_kw is None or self.potencia_solicitada_kw <= 0:
            raise RegraViolada("A potência solicitada deve ser maior que zero")
        if not DURACAO_MINIMA_MIN <= self.duracao_min <= DURACAO_MAXIMA_MIN:
            raise RegraViolada(
                f"A duração do despacho deve ficar entre {DURACAO_MINIMA_MIN} e {DURACAO_MAXIMA_MIN} minutos"
            )


@dataclass
class Acionamento:
    equipamento: Equipamento
    potencia_kw: float


@dataclass
class PlanoDespacho:
    acionamentos: list[Acionamento]
    potencia_atendida_kw: float
    status: StatusDespacho


def planejar(despacho: Despacho, equipamentos: list[Equipamento]) -> PlanoDespacho:
    candidatos = [e for e in equipamentos if e.flexibilidade_kw() > 0]
    candidatos.sort(key=lambda e: e.flexibilidade_kw(), reverse=True)

    restante = despacho.potencia_solicitada_kw
    acionamentos = []
    for equipamento in candidatos:
        if restante <= 0:
            break
        potencia = round(min(equipamento.flexibilidade_kw(), restante), 2)
        acionamentos.append(Acionamento(equipamento, potencia))
        restante = round(restante - potencia, 2)

    atendida = round(sum(a.potencia_kw for a in acionamentos), 2)
    if atendida >= despacho.potencia_solicitada_kw:
        status = StatusDespacho.ATENDIDO
    elif atendida > 0:
        status = StatusDespacho.PARCIAL
    else:
        status = StatusDespacho.SEM_CAPACIDADE
    return PlanoDespacho(acionamentos, atendida, status)
