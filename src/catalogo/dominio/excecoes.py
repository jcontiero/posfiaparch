class ServicoNaoEncontradoError(Exception):
    def __init__(self):
        super().__init__("Serviço não encontrado")


class ServicoEmUsoError(Exception):
    def __init__(self):
        super().__init__("Serviço está em uso e não pode ser removido")
