from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.aplicacao import equipamentos
from app.api.esquemas import ERRO_404, ERRO_409, ERRO_422, EquipamentoEntrada, EquipamentoSaida, FlexibilidadeSaida
from app.infraestrutura.db import get_session

router = APIRouter(tags=["Equipamentos"])


@router.post(
    "/clientes/{cliente_id}/equipamentos",
    response_model=EquipamentoSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Conecta um equipamento ao cliente",
    responses={**ERRO_404, **ERRO_422},
)
def cadastrar(cliente_id: int, dados: EquipamentoEntrada, session: Session = Depends(get_session)):
    modelo = equipamentos.cadastrar_equipamento(session, cliente_id, dados.model_dump())
    return EquipamentoSaida.model_validate(modelo)


@router.get(
    "/clientes/{cliente_id}/equipamentos",
    response_model=list[EquipamentoSaida],
    summary="Lista os equipamentos de um cliente",
    responses=ERRO_404,
)
def listar(cliente_id: int, session: Session = Depends(get_session)):
    return [EquipamentoSaida.model_validate(m) for m in equipamentos.listar_equipamentos(session, cliente_id)]


@router.delete(
    "/equipamentos/{equipamento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desconecta (remove) um equipamento",
    responses={**ERRO_404, **ERRO_409},
)
def remover(equipamento_id: int, session: Session = Depends(get_session)):
    equipamentos.remover_equipamento(session, equipamento_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/clientes/{cliente_id}/flexibilidade",
    response_model=FlexibilidadeSaida,
    summary="Quanto o cliente consegue liberar no pico",
    description=(
        "Bateria: potência total se carga > 20% (reserva para apagão). Carregador VE: potência total (adia a recarga). "
        "Ar-condicionado: 30%. Câmara fria: 20%. Equipamento inativo: 0."
    ),
    responses=ERRO_404,
)
def flexibilidade(cliente_id: int, session: Session = Depends(get_session)):
    return FlexibilidadeSaida(**equipamentos.flexibilidade_do_cliente(session, cliente_id))
