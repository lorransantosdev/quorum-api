from sqlalchemy.orm import Session

from app.aplicacao.datas import para_utc
from app.aplicacao.erros import DespachoNaoEncontrado
from app.dominio.despacho import Despacho, planejar
from app.infraestrutura.modelos import AcionamentoModelo, DespachoModelo
from app.infraestrutura.repositorios import DespachoRepositorio, EquipamentoRepositorio, equipamento_para_dominio


def criar_despacho(session: Session, dados: dict) -> DespachoModelo:
    despacho = Despacho(
        potencia_solicitada_kw=dados["potencia_solicitada_kw"],
        inicio=para_utc(dados["inicio"]),
        duracao_min=dados["duracao_min"],
        descricao=dados.get("descricao"),
    )

    # so entram equipamentos ativos de clientes que nao apertaram "hoje nao"
    elegiveis = EquipamentoRepositorio(session).elegiveis_para_despacho()
    plano = planejar(despacho, [equipamento_para_dominio(m) for m in elegiveis])

    modelo = DespachoModelo(
        descricao=despacho.descricao,
        potencia_solicitada_kw=despacho.potencia_solicitada_kw,
        potencia_atendida_kw=plano.potencia_atendida_kw,
        inicio=despacho.inicio,
        duracao_min=despacho.duracao_min,
        status=plano.status.value,
        acionamentos=[
            AcionamentoModelo(equipamento_id=a.equipamento.id, potencia_kw=a.potencia_kw) for a in plano.acionamentos
        ],
    )
    repo = DespachoRepositorio(session)
    repo.salvar(modelo)
    return repo.buscar(modelo.id)


def buscar_despacho(session: Session, despacho_id: int) -> DespachoModelo:
    modelo = DespachoRepositorio(session).buscar(despacho_id)
    if modelo is None:
        raise DespachoNaoEncontrado(despacho_id)
    return modelo


def listar_despachos(session: Session, pagina: int, tamanho: int):
    return DespachoRepositorio(session).listar(pagina, tamanho)
