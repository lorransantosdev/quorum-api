from sqlalchemy.orm import Session

from app.aplicacao.clientes import buscar_cliente
from app.aplicacao.erros import Conflito, EquipamentoNaoEncontrado
from app.dominio.equipamento import Equipamento
from app.infraestrutura.modelos import EquipamentoModelo
from app.infraestrutura.repositorios import EquipamentoRepositorio, equipamento_para_dominio


def cadastrar_equipamento(session: Session, cliente_id: int, dados: dict) -> EquipamentoModelo:
    buscar_cliente(session, cliente_id)
    equipamento = Equipamento(**dados, cliente_id=cliente_id)
    modelo = EquipamentoModelo(
        cliente_id=cliente_id,
        tipo=equipamento.tipo.value,
        marca=equipamento.marca.strip(),
        potencia_kw=equipamento.potencia_kw,
        carga_percentual=equipamento.carga_percentual,
        ativo=equipamento.ativo,
    )
    return EquipamentoRepositorio(session).salvar(modelo)


def listar_equipamentos(session: Session, cliente_id: int):
    buscar_cliente(session, cliente_id)
    return EquipamentoRepositorio(session).listar_do_cliente(cliente_id)


def remover_equipamento(session: Session, equipamento_id: int):
    repo = EquipamentoRepositorio(session)
    modelo = repo.buscar(equipamento_id)
    if modelo is None:
        raise EquipamentoNaoEncontrado(equipamento_id)
    if repo.participou_de_despacho(equipamento_id):
        raise Conflito("Equipamento já participou de despachos e não pode ser removido")
    repo.remover(modelo)


def flexibilidade_do_cliente(session: Session, cliente_id: int) -> dict:
    cliente = buscar_cliente(session, cliente_id)
    modelos = EquipamentoRepositorio(session).listar_do_cliente(cliente_id)

    itens = []
    for modelo in modelos:
        equipamento = equipamento_para_dominio(modelo)
        itens.append(
            {
                "equipamento_id": modelo.id,
                "tipo": equipamento.tipo,
                "marca": equipamento.marca,
                "potencia_kw": equipamento.potencia_kw,
                "flexibilidade_kw": equipamento.flexibilidade_kw(),
            }
        )
    total = round(sum(i["flexibilidade_kw"] for i in itens), 2)
    return {
        "cliente_id": cliente.id,
        "participa_hoje": cliente.participa_hoje,
        "flexibilidade_kw": total,
        "disponivel_hoje_kw": total if cliente.participa_hoje else 0.0,
        "equipamentos": itens,
    }
