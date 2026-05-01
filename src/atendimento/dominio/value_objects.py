import re
from dataclasses import dataclass
from enum import Enum


REGEX_PLACA = re.compile(r'^[A-Z]{3}[0-9]{4}$|^[A-Z]{3}[0-9][A-Z][0-9]{2}$')

TRANSICOES_VALIDAS: dict


class StatusOS(str, Enum):
    RECEBIDA = "RECEBIDA"
    EM_DIAGNOSTICO = "EM_DIAGNOSTICO"
    AGUARDANDO_ORCAMENTO = "AGUARDANDO_ORCAMENTO"
    AGUARDANDO_APROVACAO = "AGUARDANDO_APROVACAO"
    EM_EXECUCAO = "EM_EXECUCAO"
    SERVICOS_CONCLUIDOS = "SERVICOS_CONCLUIDOS"
    FINALIZADA = "FINALIZADA"
    ENTREGUE = "ENTREGUE"
    CANCELADA = "CANCELADA"


TRANSICOES_VALIDAS = {
    StatusOS.RECEBIDA:               [StatusOS.EM_DIAGNOSTICO],
    StatusOS.EM_DIAGNOSTICO:         [StatusOS.AGUARDANDO_ORCAMENTO],
    StatusOS.AGUARDANDO_ORCAMENTO:   [StatusOS.AGUARDANDO_APROVACAO],
    StatusOS.AGUARDANDO_APROVACAO:   [StatusOS.EM_EXECUCAO, StatusOS.CANCELADA],
    StatusOS.EM_EXECUCAO:            [StatusOS.SERVICOS_CONCLUIDOS],
    StatusOS.SERVICOS_CONCLUIDOS:    [StatusOS.FINALIZADA],
    StatusOS.FINALIZADA:             [StatusOS.ENTREGUE],
    StatusOS.ENTREGUE:               [],
    StatusOS.CANCELADA:              [],
}


@dataclass(frozen=True)
class CPF:
    valor: str

    def __post_init__(self):
        limpo = re.sub(r'\D', '', self.valor)
        if not self._valido(limpo):
            raise ValueError(f"CPF inválido: {self.valor}")
        object.__setattr__(self, 'valor', limpo)

    def _valido(self, cpf: str) -> bool:
        if len(cpf) != 11 or len(set(cpf)) == 1:
            return False
        for i in range(9, 11):
            soma = sum(int(cpf[j]) * (i + 1 - j) for j in range(i))
            digito = (soma * 10 % 11) % 10
            if digito != int(cpf[i]):
                return False
        return True

    def __str__(self):
        v = self.valor
        return f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:]}"


@dataclass(frozen=True)
class CNPJ:
    valor: str

    def __post_init__(self):
        limpo = re.sub(r'\D', '', self.valor)
        if not self._valido(limpo):
            raise ValueError(f"CNPJ inválido: {self.valor}")
        object.__setattr__(self, 'valor', limpo)

    def _valido(self, cnpj: str) -> bool:
        if len(cnpj) != 14 or len(set(cnpj)) == 1:
            return False
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        for pesos in (pesos1, pesos2):
            soma = sum(int(cnpj[i]) * pesos[i] for i in range(len(pesos)))
            resto = soma % 11
            digito = 0 if resto < 2 else 11 - resto
            if digito != int(cnpj[len(pesos)]):
                return False
        return True


@dataclass(frozen=True)
class Placa:
    valor: str

    def __post_init__(self):
        formatado = self.valor.upper().strip()
        if not REGEX_PLACA.match(formatado):
            raise ValueError(f"Placa inválida: {self.valor}")
        object.__setattr__(self, 'valor', formatado)
