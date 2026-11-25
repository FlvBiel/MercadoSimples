"""Testes de unidade para o comportamento das entidades de domínio."""

from decimal import Decimal
import pytest

from src.excecoes import ErroEstoqueInsuficiente, ErroValidacao
from src.modelos import (
    IMAGEM_PADRAO_PRODUTO,
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