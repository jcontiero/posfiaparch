from fastapi import FastAPI
from src.container import Container
from src.identidade.apresentacao.rotas import router as auth_router
from src.atendimento.apresentacao.rotas import router as atendimento_router
from src.catalogo.apresentacao.rotas import router as catalogo_router
from src.estoque.apresentacao.rotas import router as estoque_router
from src.relatorios.apresentacao.rotas import router as relatorios_router

from src.identidade.dominio.excecoes import CredenciaisInvalidasError
from src.atendimento.dominio.excecoes import (
    TransicaoInvalidaError,
    OsSemServicosError,
    ClienteNaoEncontradoError,
    VeiculoNaoEncontradoError,
    DocumentoDuplicadoError,
    DocumentoClienteInvalidoError,
    OrdemDeServicoNaoEncontradaError,
)
from src.estoque.dominio.excecoes import (
    EstoqueInsuficienteError,
    CodigoPecaDuplicadoError,
    ReposicaoInvalidaError,
)
from src.catalogo.dominio.excecoes import ServicoNaoEncontradoError
from src.shared.excecoes_http import (
    handler_credenciais_invalidas,
    handler_regra_negocio,
    handler_nao_encontrado,
    handler_conflito,
)


def criar_app(configuracoes=None) -> FastAPI:
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(
        title="Oficina Mecânica API",
        description="Sistema Integrado de Atendimento e Execução de Serviços",
        version="0.2.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.container = Container(configuracoes)

    @app.get("/health", tags=["health"])
    def health_check():
        return {"status": "ok"}

    app.add_exception_handler(CredenciaisInvalidasError, handler_credenciais_invalidas)
    app.add_exception_handler(TransicaoInvalidaError, handler_regra_negocio)
    app.add_exception_handler(OsSemServicosError, handler_regra_negocio)
    app.add_exception_handler(EstoqueInsuficienteError, handler_regra_negocio)
    app.add_exception_handler(ClienteNaoEncontradoError, handler_nao_encontrado)
    app.add_exception_handler(VeiculoNaoEncontradoError, handler_nao_encontrado)
    app.add_exception_handler(OrdemDeServicoNaoEncontradaError, handler_nao_encontrado)
    app.add_exception_handler(ServicoNaoEncontradoError, handler_nao_encontrado)
    app.add_exception_handler(DocumentoDuplicadoError, handler_conflito)
    app.add_exception_handler(DocumentoClienteInvalidoError, handler_regra_negocio)
    app.add_exception_handler(CodigoPecaDuplicadoError, handler_conflito)
    app.add_exception_handler(ReposicaoInvalidaError, handler_regra_negocio)

    app.include_router(auth_router)
    app.include_router(atendimento_router)
    app.include_router(catalogo_router)
    app.include_router(estoque_router)
    app.include_router(relatorios_router)

    return app


app = criar_app()
