from datetime import datetime

from sqlalchemy.orm import Session

from app.aplicacao.clientes import buscar_cliente
from app.aplicacao.datas import para_utc
from app.dominio.erros import RegraViolada
from app.dominio.medicao import Medicao
from app.infraestrutura.modelos import MedicaoModelo
from app.infraestrutura.repositorios import MedicaoRepositorio, cliente_para_dominio


def _validar_periodo(de: datetime | None, ate: datetime | None):
    de, ate = para_utc(de), para_utc(ate)
    if de and ate and de > ate:
        raise RegraViolada("A data 'de' deve ser anterior ou igual à data 'ate'")
    return de, ate


def registrar_medicao(session: Session, cliente_id: int, momento: datetime, demanda_kw: float) -> MedicaoModelo:
    cliente = cliente_para_dominio(buscar_cliente(session, cliente_id))
    medicao = Medicao(cliente, para_utc(momento), demanda_kw)
    modelo = MedicaoModelo(
        cliente_id=cliente_id,
        momento=medicao.momento,
        demanda_kw=medicao.demanda_kw,
        situacao=medicao.situacao.value,
        excedente_kw=medicao.excedente_kw,
    )
    return MedicaoRepositorio(session).salvar(modelo)


def listar_medicoes(session: Session, cliente_id: int, de: datetime | None = None, ate: datetime | None = None):
    de, ate = _validar_periodo(de, ate)
    buscar_cliente(session, cliente_id)
    return MedicaoRepositorio(session).listar_do_cliente(cliente_id, de, ate)


def listar_ultrapassagens(session: Session, de: datetime | None = None, ate: datetime | None = None) -> list[dict]:
    de, ate = _validar_periodo(de, ate)
    linhas = MedicaoRepositorio(session).ultrapassagens(de, ate)
    return [
        {
            "medicao_id": medicao.id,
            "cliente_id": medicao.cliente_id,
            "cliente_nome": nome,
            "momento": medicao.momento,
            "demanda_kw": medicao.demanda_kw,
            "demanda_contratada_kw": contratada,
            "excedente_kw": medicao.excedente_kw,
        }
        for medicao, nome, contratada in linhas
    ]
