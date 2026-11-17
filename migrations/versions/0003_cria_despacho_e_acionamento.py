"""cria despacho e acionamento

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-08
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "despacho",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("descricao", sa.String(120), nullable=True),
        sa.Column("potencia_solicitada_kw", sa.Float, nullable=False),
        sa.Column("potencia_atendida_kw", sa.Float, nullable=False),
        sa.Column("inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duracao_min", sa.Integer, nullable=False),
        sa.Column("status", sa.String(15), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("duracao_min BETWEEN 15 AND 120", name="ck_despacho_duracao"),
    )
    op.create_index("ix_despacho_inicio", "despacho", ["inicio"])

    op.create_table(
        "acionamento",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("despacho_id", sa.Integer, sa.ForeignKey("despacho.id", ondelete="CASCADE"), nullable=False),
        sa.Column("equipamento_id", sa.Integer, sa.ForeignKey("equipamento.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("potencia_kw", sa.Float, nullable=False),
    )
    op.create_index("ix_acionamento_despacho_id", "acionamento", ["despacho_id"])
    op.create_index("ix_acionamento_equipamento_id", "acionamento", ["equipamento_id"])


def downgrade():
    op.drop_index("ix_acionamento_equipamento_id", table_name="acionamento")
    op.drop_index("ix_acionamento_despacho_id", table_name="acionamento")
    op.drop_table("acionamento")
    op.drop_index("ix_despacho_inicio", table_name="despacho")
    op.drop_table("despacho")
