from src.atendimento.dominio.value_objects import StatusOS


class TransicaoDeStatusInvalidaError(Exception):
    def __init__(self, atual: StatusOS, tentada: StatusOS):
        super().__init__(
            f"Transição inválida: OS em '{atual.value}' não pode ir para '{tentada.value}'"
        )


class TransicaoInvalidaError(TransicaoDeStatusInvalidaError):
    pass


class OsSemServicosError(Exception):
    def __init__(self):
        super().__init__("Não é possível gerar orçamento sem serviços adicionados")


class ServicosNaoConcluidos(Exception):
    def __init__(self, quantidade: int):
        super().__init__(f"{quantidade} serviço(s) ainda não concluído(s)")


class ClienteNaoEncontradoError(Exception):
    def __init__(self, identificador: str):
        super().__init__(f"Cliente não encontrado: {identificador}")


class VeiculoNaoEncontradoError(Exception):
    def __init__(self, placa: str):
        super().__init__(f"Veículo não encontrado: {placa}")


class VeiculoComOsAtivaError(Exception):
    def __init__(self, placa: str):
        super().__init__(f"Veículo '{placa}' já possui uma ordem de serviço ativa")


class ClienteComOsAtivaError(Exception):
    def __init__(self):
        super().__init__(
            "Cliente possui ordens de serviço ativas e não pode ser removido"
        )


class DocumentoDuplicadoError(Exception):
    def __init__(self, documento: str):
        super().__init__(f"Documento já cadastrado: {documento}")


class PlacaDuplicadaError(Exception):
    def __init__(self, placa: str):
        super().__init__(f"Placa já cadastrada: {placa}")


class ItemNaoEncontradoError(Exception):
    def __init__(self, item_id):
        super().__init__(f"Item não encontrado na ordem de serviço: {item_id}")


class OrdemDeServicoNaoEncontradaError(Exception):
    def __init__(self, identificador: str):
        super().__init__(f"Ordem de serviço não encontrada: {identificador}")


class TokenDeAprovacaoInvalidoError(Exception):
    def __init__(self):
        super().__init__("Token de aprovação inválido")


class TokenDeAprovacaoExpiradoError(Exception):
    def __init__(self):
        super().__init__("Token de aprovação expirado")


class DocumentoClienteInvalidoError(Exception):
    def __init__(self):
        super().__init__("Cliente deve ter CPF ou CNPJ — nunca ambos ou nenhum")
