from sqlalchemy.orm import Session

from app.aplicacao.erros import ClienteNaoEncontrado, Conflito
from app.dominio.cliente import Cliente
from app.infraestrutura.modelos import ClienteModelo
from app.infraestrutura.repositorios import ClienteRepositorio


def listar_clientes(session: Session, pagina: int, tamanho: int, segmento: str | None = None):
    return ClienteRepositorio(session).listar(pagina, tamanho, segmento)


def buscar_cliente(session: Session, cliente_id: int) -> ClienteModelo:
    modelo = ClienteRepositorio(session).buscar(cliente_id)
    if modelo is None:
        raise ClienteNaoEncontrado(cliente_id)
    return modelo


def _verificar_cnpj(repo: ClienteRepositorio, cnpj: str | None, cliente_id: int | None = None):
    if not cnpj:
        return
    existente = repo.buscar_por_cnpj(cnpj)
    if existente and existente.id != cliente_id:
        raise Conflito(f"Já existe um cliente com o CNPJ {cnpj}")


def _copiar(cliente: Cliente, modelo: ClienteModelo):
    modelo.nome = cliente.nome.strip()
    modelo.segmento = cliente.segmento.value
    modelo.cnpj = cliente.cnpj
    modelo.bairro = cliente.bairro
    modelo.demanda_contratada_kw = cliente.demanda_contratada_kw
    modelo.participa_hoje = cliente.participa_hoje


def criar_cliente(session: Session, dados: dict) -> ClienteModelo:
    cliente = Cliente(**dados)
    repo = ClienteRepositorio(session)
    _verificar_cnpj(repo, cliente.cnpj)
    modelo = ClienteModelo()
    _copiar(cliente, modelo)
    return repo.salvar(modelo)


def atualizar_cliente(session: Session, cliente_id: int, dados: dict) -> ClienteModelo:
    modelo = buscar_cliente(session, cliente_id)
    cliente = Cliente(**dados, participa_hoje=modelo.participa_hoje, id=cliente_id)
    repo = ClienteRepositorio(session)
    _verificar_cnpj(repo, cliente.cnpj, cliente_id)
    _copiar(cliente, modelo)
    return repo.salvar(modelo)


def alterar_participacao(session: Session, cliente_id: int, participa_hoje: bool) -> ClienteModelo:
    modelo = buscar_cliente(session, cliente_id)
    modelo.participa_hoje = participa_hoje
    return ClienteRepositorio(session).salvar(modelo)


def remover_cliente(session: Session, cliente_id: int):
    modelo = buscar_cliente(session, cliente_id)
    repo = ClienteRepositorio(session)
    if repo.participou_de_despacho(cliente_id):
        raise Conflito("Cliente tem equipamentos que já participaram de despachos e não pode ser removido")
    repo.remover(modelo)
