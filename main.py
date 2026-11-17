from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html

from app.api import rotas_clientes, rotas_despachos, rotas_equipamentos, rotas_medicoes, rotas_saude
from app.api.erros import registrar_tratadores

DESCRICAO = """
**Milhares de pontos. Uma só usina.**

O Quorum é uma usina virtual: conecta baterias, carregadores de carro elétrico, ar-condicionados e
câmaras frias de pequenos e médios comércios de São Paulo e coordena esses equipamentos no pico do
fim da tarde (~18h30). A rede recebe alívio sem ligar termelétrica e o comércio evita a multa de
ultrapassagem de demanda (REN ANEEL 1.000/2021).

Todos os dados desta API são **simulados** (comércios fictícios).
"""

TAGS = [
    {"name": "Clientes", "description": "Comércios participantes e o botão 'hoje não'."},
    {"name": "Equipamentos", "description": "Equipamentos conectados e quanto cada um consegue liberar no pico."},
    {"name": "Medições", "description": "Leituras de demanda e alerta de ultrapassagem."},
    {"name": "Despachos", "description": "Eventos da usina virtual e os equipamentos acionados."},
    {"name": "Saúde", "description": "Verificação usada pelo monitoramento."},
]

app = FastAPI(title="Quorum · API", version="1.0.0", description=DESCRICAO, openapi_tags=TAGS, redoc_url=None)


@app.get("/redoc", include_in_schema=False)
def redoc():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.5/bundles/redoc.standalone.js",
    )

registrar_tratadores(app)

app.include_router(rotas_clientes.router)
app.include_router(rotas_equipamentos.router)
app.include_router(rotas_medicoes.router)
app.include_router(rotas_despachos.router)
app.include_router(rotas_saude.router)
