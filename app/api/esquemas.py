from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.aplicacao.datas import para_fuso_sp
from app.dominio.cliente import Segmento, SituacaoDemanda
from app.dominio.despacho import StatusDespacho
from app.dominio.equipamento import TipoEquipamento

DataHora = Annotated[datetime, AfterValidator(para_fuso_sp)]


class Erro(BaseModel):
    detail: str = Field(examples=["Cliente 99 não encontrado"])


ERRO_404 = {404: {"model": Erro, "description": "Recurso não encontrado"}}
ERRO_409 = {409: {"model": Erro, "description": "Conflito com o estado atual dos dados"}}
ERRO_422 = {422: {"description": "Dados inválidos ou regra de negócio violada"}}


class ClienteEntrada(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "nome": "Mercado Bom Preço – Vila Mariana",
                    "segmento": "SUPERMERCADO",
                    "cnpj": "00.000.000/0001-01",
                    "bairro": "Vila Mariana",
                    "demanda_contratada_kw": 300,
                }
            ]
        }
    )

    nome: str = Field(min_length=1, max_length=120)
    segmento: Segmento
    cnpj: str | None = Field(
        default=None, pattern=r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$", description="CNPJ fictício no formato 00.000.000/0000-00"
    )
    bairro: str | None = Field(default=None, max_length=60)
    demanda_contratada_kw: float = Field(description="Demanda contratada com a distribuidora (precisa ser > 0)")


class ClienteSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    nome: str = Field(examples=["Mercado Bom Preço – Vila Mariana"])
    segmento: Segmento
    cnpj: str | None = Field(examples=["00.000.000/0001-01"])
    bairro: str | None = Field(examples=["Vila Mariana"])
    demanda_contratada_kw: float = Field(examples=[300])
    participa_hoje: bool = Field(examples=[True])


class PaginaClientes(BaseModel):
    itens: list[ClienteSaida]
    total: int = Field(examples=[5])
    pagina: int = Field(examples=[1])
    tamanho: int = Field(examples=[20])


class ParticipacaoEntrada(BaseModel):
    participa_hoje: bool = Field(description="false = botão 'hoje não': o cliente fica fora dos despachos", examples=[False])


class EquipamentoEntrada(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"tipo": "BATERIA", "marca": "BYD", "potencia_kw": 100, "carga_percentual": 80, "ativo": True}]
        }
    )

    tipo: TipoEquipamento
    marca: str = Field(min_length=1, max_length=60)
    potencia_kw: float = Field(description="Potência nominal do equipamento (> 0)")
    carga_percentual: float | None = Field(default=None, description="Somente para BATERIA, de 0 a 100")
    ativo: bool = True


class EquipamentoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    cliente_id: int = Field(examples=[1])
    tipo: TipoEquipamento
    marca: str = Field(examples=["BYD"])
    potencia_kw: float = Field(examples=[100])
    carga_percentual: float | None = Field(examples=[80])
    ativo: bool = Field(examples=[True])


class EquipamentoFlexivel(BaseModel):
    equipamento_id: int = Field(examples=[1])
    tipo: TipoEquipamento
    marca: str = Field(examples=["Daikin"])
    potencia_kw: float = Field(examples=[40])
    flexibilidade_kw: float = Field(examples=[12])


class FlexibilidadeSaida(BaseModel):
    cliente_id: int = Field(examples=[1])
    participa_hoje: bool = Field(examples=[True])
    flexibilidade_kw: float = Field(description="Soma do que os equipamentos conseguem liberar", examples=[124])
    disponivel_hoje_kw: float = Field(description="Zero quando o cliente apertou 'hoje não'", examples=[124])
    equipamentos: list[EquipamentoFlexivel]


class MedicaoEntrada(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"momento": "2026-11-10T18:30:00-03:00", "demanda_kw": 330}]}
    )

    momento: datetime = Field(description="Sem fuso, considera horário de Brasília (-03:00)")
    demanda_kw: float = Field(description="Leitura do medidor, de 0 a 10000 kW")


class MedicaoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    cliente_id: int = Field(examples=[1])
    momento: DataHora = Field(examples=["2026-11-10T18:30:00-03:00"])
    demanda_kw: float = Field(examples=[330])
    situacao: SituacaoDemanda
    excedente_kw: float = Field(examples=[15])


class UltrapassagemSaida(BaseModel):
    medicao_id: int = Field(examples=[1])
    cliente_id: int = Field(examples=[1])
    cliente_nome: str = Field(examples=["Mercado Bom Preço – Vila Mariana"])
    momento: DataHora = Field(examples=["2026-11-10T18:30:00-03:00"])
    demanda_kw: float = Field(examples=[330])
    demanda_contratada_kw: float = Field(examples=[300])
    excedente_kw: float = Field(examples=[15])


class DespachoEntrada(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "descricao": "Pico de fim de tarde - zona sul",
                    "potencia_solicitada_kw": 150,
                    "inicio": "2026-11-18T18:30:00-03:00",
                    "duracao_min": 60,
                }
            ]
        }
    )

    descricao: str | None = Field(default=None, max_length=120)
    potencia_solicitada_kw: float = Field(description="Quanto a rede pediu para a usina virtual (> 0)")
    inicio: datetime
    duracao_min: int = Field(description="Entre 15 e 120 minutos")


class AcionamentoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    equipamento_id: int = Field(examples=[2])
    potencia_kw: float = Field(examples=[100])


class DespachoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    descricao: str | None = Field(examples=["Pico de fim de tarde - zona sul"])
    potencia_solicitada_kw: float = Field(examples=[150])
    potencia_atendida_kw: float = Field(examples=[150])
    inicio: DataHora = Field(examples=["2026-11-18T18:30:00-03:00"])
    duracao_min: int = Field(examples=[60])
    status: StatusDespacho
    acionamentos: list[AcionamentoSaida]


class Saude(BaseModel):
    status: str = Field(examples=["ok"])
    banco: str = Field(examples=["ok"])
