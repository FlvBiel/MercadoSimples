"""Testes de unidade para as funções públicas de validação e formatação."""

from decimal import Decimal
import pytest

from src.excecoes import ErroValidacao
from src.validadores import (
    arquivo_imagem_permitido,
    formatar_moeda,
    validar_categoria,
    validar_email,
    validar_estoque,
    validar_nome,
    validar_perfil,
    validar_preco,
    validar_senha,
    validar_url_imagem,
)


def test_validar_nome_remove_espacos_extras_nas_extremidades() -> None:
    assert validar_nome("   João da Silva   ") == "João da Silva"


def test_validar_nome_rejeita_texto_muito_curto() -> None:
    with pytest.raises(ErroValidacao):
        validar_nome("A")


def test_validar_email_normaliza_para_minusculas() -> None:
    assert validar_email("  Maria.Clara@Exemplo.COM ") == "maria.clara@exemplo.com"


def test_validar_email_rejeita_formato_invalido() -> None:
    with pytest.raises(ErroValidacao):
        validar_email("email-sem-arroba.com")


def test_validar_senha_rejeita_menos_de_seis_caracteres() -> None:
    with pytest.raises(ErroValidacao):
        validar_senha("12345")


def test_validar_perfil_aceita_apenas_cliente_ou_anunciante() -> None:
    assert validar_perfil("CLIENTE") == "cliente"
    assert validar_perfil("anunciante") == "anunciante"
    with pytest.raises(ErroValidacao):
        validar_perfil("administrador")

def test_validar_preco_converte_virgula_decimal_com_precisao() -> None:
    assert validar_preco("149,90") == Decimal("149.90")
    assert validar_preco(25) == Decimal("25.00")


@pytest.mark.parametrize("valor_invalido", ["0", "-10.50", "abc", "", True])
def test_validar_preco_rejeita_valores_nao_positivos_ou_invalidos(valor_invalido: object) -> None:
    with pytest.raises(ErroValidacao):
        validar_preco(valor_invalido)  # type: ignore[arg-type]


def test_validar_estoque_aceita_zero_e_rejeita_negativo() -> None:
    assert validar_estoque("0") == 0
    assert validar_estoque(15) == 15
    with pytest.raises(ErroValidacao):
        validar_estoque(-1)


def test_validar_categoria_usa_outros_quando_vazia_e_rejeita_desconhecida() -> None:
    assert validar_categoria("") == "Outros"
    assert validar_categoria("Livros") == "Livros"
    with pytest.raises(ErroValidacao):
        validar_categoria("Automóveis")


def test_validar_url_imagem_aceita_rotas_permitidas_e_rejeita_esquema_inseguro() -> None:
    assert validar_url_imagem("https://exemplo.com/foto.png") == "https://exemplo.com/foto.png"
    assert validar_url_imagem("/uploads/prod_123.jpg") == "/uploads/prod_123.jpg"
    with pytest.raises(ErroValidacao):
        validar_url_imagem("javascript:alert(1)")


def test_formatar_moeda_e_extensao_de_imagem() -> None:
    assert formatar_moeda(Decimal("1234.50")) == "R$ 1.234,50"
    assert arquivo_imagem_permitido("camera.JPG") is True
    assert arquivo_imagem_permitido("script.exe") is False