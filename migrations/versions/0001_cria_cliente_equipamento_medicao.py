"""cria cliente, equipamento e medicao

Revision ID: 0001
Revises:
Create Date: 2026-11-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cliente",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("segmento", sa.String(20), nullable=False),
        sa.Column("cnpj", sa.String(18), nullable=True),
        sa.Column("demanda_contratada_kw", sa.Float, nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("cnpj", name="uq_cliente_cnpj"),
        sa.CheckConstraint("demanda_contratada_kw > 0", name="ck_cliente_demanda_positiva"),
    )

    op.create_table(
        "equipamento",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("cliente_id", sa.Integer, sa.ForeignKey("cliente.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("marca", sa.String(60), nullable=False),
        sa.Column("potencia_kw", sa.Float, nullable=False),
        sa.Column("carga_percentual", sa.Float, nullable=True),
        sa.Column("ativo", sa.Boolean, server_default=sa.true(), nullable=False),
        sa.CheckConstraint("potencia_kw > 0", name="ck_equipamento_potencia_positiva"),
    )
    op.create_index("ix_equipamento_cliente_id", "equipamento", ["cliente_id"])

    op.create_table(
        "medicao",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("cliente_id", sa.Integer, sa.ForeignKey("cliente.id", ondelete="CASCADE"), nullable=False),
        sa.Column("momento", sa.DateTime(timezone=True), nullable=False),
        sa.Column("demanda_kw", sa.Float, nullable=False),
        sa.Column("situacao", sa.String(15), nullable=False),
        sa.Column("excedente_kw", sa.Float, nullable=False, server_default="0"),
    )
    op.create_index("ix_medicao_cliente_momento", "medicao", ["cliente_id", "momento"])


def downgrade():
    op.drop_index("ix_medicao_cliente_momento", table_name="medicao")
    op.drop_table("medicao")
    op.drop_index("ix_equipamento_cliente_id", table_name="equipamento")
    op.drop_table("equipamento")
    op.drop_table("cliente")
