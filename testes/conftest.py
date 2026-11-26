"""Fixtures compartilhadas para os testes de unidade e integração."""

from typing import Iterator

import pytest

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