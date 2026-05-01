class CredenciaisInvalidasError(Exception):
    def __init__(self):
        super().__init__("Email ou senha inválidos")
