from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.aplicacao import clientes
from app.api.esquemas import (
    ERRO_404,
    ERRO_409,
    ERRO_422,
    ClienteEntrada,
    ClienteSaida,
    PaginaClientes,
    ParticipacaoEntrada,
)
from app.dominio.cliente import Segmento
from app.infraestrutura.db import get_session

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get(
    "",
    response_model=PaginaClientes,
    summary="Lista os clientes com paginação",
    description="Ordenado por id. Pode filtrar por segmento.",
    responses=ERRO_422,
)
def listar(
    pagina: int = Query(1, ge=1, description="Página, começando em 1"),
    tamanho: int = Query(20, ge=1, le=100, description="Itens por página (máx. 100)"),
    segmento: Segmento | None = Query(None, description="Filtra pelo segmento do comércio"),
    session: Session = Depends(get_session),
):
    itens, total = clientes.listar_clientes(session, pagina, tamanho, segmento.value if segmento else None)
    return PaginaClientes(
        itens=[ClienteSaida.model_validate(c) for c in itens], total=total, pagina=pagina, tamanho=tamanho
    )


@router.get("/{cliente_id}", response_model=ClienteSaida, summary="Busca um cliente pelo id", responses=ERRO_404)
def buscar(cliente_id: int, session: Session = Depends(get_session)):
    return ClienteSaida.model_validate(clientes.buscar_cliente(session, cliente_id))


@router.post(
    "",
    response_model=ClienteSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um cliente (comércio participante)",
    responses={**ERRO_409, **ERRO_422},
)
def criar(dados: ClienteEntrada, session: Session = Depends(get_session)):
    return ClienteSaida.model_validate(clientes.criar_cliente(session, dados.model_dump()))


@router.put(
    "/{cliente_id}",
    response_model=ClienteSaida,
    summary="Atualiza os dados de um cliente",
    responses={**ERRO_404, **ERRO_409, **ERRO_422},
)
def atualizar(cliente_id: int, dados: ClienteEntrada, session: Session = Depends(get_session)):
    return ClienteSaida.model_validate(clientes.atualizar_cliente(session, cliente_id, dados.model_dump()))


@router.delete(
    "/{cliente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um cliente",
    description=(
        "Remove o cliente junto com seus equipamentos e medições (ON DELETE CASCADE). "
        "Se algum equipamento já participou de um despacho, retorna 409 para não perder o histórico da usina."
    ),
    responses={**ERRO_404, **ERRO_409},
)
def remover(cliente_id: int, session: Session = Depends(get_session)):
    clientes.remover_cliente(session, cliente_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{cliente_id}/participacao",
    response_model=ClienteSaida,
    summary="Botão 'hoje não': liga ou desliga a participação do dia",
    responses={**ERRO_404, **ERRO_422},
)
def alterar_participacao(cliente_id: int, dados: ParticipacaoEntrada, session: Session = Depends(get_session)):
    return ClienteSaida.model_validate(clientes.alterar_participacao(session, cliente_id, dados.participa_hoje))
