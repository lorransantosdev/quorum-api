from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.aplicacao import despachos
from app.api.esquemas import ERRO_404, ERRO_422, DespachoEntrada, DespachoSaida
from app.infraestrutura.db import get_session

router = APIRouter(prefix="/despachos", tags=["Despachos"])


@router.post(
    "",
    response_model=DespachoSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um despacho da usina virtual e planeja os acionamentos",
    description=(
        "Escolhe os equipamentos de maior flexibilidade primeiro até chegar na potência pedida. "
        "Clientes com 'hoje não' ficam de fora. Status: ATENDIDO, PARCIAL ou SEM_CAPACIDADE."
    ),
    responses=ERRO_422,
)
def criar(dados: DespachoEntrada, session: Session = Depends(get_session)):
    return DespachoSaida.model_validate(despachos.criar_despacho(session, dados.model_dump()))


@router.get(
    "",
    response_model=list[DespachoSaida],
    summary="Lista os despachos (mais recentes primeiro)",
    responses=ERRO_422,
)
def listar(
    pagina: int = Query(1, ge=1),
    tamanho: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    return [DespachoSaida.model_validate(d) for d in despachos.listar_despachos(session, pagina, tamanho)]


@router.get("/{despacho_id}", response_model=DespachoSaida, summary="Busca um despacho pelo id", responses=ERRO_404)
def buscar(despacho_id: int, session: Session = Depends(get_session)):
    return DespachoSaida.model_validate(despachos.buscar_despacho(session, despacho_id))
