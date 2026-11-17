from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infraestrutura.db import Base


class ClienteModelo(Base):
    __tablename__ = "cliente"
    __table_args__ = (UniqueConstraint("cnpj", name="uq_cliente_cnpj"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    segmento: Mapped[str] = mapped_column(String(20))
    cnpj: Mapped[str | None] = mapped_column(String(18))
    bairro: Mapped[str | None] = mapped_column(String(60))
    demanda_contratada_kw: Mapped[float] = mapped_column(Float)
    participa_hoje: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    equipamentos: Mapped[list["EquipamentoModelo"]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan", passive_deletes=True
    )
    medicoes: Mapped[list["MedicaoModelo"]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan", passive_deletes=True
    )


class EquipamentoModelo(Base):
    __tablename__ = "equipamento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id", ondelete="CASCADE"), index=True)
    tipo: Mapped[str] = mapped_column(String(20))
    marca: Mapped[str] = mapped_column(String(60))
    potencia_kw: Mapped[float] = mapped_column(Float)
    carga_percentual: Mapped[float | None] = mapped_column(Float)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    cliente: Mapped[ClienteModelo] = relationship(back_populates="equipamentos")


class MedicaoModelo(Base):
    __tablename__ = "medicao"
    __table_args__ = (Index("ix_medicao_cliente_momento", "cliente_id", "momento"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id", ondelete="CASCADE"))
    momento: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    demanda_kw: Mapped[float] = mapped_column(Float)
    situacao: Mapped[str] = mapped_column(String(15))
    excedente_kw: Mapped[float] = mapped_column(Float, default=0)

    cliente: Mapped[ClienteModelo] = relationship(back_populates="medicoes")


class DespachoModelo(Base):
    __tablename__ = "despacho"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    descricao: Mapped[str | None] = mapped_column(String(120))
    potencia_solicitada_kw: Mapped[float] = mapped_column(Float)
    potencia_atendida_kw: Mapped[float] = mapped_column(Float)
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duracao_min: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(15))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    acionamentos: Mapped[list["AcionamentoModelo"]] = relationship(
        back_populates="despacho", cascade="all, delete-orphan", order_by="AcionamentoModelo.id"
    )


class AcionamentoModelo(Base):
    __tablename__ = "acionamento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    despacho_id: Mapped[int] = mapped_column(ForeignKey("despacho.id", ondelete="CASCADE"), index=True)
    equipamento_id: Mapped[int] = mapped_column(ForeignKey("equipamento.id", ondelete="RESTRICT"), index=True)
    potencia_kw: Mapped[float] = mapped_column(Float)

    despacho: Mapped[DespachoModelo] = relationship(back_populates="acionamentos")
    equipamento: Mapped[EquipamentoModelo] = relationship()
