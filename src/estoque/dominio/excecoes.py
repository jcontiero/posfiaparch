class EstoqueInsuficienteError(Exception):
    def __init__(self, nome: str, solicitado: int, disponivel: int):
        super().__init__(
            f"Estoque insuficiente para '{nome}': solicitado {solicitado}, disponível {disponivel}"
        )


class PecaNaoEncontradaError(Exception):
    def __init__(self, identificador):
        super().__init__(f"Peça não encontrada: {identificador}")


class CodigoPecaDuplicadoError(Exception):
    def __init__(self, codigo: str):
        super().__init__(f"Já existe uma peça com o código: {codigo}")
