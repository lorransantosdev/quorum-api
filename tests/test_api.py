from app.infraestrutura.db import get_session
from main import app

MERCADO = {
    "nome": "Mercado Teste – Pinheiros",
    "segmento": "SUPERMERCADO",
    "cnpj": "00.000.000/0009-01",
    "bairro": "Pinheiros",
    "demanda_contratada_kw": 300,
}


def criar_cliente(api, **dados):
    resposta = api.post("/clientes", json={**MERCADO, **dados})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def criar_equipamento(api, cliente_id, **dados):
    corpo = {"tipo": "BATERIA", "marca": "BYD", "potencia_kw": 100, "carga_percentual": 80, **dados}
    resposta = api.post(f"/clientes/{cliente_id}/equipamentos", json=corpo)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def criar_despacho(api, **dados):
    corpo = {"potencia_solicitada_kw": 120, "inicio": "2026-11-18T18:30:00-03:00", "duracao_min": 60, **dados}
    return api.post("/despachos", json=corpo)


def test_health_com_banco_ok(api):
    resposta = api.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "banco": "ok"}


def test_health_com_banco_fora(api):
    class SessaoQuebrada:
        def execute(self, *args):
            raise ConnectionError("banco caiu")

    app.dependency_overrides[get_session] = lambda: SessaoQuebrada()
    resposta = api.get("/health")
    assert resposta.status_code == 503
    assert resposta.json()["banco"] == "indisponivel"


def test_criar_cliente(api):
    corpo = criar_cliente(api)
    assert corpo["id"] > 0
    assert corpo["nome"] == MERCADO["nome"]
    assert corpo["participa_hoje"] is True
    assert corpo["bairro"] == "Pinheiros"


def test_criar_cliente_com_demanda_zero_viola_regra(api):
    resposta = api.post("/clientes", json={**MERCADO, "demanda_contratada_kw": 0})
    assert resposta.status_code == 422
    assert "demanda contratada" in resposta.json()["detail"]


def test_criar_cliente_com_cnpj_repetido(api):
    criar_cliente(api)
    resposta = api.post("/clientes", json=MERCADO)
    assert resposta.status_code == 409
    assert "CNPJ" in resposta.json()["detail"]


def test_buscar_cliente_inexistente(api):
    resposta = api.get("/clientes/999")
    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Cliente 999 não encontrado"}


def test_listar_clientes_paginado_e_filtrado(api):
    for i in range(3):
        criar_cliente(api, nome=f"Mercado {i}", cnpj=f"00.000.000/000{i}-10")
    criar_cliente(api, nome="Academia X", segmento="ACADEMIA", cnpj="00.000.000/0005-10")

    pagina = api.get("/clientes", params={"pagina": 2, "tamanho": 2}).json()
    assert pagina["total"] == 4
    assert [c["nome"] for c in pagina["itens"]] == ["Mercado 2", "Academia X"]

    academias = api.get("/clientes", params={"segmento": "ACADEMIA"}).json()
    assert academias["total"] == 1
    assert academias["itens"][0]["segmento"] == "ACADEMIA"


def test_listar_clientes_tamanho_acima_do_maximo(api):
    assert api.get("/clientes", params={"tamanho": 101}).status_code == 422


def test_atualizar_cliente(api):
    cliente = criar_cliente(api)
    resposta = api.put(f"/clientes/{cliente['id']}", json={**MERCADO, "demanda_contratada_kw": 350})
    assert resposta.status_code == 200
    assert resposta.json()["demanda_contratada_kw"] == 350
    assert api.get(f"/clientes/{cliente['id']}").json()["demanda_contratada_kw"] == 350


def test_atualizar_cliente_inexistente(api):
    resposta = api.put("/clientes/999", json=MERCADO)
    assert resposta.status_code == 404


def test_botao_hoje_nao(api):
    cliente = criar_cliente(api)
    resposta = api.patch(f"/clientes/{cliente['id']}/participacao", json={"participa_hoje": False})
    assert resposta.status_code == 200
    assert resposta.json()["participa_hoje"] is False


def test_remover_cliente_apaga_equipamentos_e_medicoes(api, engine):
    cliente = criar_cliente(api)
    criar_equipamento(api, cliente["id"])
    api.post(f"/clientes/{cliente['id']}/medicoes", json={"momento": "2026-11-10T18:30:00-03:00", "demanda_kw": 200})

    resposta = api.delete(f"/clientes/{cliente['id']}")
    assert resposta.status_code == 204
    assert api.get(f"/clientes/{cliente['id']}").status_code == 404

    with engine.connect() as conexao:
        from sqlalchemy import text

        assert conexao.execute(text("SELECT count(*) FROM equipamento")).scalar() == 0
        assert conexao.execute(text("SELECT count(*) FROM medicao")).scalar() == 0


def test_equipamentos_e_flexibilidade(api):
    cliente = criar_cliente(api)
    criar_equipamento(api, cliente["id"])
    criar_equipamento(api, cliente["id"], tipo="AR_CONDICIONADO", marca="Daikin", potencia_kw=40, carga_percentual=None)

    lista = api.get(f"/clientes/{cliente['id']}/equipamentos").json()
    assert [e["tipo"] for e in lista] == ["BATERIA", "AR_CONDICIONADO"]

    flex = api.get(f"/clientes/{cliente['id']}/flexibilidade").json()
    assert flex["flexibilidade_kw"] == 112
    assert flex["disponivel_hoje_kw"] == 112
    assert [e["flexibilidade_kw"] for e in flex["equipamentos"]] == [100, 12]


def test_bateria_sem_carga_viola_regra(api):
    cliente = criar_cliente(api)
    resposta = api.post(
        f"/clientes/{cliente['id']}/equipamentos", json={"tipo": "BATERIA", "marca": "BYD", "potencia_kw": 50}
    )
    assert resposta.status_code == 422
    assert resposta.json()["detail"] == "Bateria precisa informar carga_percentual"


def test_equipamento_para_cliente_inexistente(api):
    resposta = api.post("/clientes/999/equipamentos", json={"tipo": "CARREGADOR_VE", "marca": "ABB", "potencia_kw": 22})
    assert resposta.status_code == 404


def test_medicao_com_ultrapassagem(api):
    cliente = criar_cliente(api)
    resposta = api.post(
        f"/clientes/{cliente['id']}/medicoes", json={"momento": "2026-11-10T18:30:00-03:00", "demanda_kw": 330}
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["situacao"] == "ULTRAPASSAGEM"
    assert corpo["excedente_kw"] == 15
    assert corpo["momento"] == "2026-11-10T18:30:00-03:00"


def test_medicao_negativa_e_falha_do_medidor(api):
    cliente = criar_cliente(api)
    resposta = api.post(
        f"/clientes/{cliente['id']}/medicoes", json={"momento": "2026-11-10T18:30:00-03:00", "demanda_kw": -3}
    )
    assert resposta.status_code == 422
    assert "falha do medidor" in resposta.json()["detail"]


def test_listar_medicoes_por_periodo_mais_recentes_primeiro(api):
    cliente = criar_cliente(api)
    for hora, demanda in [("14:00", 200), ("18:30", 290), ("20:00", 150)]:
        api.post(
            f"/clientes/{cliente['id']}/medicoes",
            json={"momento": f"2026-11-10T{hora}:00-03:00", "demanda_kw": demanda},
        )

    resposta = api.get(
        f"/clientes/{cliente['id']}/medicoes",
        params={"de": "2026-11-10T18:00:00-03:00", "ate": "2026-11-10T21:00:00-03:00"},
    )
    assert resposta.status_code == 200
    assert [m["demanda_kw"] for m in resposta.json()] == [150, 290]
    assert [m["situacao"] for m in resposta.json()] == ["NORMAL", "ATENCAO"]


def test_listar_medicoes_com_periodo_invertido(api):
    cliente = criar_cliente(api)
    resposta = api.get(
        f"/clientes/{cliente['id']}/medicoes",
        params={"de": "2026-11-11T00:00:00-03:00", "ate": "2026-11-10T00:00:00-03:00"},
    )
    assert resposta.status_code == 422
    assert "de" in resposta.json()["detail"]


def test_ultrapassagens_traz_nome_do_cliente(api):
    mercado = criar_cliente(api)
    padaria = criar_cliente(api, nome="Padaria Teste", segmento="PADARIA", cnpj="00.000.000/0009-02", demanda_contratada_kw=75)
    api.post(f"/clientes/{mercado['id']}/medicoes", json={"momento": "2026-11-10T18:30:00-03:00", "demanda_kw": 200})
    api.post(f"/clientes/{padaria['id']}/medicoes", json={"momento": "2026-11-11T18:45:00-03:00", "demanda_kw": 80})
    api.post(f"/clientes/{padaria['id']}/medicoes", json={"momento": "2026-12-01T18:45:00-03:00", "demanda_kw": 90})

    resposta = api.get(
        "/medicoes/ultrapassagens", params={"de": "2026-11-01T00:00:00-03:00", "ate": "2026-11-30T23:59:59-03:00"}
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["cliente_nome"] == "Padaria Teste"
    assert corpo[0]["excedente_kw"] == 1.25


def test_despacho_ignora_cliente_que_apertou_hoje_nao(api):
    mercado = criar_cliente(api)
    academia = criar_cliente(api, nome="Academia", segmento="ACADEMIA", cnpj="00.000.000/0009-03")
    bateria = criar_equipamento(api, mercado["id"], potencia_kw=100)
    carregador = criar_equipamento(api, mercado["id"], tipo="CARREGADOR_VE", marca="WEG", potencia_kw=22, carga_percentual=None)
    criar_equipamento(api, academia["id"], potencia_kw=200)
    api.patch(f"/clientes/{academia['id']}/participacao", json={"participa_hoje": False})

    resposta = criar_despacho(api, potencia_solicitada_kw=110)
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "ATENDIDO"
    assert corpo["potencia_atendida_kw"] == 110
    assert corpo["acionamentos"] == [
        {"equipamento_id": bateria["id"], "potencia_kw": 100},
        {"equipamento_id": carregador["id"], "potencia_kw": 10},
    ]

    assert api.get(f"/despachos/{corpo['id']}").json() == corpo


def test_despacho_sem_capacidade(api):
    resposta = criar_despacho(api)
    assert resposta.status_code == 201
    assert resposta.json()["status"] == "SEM_CAPACIDADE"
    assert resposta.json()["acionamentos"] == []


def test_despacho_com_duracao_invalida(api):
    resposta = criar_despacho(api, duracao_min=200)
    assert resposta.status_code == 422
    assert "duração" in resposta.json()["detail"]


def test_listar_despachos_mais_recentes_primeiro(api):
    criar_despacho(api, inicio="2026-11-17T18:30:00-03:00", descricao="ontem")
    criar_despacho(api, inicio="2026-11-18T18:30:00-03:00", descricao="hoje")
    resposta = api.get("/despachos")
    assert resposta.status_code == 200
    assert [d["descricao"] for d in resposta.json()] == ["hoje", "ontem"]


def test_buscar_despacho_inexistente(api):
    resposta = api.get("/despachos/999")
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Despacho 999 não encontrado"


def test_nao_remove_cliente_nem_equipamento_que_ja_participou_de_despacho(api):
    cliente = criar_cliente(api)
    equipamento = criar_equipamento(api, cliente["id"])
    criar_despacho(api, potencia_solicitada_kw=50)

    resposta = api.delete(f"/clientes/{cliente['id']}")
    assert resposta.status_code == 409
    assert "despachos" in resposta.json()["detail"]

    resposta = api.delete(f"/equipamentos/{equipamento['id']}")
    assert resposta.status_code == 409


def test_remover_equipamento(api):
    cliente = criar_cliente(api)
    equipamento = criar_equipamento(api, cliente["id"])
    assert api.delete(f"/equipamentos/{equipamento['id']}").status_code == 204
    assert api.delete(f"/equipamentos/{equipamento['id']}").status_code == 404
    assert api.get(f"/clientes/{cliente['id']}/equipamentos").json() == []


def test_openapi_documenta_rotas_e_erros(api):
    doc = api.get("/openapi.json").json()
    assert doc["info"]["title"] == "Quorum · API"
    rota = doc["paths"]["/clientes/{cliente_id}"]["get"]
    assert rota["tags"] == ["Clientes"]
    assert "404" in rota["responses"]
    assert "409" in doc["paths"]["/clientes/{cliente_id}"]["delete"]["responses"]
