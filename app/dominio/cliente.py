from dataclasses import dataclass
from enum import Enum

from app.dominio.erros import RegraViolada

# REN ANEEL 1.000/2021: acima de 5% da demanda contratada o cliente paga ultrapassagem
TOLERANCIA_ULTRAPASSAGEM = 0.05
FAIXA_ATENCAO = 0.90


class Segmento(str, Enum):
    SUPERMERCADO = "SUPERMERCADO"
    ACADEMIA = "ACADEMIA"
    CLINICA = "CLINICA"
    PADARIA = "PADARIA"
    ESCOLA = "ESCOLA"
    OUTRO = "OUTRO"


class SituacaoDemanda(str, Enum):
    NORMAL = "NORMAL"
    ATENCAO = "ATENCAO"
    ULTRAPASSAGEM = "ULTRAPASSAGEM"


@dataclass
class Cliente:
    nome: str
    segmento: Segmento
    demanda_contratada_kw: float
    cnpj: str | None = None
    bairro: str | None = None
    participa_hoje: bool = True
    id: int | None = None

    def __post_init__(self):
        if not self.nome or not self.nome.strip():
            raise RegraViolada("O nome do cliente é obrigatório")
        try:
            self.segmento = Segmento(self.segmento)
        except ValueError:
            raise RegraViolada(f"Segmento inválido: {self.segmento}")
        if self.demanda_contratada_kw is None or self.demanda_contratada_kw <= 0:
            raise RegraViolada("A demanda contratada deve ser maior que zero")

    @property
    def limite_tolerado_kw(self) -> float:
        return round(self.demanda_contratada_kw * (1 + TOLERANCIA_ULTRAPASSAGEM), 4)

    def classificar_demanda(self, demanda_kw: float) -> SituacaoDemanda:
        if demanda_kw > self.limite_tolerado_kw:
            return SituacaoDemanda.ULTRAPASSAGEM
        if demanda_kw >= self.demanda_contratada_kw * FAIXA_ATENCAO:
            return SituacaoDemanda.ATENCAO
        return SituacaoDemanda.NORMAL

    def excedente_kw(self, demanda_kw: float) -> float:
        return round(max(0.0, demanda_kw - self.limite_tolerado_kw), 2)
