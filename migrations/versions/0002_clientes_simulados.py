"""carrega clientes simulados de Sao Paulo

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-04
"""
from datetime import datetime, timedelta, timezone

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

FUSO_SP = timezone(timedelta(hours=-3))

# dados ficticios, nenhum desses comercios existe de verdade
CLIENTES = [
    ("Mercado Bom Preço – Vila Mariana", "SUPERMERCADO", "00.000.000/0001-01", 300),
    ("Academia Movimento – Tatuapé", "ACADEMIA", "00.000.000/0001-02", 150),
    ("Clínica Vida – Lapa", "CLINICA", "00.000.000/0001-03", 120),
    ("Padaria Pão Dourado – Mooca", "PADARIA", "00.000.000/0001-04", 75),
    ("Escola Aprender – Butantã", "ESCOLA", "00.000.000/0001-05", 200),
]

EQUIPAMENTOS = [
    ("00.000.000/0001-01", "CAMARA_FRIA", "Elgin", 60, None),
    ("00.000.000/0001-01", "BATERIA", "BYD", 100, 80),
    ("00.000.000/0001-01", "AR_CONDICIONADO", "Daikin", 40, None),
    ("00.000.000/0001-02", "AR_CONDICIONADO", "Midea", 50, None),
    ("00.000.000/0001-02", "CARREGADOR_VE", "WEG", 22, None),
    ("00.000.000/0001-03", "BATERIA", "WEG", 60, 15),
    ("00.000.000/0001-03", "AR_CONDICIONADO", "LG", 30, None),
    ("00.000.000/0001-04", "CAMARA_FRIA", "Gelopar", 15, None),
    ("00.000.000/0001-05", "CARREGADOR_VE", "ABB", 22, None),
    ("00.000.000/0001-05", "BATERIA", "Moura", 80, 65),
]

MEDICOES = [
    ("00.000.000/0001-01", datetime(2026, 11, 10, 14, 0, tzinfo=FUSO_SP), 250, "NORMAL", 0),
    ("00.000.000/0001-01", datetime(2026, 11, 10, 18, 30, tzinfo=FUSO_SP), 330, "ULTRAPASSAGEM", 15),
    ("00.000.000/0001-02", datetime(2026, 11, 11, 18, 30, tzinfo=FUSO_SP), 140, "ATENCAO", 0),
    ("00.000.000/0001-04", datetime(2026, 11, 11, 18, 45, tzinfo=FUSO_SP), 80, "ULTRAPASSAGEM", 1.25),
    ("00.000.000/0001-05", datetime(2026, 11, 12, 18, 30, tzinfo=FUSO_SP), 150, "NORMAL", 0),
]


def upgrade():
    cliente = sa.table(
        "cliente",
        sa.column("nome", sa.String),
        sa.column("segmento", sa.String),
        sa.column("cnpj", sa.String),
        sa.column("demanda_contratada_kw", sa.Float),
    )
    op.bulk_insert(
        cliente,
        [{"nome": n, "segmento": s, "cnpj": c, "demanda_contratada_kw": d} for n, s, c, d in CLIENTES],
    )

    for cnpj, tipo, marca, potencia, carga in EQUIPAMENTOS:
        op.execute(
            sa.text(
                "INSERT INTO equipamento (cliente_id, tipo, marca, potencia_kw, carga_percentual, ativo) "
                "SELECT id, :tipo, :marca, :potencia, :carga, true FROM cliente WHERE cnpj = :cnpj"
            ).bindparams(
                sa.bindparam("carga", value=carga, type_=sa.Float),
                tipo=tipo,
                marca=marca,
                potencia=potencia,
                cnpj=cnpj,
            )
        )

    for cnpj, momento, demanda, situacao, excedente in MEDICOES:
        op.execute(
            sa.text(
                "INSERT INTO medicao (cliente_id, momento, demanda_kw, situacao, excedente_kw) "
                "SELECT id, :momento, :demanda, :situacao, :excedente FROM cliente WHERE cnpj = :cnpj"
            ).bindparams(
                sa.bindparam("momento", value=momento, type_=sa.DateTime(timezone=True)),
                demanda=demanda,
                situacao=situacao,
                excedente=excedente,
                cnpj=cnpj,
            )
        )


def downgrade():
    # equipamentos e medicoes saem junto pelo ON DELETE CASCADE
    cnpjs = [c[2] for c in CLIENTES]
    op.execute(
        sa.text("DELETE FROM cliente WHERE cnpj IN :cnpjs").bindparams(sa.bindparam("cnpjs", value=cnpjs, expanding=True))
    )
