"""Testes de unidade para as funções públicas de validação e formatação."""

import pytest

from src.excecoes import ErroValidacao
from src.validadores import (
    validar_email,
    validar_nome,
    validar_perfil,
    validar_senha,
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