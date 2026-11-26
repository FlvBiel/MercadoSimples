"""Testes de unidade para publicação, edição, remoção e pesquisa de produtos."""

from decimal import Decimal
import pytest

from src.excecoes import ErroNaoEncontrado, ErroPermissao
from src.modelos import Produto, Usuario
from src.rotas.auxiliares import ContinerServicos


def test_anunciante_consegue_publicar_novo_produto(
    servicos: ContinerServicos,
    anunciante_padrao: Usuario,
) -> None:
    assert anunciante_padrao.id is not None
    produto = servicos.catalogo.anunciar_produto(
        anunciante_id=anunciante_padrao.id,
        titulo="Mochila Impermeável",
        descricao="Mochila para notebook 15 polegadas",
        preco="189,90",
        estoque=8,
        categoria="Outros",
        imagem_url="https://exemplo.com/mochila.jpg",
    )

    assert produto.id is not None
    assert produto.preco == Decimal("189.90")
    assert produto.nome_anunciante == anunciante_padrao.nome


def test_cliente_nao_tem_permissao_para_anunciar_produto(
    servicos: ContinerServicos,
    cliente_padrao: Usuario,
) -> None:
    assert cliente_padrao.id is not None
    with pytest.raises(ErroPermissao):
        servicos.catalogo.anunciar_produto(
            anunciante_id=cliente_padrao.id,
            titulo="Item Proibido",
            descricao="",
            preco="50.00",
            estoque=1,
        )


def test_anunciante_consegue_alterar_preco_do_proprio_produto(
    servicos: ContinerServicos,
    anunciante_padrao: Usuario,
    produto_padrao: Produto,
) -> None:
    assert anunciante_padrao.id is not None and produto_padrao.id is not None
    atualizado = servicos.catalogo.alterar_preco_produto(
        anunciante_id=anunciante_padrao.id,
        produto_id=produto_padrao.id,
        novo_preco="129,50",
    )

    assert atualizado.preco == Decimal("129.50")


def test_anunciante_consegue_editar_dados_completos_do_produto(
    servicos: ContinerServicos,
    anunciante_padrao: Usuario,
    produto_padrao: Produto,
) -> None:
    assert anunciante_padrao.id is not None and produto_padrao.id is not None
    editado = servicos.catalogo.editar_produto(
        anunciante_id=anunciante_padrao.id,
        produto_id=produto_padrao.id,
        titulo="Fone Bluetooth Pro",
        descricao="Versão atualizada",
        preco="199.00",
        estoque=12,
        categoria="Eletrônicos",
        imagem_url="https://exemplo.com/fone.png",
    )

    assert editado.titulo == "Fone Bluetooth Pro"
    assert editado.estoque == 12
    assert editado.imagem_url == "https://exemplo.com/fone.png"


def test_anunciante_nao_pode_editar_produto_de_outro_anunciante(
    servicos: ContinerServicos,
    produto_padrao: Produto,
) -> None:
    outro_anunciante = servicos.autenticacao.cadastrar_usuario(
        "Outro Vendedor", "outro@loja.com", "123456", "anunciante"
    )
    assert outro_anunciante.id is not None and produto_padrao.id is not None

    with pytest.raises(ErroPermissao):
        servicos.catalogo.alterar_preco_produto(outro_anunciante.id, produto_padrao.id, "10.00")


def test_anunciante_remove_produto_e_ele_some_do_catalogo_publico(
    servicos: ContinerServicos,
    anunciante_padrao: Usuario,
    produto_padrao: Produto,
) -> None:
    assert anunciante_padrao.id is not None and produto_padrao.id is not None
    servicos.catalogo.remover_produto(anunciante_padrao.id, produto_padrao.id)

    assert servicos.catalogo.pesquisar_produtos() == []
    with pytest.raises(ErroNaoEncontrado):
        servicos.catalogo.obter_produto_ativo(produto_padrao.id)


def test_anunciante_nao_pode_remover_produto_de_terceiro(
    servicos: ContinerServicos,
    produto_padrao: Produto,
) -> None:
    intruso = servicos.autenticacao.cadastrar_usuario(
        "Intruso", "intruso@loja.com", "123456", "anunciante"
    )
    assert intruso.id is not None and produto_padrao.id is not None

    with pytest.raises(ErroPermissao):
        servicos.catalogo.remover_produto(intruso.id, produto_padrao.id)