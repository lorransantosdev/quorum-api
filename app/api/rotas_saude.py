from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.esquemas import Saude
from app.infraestrutura.db import get_session

router = APIRouter(tags=["Saúde"])


@router.get(
    "/health",
    response_model=Saude,
    summary="Verifica se a API e o banco estão respondendo",
    description="Executa um SELECT 1 no PostgreSQL. Usado pelo monitoramento da infraestrutura Linux.",
    responses={503: {"model": Saude, "description": "Banco de dados indisponível"}},
)
def health(session: Session = Depends(get_session)):
    try:
        session.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "erro", "banco": "indisponivel"})
    return Saude(status="ok", banco="ok")
