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

def test_finalizar_compra_impede_conta_anunciante_de_comprar(
    servicos: ContinerServicos,
    anunciante_padrao: Usuario,
    produto_padrao: Produto,
) -> None:
    assert anunciante_padrao.id is not None
    carrinho = Carrinho()
    carrinho.adicionar(produto_padrao, 1)

    with pytest.raises(ErroPermissao):
        servicos.pedido.finalizar_compra(anunciante_padrao.id, carrinho)


def test_finalizar_compra_nao_altera_estoque_nem_saldo_se_pagamento_recusado(
    banco_memoria: BancoDados,
    servicos: ContinerServicos,
    anunciante_padrao: Usuario,
    cliente_padrao: Usuario,
    produto_padrao: Produto,
) -> None:
    assert (
        anunciante_padrao.id is not None
        and cliente_padrao.id is not None
        and produto_padrao.id is not None
    )
    servico_recusa = ServicoPedido(
        banco=banco_memoria,
        repositorio_usuario=RepositorioUsuario(banco_memoria),
        repositorio_produto=RepositorioProduto(banco_memoria),
        repositorio_pedido=RepositorioPedido(banco_memoria),
        simulador_pagamento=SimuladorPagamento(aprovar_sempre=False),
    )

    carrinho = Carrinho()
    carrinho.adicionar(produto_padrao, 2)

    with pytest.raises(ErroValidacao):
        servico_recusa.finalizar_compra(cliente_padrao.id, carrinho)

    assert servicos.catalogo.obter_produto_ativo(produto_padrao.id).estoque == 5
    assert servicos.autenticacao.obter_usuario(anunciante_padrao.id).saldo == Decimal("0.00")


def test_finalizar_compra_falha_quando_estoque_acabou_antes_do_pagamento(
    servicos: ContinerServicos,
    anunciante_padrao: Usuario,
    cliente_padrao: Usuario,
    produto_padrao: Produto,
) -> None:
    assert (
        anunciante_padrao.id is not None
        and cliente_padrao.id is not None
        and produto_padrao.id is not None
    )
    carrinho = Carrinho()
    carrinho.adicionar(produto_padrao, 2)

    servicos.catalogo.editar_produto(
        anunciante_id=anunciante_padrao.id,
        produto_id=produto_padrao.id,
        titulo=produto_padrao.titulo,
        descricao=produto_padrao.descricao,
        preco=produto_padrao.preco,
        estoque=1,
        categoria=produto_padrao.categoria,
    )

    with pytest.raises(ErroEstoqueInsuficiente):
        servicos.pedido.finalizar_compra(cliente_padrao.id, carrinho)


def test_resumo_financeiro_retorna_saldo_e_extrato_de_vendas_do_anunciante(
    servicos: ContinerServicos,
    anunciante_padrao: Usuario,
    cliente_padrao: Usuario,
    produto_padrao: Produto,
) -> None:
    assert anunciante_padrao.id is not None and cliente_padrao.id is not None
    carrinho = Carrinho()
    carrinho.adicionar(produto_padrao, 2)
    servicos.pedido.finalizar_compra(cliente_padrao.id, carrinho)

    resumo = servicos.pedido.obter_resumo_financeiro_anunciante(anunciante_padrao.id)

    assert resumo.saldo_disponivel == Decimal("300.00")
    assert resumo.total_vendas == 1
    assert resumo.itens_vendidos == 2
    assert resumo.vendas[0].nome_comprador == cliente_padrao.nome