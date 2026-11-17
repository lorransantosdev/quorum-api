from datetime import datetime, timedelta, timezone

import pytest

from app.dominio.cliente import Cliente, Segmento, SituacaoDemanda
from app.dominio.despacho import Despacho, StatusDespacho, planejar
from app.dominio.equipamento import Equipamento, TipoEquipamento
from app.dominio.erros import RegraViolada
from app.dominio.medicao import Medicao

PICO = datetime(2026, 11, 18, 18, 30, tzinfo=timezone(timedelta(hours=-3)))


def novo_cliente(demanda=100):
    return Cliente(nome="Padaria Teste", segmento=Segmento.PADARIA, demanda_contratada_kw=demanda)


def bateria(potencia=50, carga=80, **extra):
    return Equipamento(tipo=TipoEquipamento.BATERIA, marca="BYD", potencia_kw=potencia, carga_percentual=carga, **extra)


@pytest.mark.parametrize("demanda", [0, -10])
def test_cliente_com_demanda_contratada_invalida(demanda):
    with pytest.raises(RegraViolada):
        novo_cliente(demanda)


def test_cliente_sem_nome():
    with pytest.raises(RegraViolada):
        Cliente(nome="  ", segmento=Segmento.OUTRO, demanda_contratada_kw=100)


def test_cliente_participa_hoje_por_padrao():
    assert novo_cliente().participa_hoje is True


@pytest.mark.parametrize(
    "demanda, esperado",
    [
        (50, SituacaoDemanda.NORMAL),
        (89.99, SituacaoDemanda.NORMAL),
        (90, SituacaoDemanda.ATENCAO),
        (100, SituacaoDemanda.ATENCAO),
        (105, SituacaoDemanda.ATENCAO),
        (105.01, SituacaoDemanda.ULTRAPASSAGEM),
        (130, SituacaoDemanda.ULTRAPASSAGEM),
    ],
)
def test_classificar_demanda_respeita_tolerancia_de_5_porcento(demanda, esperado):
    assert novo_cliente(100).classificar_demanda(demanda) == esperado


def test_excedente_considera_a_tolerancia():
    cliente = novo_cliente(300)
    assert cliente.excedente_kw(330) == 15.0
    assert cliente.excedente_kw(310) == 0.0


@pytest.mark.parametrize("demanda", [-1, 10000.5])
def test_medicao_fora_da_faixa_do_sensor(demanda):
    with pytest.raises(RegraViolada):
        Medicao(novo_cliente(), PICO, demanda)


def test_medicao_classifica_ultrapassagem():
    medicao = Medicao(novo_cliente(75), PICO, 80)
    assert medicao.situacao == SituacaoDemanda.ULTRAPASSAGEM
    assert medicao.excedente_kw == 1.25


def test_bateria_acima_da_reserva_libera_potencia_total():
    assert bateria(potencia=100, carga=80).flexibilidade_kw() == 100


@pytest.mark.parametrize("carga", [0, 15, 20])
def test_bateria_na_reserva_minima_nao_libera_nada(carga):
    assert bateria(carga=carga).flexibilidade_kw() == 0


@pytest.mark.parametrize(
    "tipo, potencia, esperado",
    [
        (TipoEquipamento.CARREGADOR_VE, 22, 22),
        (TipoEquipamento.AR_CONDICIONADO, 40, 12),
        (TipoEquipamento.CAMARA_FRIA, 60, 12),
    ],
)
def test_flexibilidade_por_tipo(tipo, potencia, esperado):
    assert Equipamento(tipo=tipo, marca="WEG", potencia_kw=potencia).flexibilidade_kw() == esperado


def test_equipamento_inativo_nao_tem_flexibilidade():
    assert bateria(ativo=False).flexibilidade_kw() == 0


def test_carga_so_vale_para_bateria():
    with pytest.raises(RegraViolada):
        Equipamento(tipo=TipoEquipamento.CAMARA_FRIA, marca="Elgin", potencia_kw=10, carga_percentual=50)


@pytest.mark.parametrize("carga", [None, -5, 101])
def test_bateria_com_carga_invalida(carga):
    with pytest.raises(RegraViolada):
        bateria(carga=carga)


def test_equipamento_com_potencia_zero():
    with pytest.raises(RegraViolada):
        Equipamento(tipo=TipoEquipamento.CARREGADOR_VE, marca="ABB", potencia_kw=0)


@pytest.mark.parametrize("duracao", [10, 121])
def test_despacho_com_duracao_fora_do_limite(duracao):
    with pytest.raises(RegraViolada):
        Despacho(potencia_solicitada_kw=50, inicio=PICO, duracao_min=duracao)


def test_despacho_com_potencia_zero():
    with pytest.raises(RegraViolada):
        Despacho(potencia_solicitada_kw=0, inicio=PICO, duracao_min=30)


def test_planejar_aciona_maior_flexibilidade_primeiro():
    ar = Equipamento(tipo=TipoEquipamento.AR_CONDICIONADO, marca="LG", potencia_kw=40, id=1)
    carregador = Equipamento(tipo=TipoEquipamento.CARREGADOR_VE, marca="WEG", potencia_kw=22, id=2)
    bat = bateria(potencia=100, carga=80, id=3)

    plano = planejar(Despacho(110, PICO, 60), [ar, carregador, bat])

    assert plano.status == StatusDespacho.ATENDIDO
    assert plano.potencia_atendida_kw == 110
    assert [(a.equipamento.id, a.potencia_kw) for a in plano.acionamentos] == [(3, 100), (2, 10)]


def test_planejar_parcial_quando_falta_capacidade():
    plano = planejar(Despacho(500, PICO, 30), [bateria(potencia=100), bateria(potencia=50)])
    assert plano.status == StatusDespacho.PARCIAL
    assert plano.potencia_atendida_kw == 150


def test_planejar_sem_capacidade():
    plano = planejar(Despacho(50, PICO, 30), [bateria(carga=10), bateria(ativo=False)])
    assert plano.status == StatusDespacho.SEM_CAPACIDADE
    assert plano.acionamentos == []
    assert plano.potencia_atendida_kw == 0
