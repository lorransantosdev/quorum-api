"""adiciona participa_hoje e bairro no cliente

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

BAIRROS = {
    "00.000.000/0001-01": "Vila Mariana",
    "00.000.000/0001-02": "Tatuapé",
    "00.000.000/0001-03": "Lapa",
    "00.000.000/0001-04": "Mooca",
    "00.000.000/0001-05": "Butantã",
}


def upgrade():
    op.add_column("cliente", sa.Column("participa_hoje", sa.Boolean, nullable=False, server_default=sa.true()))
    op.add_column("cliente", sa.Column("bairro", sa.String(60), nullable=True))

    for cnpj, bairro in BAIRROS.items():
        op.execute(
            sa.text("UPDATE cliente SET bairro = :bairro WHERE cnpj = :cnpj").bindparams(bairro=bairro, cnpj=cnpj)
        )


def downgrade():
    op.drop_column("cliente", "bairro")
    op.drop_column("cliente", "participa_hoje")
