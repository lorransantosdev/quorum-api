import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.infraestrutura import modelos  # noqa: F401
from app.infraestrutura.db import Base, get_session
from main import app


def criar_engine_de_teste():
    url = os.getenv("TEST_DATABASE_URL")
    if url:
        return create_engine(url)

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def ligar_fks(conexao, _):
        conexao.execute("PRAGMA foreign_keys=ON")

    return engine


@pytest.fixture
def engine():
    engine = criar_engine_de_teste()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def api(engine):
    Sessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def sessao_de_teste():
        session = Sessao()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = sessao_de_teste
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()
