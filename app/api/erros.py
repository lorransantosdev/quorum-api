from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.aplicacao.erros import Conflito, NaoEncontrado
from app.dominio.erros import RegraViolada


def registrar_tratadores(app: FastAPI):
    @app.exception_handler(RegraViolada)
    async def regra_violada(request: Request, exc: RegraViolada):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(NaoEncontrado)
    async def nao_encontrado(request: Request, exc: NaoEncontrado):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(Conflito)
    async def conflito(request: Request, exc: Conflito):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(IntegrityError)
    async def integridade(request: Request, exc: IntegrityError):
        return JSONResponse(status_code=409, content={"detail": "Operação viola a integridade dos dados"})
