from dataclasses import dataclass
from enum import Enum

from app.dominio.erros import RegraViolada

RESERVA_MINIMA_BATERIA = 20
FATOR_AR_CONDICIONADO = 0.30
FATOR_CAMARA_FRIA = 0.20


class TipoEquipamento(str, Enum):
    BATERIA = "BATERIA"
    CARREGADOR_VE = "CARREGADOR_VE"
    AR_CONDICIONADO = "AR_CONDICIONADO"
    CAMARA_FRIA = "CAMARA_FRIA"


@dataclass
class Equipamento:
    tipo: TipoEquipamento
    marca: str
    potencia_kw: float
    carga_percentual: float | None = None
    ativo: bool = True
    cliente_id: int | None = None
    id: int | None = None

    def __post_init__(self):
        try:
            self.tipo = TipoEquipamento(self.tipo)
        except ValueError:
            raise RegraViolada(f"Tipo de equipamento inválido: {self.tipo}")
        if not self.marca or not self.marca.strip():
            raise RegraViolada("A marca do equipamento é obrigatória")
        if self.potencia_kw is None or self.potencia_kw <= 0:
            raise RegraViolada("A potência do equipamento deve ser maior que zero")

        if self.tipo == TipoEquipamento.BATERIA:
            if self.carga_percentual is None:
                raise RegraViolada("Bateria precisa informar carga_percentual")
            if not 0 <= self.carga_percentual <= 100:
                raise RegraViolada("carga_percentual deve estar entre 0 e 100")
        elif self.carga_percentual is not None:
            raise RegraViolada("carga_percentual só se aplica a baterias")

    def flexibilidade_kw(self) -> float:
        if not self.ativo:
            return 0.0
        if self.tipo == TipoEquipamento.BATERIA:
            # abaixo da reserva a bateria fica guardada para caso de apagão
            if self.carga_percentual > RESERVA_MINIMA_BATERIA:
                return self.potencia_kw
            return 0.0
        if self.tipo == TipoEquipamento.CARREGADOR_VE:
            return self.potencia_kw
        if self.tipo == TipoEquipamento.AR_CONDICIONADO:
            # sobe no maximo 1 grau a cada 30 min, sem tirar o conforto
            return round(self.potencia_kw * FATOR_AR_CONDICIONADO, 2)
        return round(self.potencia_kw * FATOR_CAMARA_FRIA, 2)
