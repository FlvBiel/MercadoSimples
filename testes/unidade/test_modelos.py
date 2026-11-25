"""Testes de unidade para o comportamento das entidades de domínio."""

from decimal import Decimal
import pytest

from src.excecoes import ErroEstoqueInsuficiente, ErroValidacao
from src.modelos import (
    IMAGEM_PADRAO_PRODUTO,
    Carrinho,
    Produto,
    Usuario,
)


def test_usuario_identifica_corretamente_perfil_cliente_e_anunciante() -> None:
    cliente = Usuario(nome="Ana", email="ana@ex.com", senha_hash="h", perfil="cliente")
    anunciante = Usuario(nome="Beto", email="beto@ex.com", senha_hash="h", perfil="anunciante")

    assert cliente.eh_cliente() is True
    assert cliente.eh_anunciante() is False
    assert anunciante.eh_anunciante() is True
    assert anunciante.eh_cliente() is False


def test_usuario_anunciante_acumula_credito_de_saldo() -> None:
    anunciante = Usuario(nome="Beto", email="beto@ex.com", senha_hash="h", perfil="anunciante")
    anunciante.creditar_saldo(Decimal("49.90"))
    anunciante.creditar_saldo(Decimal("10.10"))

    assert anunciante.saldo == Decimal("60.00")


def test_usuario_cliente_nao_pode_receber_credito_de_saldo() -> None:
    cliente = Usuario(nome="Ana", email="ana@ex.com", senha_hash="h", perfil="cliente")
    with pytest.raises(ErroValidacao):
        cliente.creditar_saldo(Decimal("20.00"))


def test_produto_verifica_disponibilidade_conforme_estoque_e_status_ativo() -> None:
    produto = Produto(
        id=1,
        anunciante_id=10,
        titulo="Livro Python",
        descricao="",
        preco=Decimal("80.00"),
        estoque=3,
    )
    assert produto.esta_disponivel(3) is True
    assert produto.esta_disponivel(4) is False

    produto.desativar()
    assert produto.esta_disponivel(1) is False


def test_produto_reduz_estoque_e_bloqueia_excesso() -> None:
    produto = Produto(
        id=1,
        anunciante_id=10,
        titulo="Caderno",
        descricao="",
        preco=Decimal("25.00"),
        estoque=4,
    )
    produto.reduzir_estoque(3)
    assert produto.estoque == 1

    with pytest.raises(ErroEstoqueInsuficiente):
        produto.reduzir_estoque(2)


def test_produto_retorna_imagem_padrao_quando_sem_foto_propria() -> None:
    sem_foto = Produto(10, "Item A", "", Decimal("10.00"), 1, imagem_url="", id=1)
    com_foto = Produto(
        10, "Item B", "", Decimal("10.00"), 1, imagem_url="https://img.com/b.png", id=2
    )

    assert sem_foto.caminho_imagem_exibicao() == IMAGEM_PADRAO_PRODUTO
    assert com_foto.caminho_imagem_exibicao() == "https://img.com/b.png"

def test_carrinho_soma_quantidades_do_mesmo_produto_e_calcula_total() -> None:
    p1 = Produto(10, "Mouse", "", Decimal("50.00"), 5, id=1)
    p2 = Produto(10, "Teclado", "", Decimal("120.50"), 5, id=2)

    carrinho = Carrinho()
    carrinho.adicionar(p1, 2)
    carrinho.adicionar(p1, 1)
    carrinho.adicionar(p2, 1)

    assert carrinho.quantidade_total_itens() == 4
    assert carrinho.calcular_total() == Decimal("270.50")


def test_carrinho_impede_adicionar_quantidade_acima_do_estoque() -> None:
    produto = Produto(10, "Monitor", "", Decimal("700.00"), 2, id=1)
    carrinho = Carrinho()

    with pytest.raises(ErroEstoqueInsuficiente):
        carrinho.adicionar(produto, 3)


def test_carrinho_atualiza_remove_e_limpa_itens() -> None:
    p1 = Produto(10, "Cabo HDMI", "", Decimal("30.00"), 10, id=1)
    p2 = Produto(10, "Adaptador", "", Decimal("20.00"), 10, id=2)

    carrinho = Carrinho()
    carrinho.adicionar(p1, 1)
    carrinho.adicionar(p2, 2)
    carrinho.atualizar_quantidade(1, 4)
    assert carrinho.calcular_total() == Decimal("160.00")

    carrinho.remover(2)
    assert carrinho.para_dicionario() == {"1": 4}

    carrinho.limpar()
    assert carrinho.esta_vazio() is True