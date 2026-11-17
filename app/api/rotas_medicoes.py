from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.aplicacao import medicoes
from app.api.esquemas import ERRO_404, ERRO_422, MedicaoEntrada, MedicaoSaida, UltrapassagemSaida
from app.infraestrutura.db import get_session

router = APIRouter(tags=["Medições"])


@router.post(
    "/clientes/{cliente_id}/medicoes",
    response_model=MedicaoSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Registra uma leitura de demanda do medidor",
    description="Classifica a leitura em NORMAL (< 90%), ATENCAO (90% a 105%) ou ULTRAPASSAGEM (> 105% do contratado).",
    responses={**ERRO_404, **ERRO_422},
)
def registrar(cliente_id: int, dados: MedicaoEntrada, session: Session = Depends(get_session)):
    modelo = medicoes.registrar_medicao(session, cliente_id, dados.momento, dados.demanda_kw)
    return MedicaoSaida.model_validate(modelo)


@router.get(
    "/clientes/{cliente_id}/medicoes",
    response_model=list[MedicaoSaida],
    summary="Lista as medições do cliente no período (mais recentes primeiro)",
    responses={**ERRO_404, **ERRO_422},
)
def listar(
    cliente_id: int,
    de: datetime | None = Query(None, description="Início do período (ISO 8601)"),
    ate: datetime | None = Query(None, description="Fim do período (ISO 8601)"),
    session: Session = Depends(get_session),
):
    return [MedicaoSaida.model_validate(m) for m in medicoes.listar_medicoes(session, cliente_id, de, ate)]


@router.get(
    "/medicoes/ultrapassagens",
    response_model=list[UltrapassagemSaida],
    summary="Lista todas as ultrapassagens de demanda no período, com o nome do cliente",
    responses=ERRO_422,
)
def ultrapassagens(
    de: datetime | None = Query(None, description="Início do período (ISO 8601)"),
    ate: datetime | None = Query(None, description="Fim do período (ISO 8601)"),
    session: Session = Depends(get_session),
):
    return [UltrapassagemSaida(**linha) for linha in medicoes.listar_ultrapassagens(session, de, ate)]
