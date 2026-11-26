"""Fixtures compartilhadas para os testes de unidade e integração."""

from pathlib import Path
from typing import Iterator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src import criar_app
from src.banco import BancoDados
from src.modelos import Produto, Usuario
from src.repositorios import (
    RepositorioPedido,
    RepositorioProduto,
    RepositorioUsuario,
)
from src.rotas.auxiliares import ContinerServicos
from src.servicos import (
    ServicoAutenticacao,
    ServicoCarrinho,
    ServicoCatalogo,
    ServicoPedido,
    SimuladorPagamento,
)


@pytest.fixture()
def banco_memoria() -> Iterator[BancoDados]:
    """Cria um banco SQLite em memória isolado por teste."""
    banco = BancoDados(":memory:")
    banco.inicializar()
    yield banco
    banco.fechar()


@pytest.fixture()
def servicos(banco_memoria: BancoDados) -> ContinerServicos:
    """Instancia todos os serviços conectados ao banco em memória."""
    repo_usuario = RepositorioUsuario(banco_memoria)
    repo_produto = RepositorioProduto(banco_memoria)
    repo_pedido = RepositorioPedido(banco_memoria)
    return ContinerServicos(
        banco=banco_memoria,
        autenticacao=ServicoAutenticacao(repo_usuario),
        catalogo=ServicoCatalogo(repo_produto, repo_usuario),
        carrinho=ServicoCarrinho(repo_produto),
        pedido=ServicoPedido(
            banco=banco_memoria,
            repositorio_usuario=repo_usuario,
            repositorio_produto=repo_produto,
            repositorio_pedido=repo_pedido,
            simulador_pagamento=SimuladorPagamento(),
        ),
    )


@pytest.fixture()
def anunciante_padrao(servicos: ContinerServicos) -> Usuario:
    """Cadastra e retorna um usuário com perfil de anunciante."""
    return servicos.autenticacao.cadastrar_usuario(
        nome="Carlos Vendedor",
        email="carlos@loja.com",
        senha="senha_segura_123",
        perfil="anunciante",
    )


@pytest.fixture()
def cliente_padrao(servicos: ContinerServicos) -> Usuario:
    """Cadastra e retorna um usuário com perfil de cliente."""
    return servicos.autenticacao.cadastrar_usuario(
        nome="Ana Compradora",
        email="ana@cliente.com",
        senha="senha_segura_123",
        perfil="cliente",
    )


@pytest.fixture()
def produto_padrao(servicos: ContinerServicos, anunciante_padrao: Usuario) -> Produto:
    """Publica e retorna um produto ativo padrão."""
    assert anunciante_padrao.id is not None
    return servicos.catalogo.anunciar_produto(
        anunciante_id=anunciante_padrao.id,
        titulo="Fone Bluetooth Sem Fio",
        descricao="Fone confortável com cancelamento de ruído.",
        preco="150.00",
        estoque=5,
        categoria="Eletrônicos",
    )


@pytest.fixture()
def app_teste(tmp_path: Path) -> Flask:
    """Cria uma aplicação Flask configurada com banco e pasta temporários."""
    return criar_app(
        {
            "TESTING": True,
            "SECRET_KEY": "chave-secreta-de-teste",
            "CAMINHO_BANCO": str(tmp_path / "mercado_teste.db"),
            "PASTA_UPLOADS": str(tmp_path / "uploads"),
        }
    )


@pytest.fixture()
def cliente_web(app_teste: Flask) -> FlaskClient:
    """Retorna um cliente HTTP de testes do Flask."""
    return app_teste.test_client()