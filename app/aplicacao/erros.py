class NaoEncontrado(Exception):
    pass


class ClienteNaoEncontrado(NaoEncontrado):
    def __init__(self, cliente_id: int):
        super().__init__(f"Cliente {cliente_id} não encontrado")


class EquipamentoNaoEncontrado(NaoEncontrado):
    def __init__(self, equipamento_id: int):
        super().__init__(f"Equipamento {equipamento_id} não encontrado")


class DespachoNaoEncontrado(NaoEncontrado):
    def __init__(self, despacho_id: int):
        super().__init__(f"Despacho {despacho_id} não encontrado")


class Conflito(Exception):
    pass
