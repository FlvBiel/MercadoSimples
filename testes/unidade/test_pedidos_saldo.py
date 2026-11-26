"""Testes de unidade para fechamento de pedido, pagamento simulado e saldo de anunciantes."""

from decimal import Decimal
import pytest

from src.banco import BancoDados
from src.excecoes import (
    ErroEstoqueInsuficiente,
    ErroPermissao,
    ErroValidacao,
)
from src.modelos import Carrinho, Produto, Usuario
from src.repositorios import (
    RepositorioPedido,
    RepositorioProduto,
    RepositorioUsuario,
)
from src.rotas.auxiliares import ContinerServicos
from src.servicos import ServicoPedido, SimuladorPagamento


def test_finalizar_compra_aprova_pagamento_cria_pedido_e_limpa_carrinho(
    servicos: ContinerServicos,
    cliente_padrao: Usuario,
    produto_padrao: Produto,
) -> None:
    assert cliente_padrao.id is not None
    carrinho = Carrinho()
    carrinho.adicionar(produto_padrao, 2)

    pedido = servicos.pedido.finalizar_compra(cliente_padrao.id, carrinho)

    assert pedido.id is not None
    assert pedido.status == "pago"
    assert pedido.total == Decimal("300.00")
    assert pedido.codigo_transacao.startswith(f"PAG-{cliente_padrao.id}-")
    assert carrinho.esta_vazio() is True


def test_finalizar_compra_reduz_estoque_dos_produtos_adquiridos(
    servicos: ContinerServicos,
    cliente_padrao: Usuario,
    produto_padrao: Produto,
) -> None:
    assert cliente_padrao.id is not None and produto_padrao.id is not None
    carrinho = Carrinho()
    carrinho.adicionar(produto_padrao, 3)

    servicos.pedido.finalizar_compra(cliente_padrao.id, carrinho)
    atualizado = servicos.catalogo.obter_produto_ativo(produto_padrao.id)

    assert atualizado.estoque == 2


def test_finalizar_compra_credita_saldo_correto_para_multiplos_anunciantes(
    servicos: ContinerServicos,
    anunciante_padrao: Usuario,
    cliente_padrao: Usuario,
    produto_padrao: Produto,
) -> None:
    segundo_anunciante = servicos.autenticacao.cadastrar_usuario(
        "Beatriz Artes", "bia@loja.com", "123456", "anunciante"
    )
    assert (
        anunciante_padrao.id is not None
        and segundo_anunciante.id is not None
        and cliente_padrao.id is not None
    )

    quadro = servicos.catalogo.anunciar_produto(
        segundo_anunciante.id, "Quadro Decorativo", "", "85.50", 4, "Casa"
    )

    carrinho = Carrinho()
    carrinho.adicionar(produto_padrao, 2)  # 2 * 150.00 = 300.00
    carrinho.adicionar(quadro, 1)  # 1 * 85.50 = 85.50

    servicos.pedido.finalizar_compra(cliente_padrao.id, carrinho)

    vendedor_1 = servicos.autenticacao.obter_usuario(anunciante_padrao.id)
    vendedor_2 = servicos.autenticacao.obter_usuario(segundo_anunciante.id)

    assert vendedor_1.saldo == Decimal("300.00")
    assert vendedor_2.saldo == Decimal("85.50")


def test_finalizar_compra_rejeita_carrinho_vazio(
    servicos: ContinerServicos,
    cliente_padrao: Usuario,
) -> None:
    assert cliente_padrao.id is not None
    with pytest.raises(ErroValidacao):
        servicos.pedido.finalizar_compra(cliente_padrao.id, Carrinho())