"""Testes de unidade para o serviço de carrinho de compras."""

from decimal import Decimal
import pytest

from src.excecoes import ErroNaoEncontrado
from src.modelos import Produto, Usuario
from src.rotas.auxiliares import ContinerServicos


def test_servico_carrinho_adiciona_e_reconstroi_itens_com_precos_atuais(
    servicos: ContinerServicos,
    produto_padrao: Produto,
) -> None:
    assert produto_padrao.id is not None
    dados = servicos.carrinho.adicionar_item({}, produto_padrao.id, 2)
    carrinho = servicos.carrinho.reconstruir_carrinho(dados)

    assert carrinho.quantidade_total_itens() == 2
    assert carrinho.calcular_total() == Decimal("300.00")


def test_servico_carrinho_rejeita_produto_inexistente_ou_removido(
    servicos: ContinerServicos,
    anunciante_padrao: Usuario,
    produto_padrao: Produto,
) -> None:
    assert anunciante_padrao.id is not None and produto_padrao.id is not None
    servicos.catalogo.remover_produto(anunciante_padrao.id, produto_padrao.id)

    with pytest.raises(ErroNaoEncontrado):
        servicos.carrinho.adicionar_item({}, produto_padrao.id, 1)


def test_servico_carrinho_ajusta_quantidade_se_estoque_diminuiu(
    servicos: ContinerServicos,
    anunciante_padrao: Usuario,
    produto_padrao: Produto,
) -> None:
    assert anunciante_padrao.id is not None and produto_padrao.id is not None
    dados = servicos.carrinho.adicionar_item({}, produto_padrao.id, 4)

    servicos.catalogo.editar_produto(
        anunciante_id=anunciante_padrao.id,
        produto_id=produto_padrao.id,
        titulo=produto_padrao.titulo,
        descricao=produto_padrao.descricao,
        preco=produto_padrao.preco,
        estoque=2,
        categoria=produto_padrao.categoria,
    )

    carrinho = servicos.carrinho.reconstruir_carrinho(dados)
    assert carrinho.quantidade_total_itens() == 2


def test_servico_carrinho_atualiza_quantidade_de_item(
    servicos: ContinerServicos,
    produto_padrao: Produto,
) -> None:
    assert produto_padrao.id is not None
    dados = servicos.carrinho.adicionar_item({}, produto_padrao.id, 1)
    dados = servicos.carrinho.atualizar_item(dados, produto_padrao.id, 3)

    assert dados == {str(produto_padrao.id): 3}


def test_servico_carrinho_remove_item_individual(
    servicos: ContinerServicos,
    produto_padrao: Produto,
) -> None:
    assert produto_padrao.id is not None
    dados = servicos.carrinho.adicionar_item({}, produto_padrao.id, 2)
    dados = servicos.carrinho.remover_item(dados, produto_padrao.id)

    assert dados == {}


def test_servico_carrinho_ignora_entradas_invalidas_na_reconstrucao(
    servicos: ContinerServicos,
) -> None:
    carrinho = servicos.carrinho.reconstruir_carrinho({"invalido": 2, "999": 1, "1": 0})  # type: ignore[dict-item]
    assert carrinho.esta_vazio() is True