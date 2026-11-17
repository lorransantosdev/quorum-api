from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.dominio.cliente import Cliente, SituacaoDemanda
from app.dominio.equipamento import Equipamento
from app.infraestrutura.modelos import (
    AcionamentoModelo,
    ClienteModelo,
    DespachoModelo,
    EquipamentoModelo,
    MedicaoModelo,
)


def cliente_para_dominio(modelo: ClienteModelo) -> Cliente:
    return Cliente(
        id=modelo.id,
        nome=modelo.nome,
        segmento=modelo.segmento,
        demanda_contratada_kw=modelo.demanda_contratada_kw,
        cnpj=modelo.cnpj,
        bairro=modelo.bairro,
        participa_hoje=modelo.participa_hoje,
    )


def equipamento_para_dominio(modelo: EquipamentoModelo) -> Equipamento:
    return Equipamento(
        id=modelo.id,
        cliente_id=modelo.cliente_id,
        tipo=modelo.tipo,
        marca=modelo.marca,
        potencia_kw=modelo.potencia_kw,
        carga_percentual=modelo.carga_percentual,
        ativo=modelo.ativo,
    )


class Repositorio:
    def __init__(self, session: Session):
        self.session = session

    def salvar(self, modelo):
        self.session.add(modelo)
        self.session.commit()
        self.session.refresh(modelo)
        return modelo

    def remover(self, modelo):
        self.session.delete(modelo)
        self.session.commit()


class ClienteRepositorio(Repositorio):
    def listar(self, pagina: int, tamanho: int, segmento: str | None = None):
        consulta = select(ClienteModelo)
        if segmento:
            consulta = consulta.where(ClienteModelo.segmento == segmento)
        total = self.session.scalar(select(func.count()).select_from(consulta.subquery()))
        itens = self.session.scalars(
            consulta.order_by(ClienteModelo.id).offset((pagina - 1) * tamanho).limit(tamanho)
        ).all()
        return itens, total

    def buscar(self, cliente_id: int) -> ClienteModelo | None:
        return self.session.get(ClienteModelo, cliente_id)

    def buscar_por_cnpj(self, cnpj: str) -> ClienteModelo | None:
        return self.session.scalar(select(ClienteModelo).where(ClienteModelo.cnpj == cnpj))

    def participou_de_despacho(self, cliente_id: int) -> bool:
        consulta = (
            select(func.count(AcionamentoModelo.id))
            .join(EquipamentoModelo, AcionamentoModelo.equipamento_id == EquipamentoModelo.id)
            .where(EquipamentoModelo.cliente_id == cliente_id)
        )
        return self.session.scalar(consulta) > 0


class EquipamentoRepositorio(Repositorio):
    def buscar(self, equipamento_id: int) -> EquipamentoModelo | None:
        return self.session.get(EquipamentoModelo, equipamento_id)

    def listar_do_cliente(self, cliente_id: int):
        consulta = select(EquipamentoModelo).where(EquipamentoModelo.cliente_id == cliente_id)
        return self.session.scalars(consulta.order_by(EquipamentoModelo.id)).all()

    def participou_de_despacho(self, equipamento_id: int) -> bool:
        consulta = select(func.count(AcionamentoModelo.id)).where(AcionamentoModelo.equipamento_id == equipamento_id)
        return self.session.scalar(consulta) > 0

    def elegiveis_para_despacho(self):
        consulta = (
            select(EquipamentoModelo)
            .join(ClienteModelo)
            .where(ClienteModelo.participa_hoje.is_(True), EquipamentoModelo.ativo.is_(True))
            .order_by(EquipamentoModelo.id)
        )
        return self.session.scalars(consulta).all()


class MedicaoRepositorio(Repositorio):
    def listar_do_cliente(self, cliente_id: int, de: datetime | None, ate: datetime | None):
        consulta = select(MedicaoModelo).where(MedicaoModelo.cliente_id == cliente_id)
        if de:
            consulta = consulta.where(MedicaoModelo.momento >= de)
        if ate:
            consulta = consulta.where(MedicaoModelo.momento <= ate)
        return self.session.scalars(consulta.order_by(MedicaoModelo.momento.desc())).all()

    def ultrapassagens(self, de: datetime | None, ate: datetime | None):
        consulta = (
            select(MedicaoModelo, ClienteModelo.nome, ClienteModelo.demanda_contratada_kw)
            .join(ClienteModelo, MedicaoModelo.cliente_id == ClienteModelo.id)
            .where(MedicaoModelo.situacao == SituacaoDemanda.ULTRAPASSAGEM.value)
        )
        if de:
            consulta = consulta.where(MedicaoModelo.momento >= de)
        if ate:
            consulta = consulta.where(MedicaoModelo.momento <= ate)
        return self.session.execute(consulta.order_by(MedicaoModelo.momento.desc())).all()


class DespachoRepositorio(Repositorio):
    def buscar(self, despacho_id: int) -> DespachoModelo | None:
        consulta = (
            select(DespachoModelo)
            .options(selectinload(DespachoModelo.acionamentos).selectinload(AcionamentoModelo.equipamento))
            .where(DespachoModelo.id == despacho_id)
        )
        return self.session.scalar(consulta)

    def listar(self, pagina: int, tamanho: int):
        consulta = (
            select(DespachoModelo)
            .options(selectinload(DespachoModelo.acionamentos).selectinload(AcionamentoModelo.equipamento))
            .order_by(DespachoModelo.inicio.desc(), DespachoModelo.id.desc())
            .offset((pagina - 1) * tamanho)
            .limit(tamanho)
        )
        return self.session.scalars(consulta).all()
