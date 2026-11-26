"""Testes de unidade do serviço de cadastro e autenticação."""

import pytest

from src.excecoes import ErroAutenticacao, ErroNaoEncontrado
from src.rotas.auxiliares import ContinerServicos


def test_cadastrar_usuario_armazena_hash_em_vez_da_senha_em_texto_puro(
    servicos: ContinerServicos,
) -> None:
    usuario = servicos.autenticacao.cadastrar_usuario(
        nome="Lucas Mendes",
        email="lucas@teste.com",
        senha="minha_senha_secreta",
        perfil="cliente",
    )

    assert usuario.id is not None
    assert usuario.senha_hash != "minha_senha_secreta"


def test_cadastrar_usuario_impede_emails_duplicados(servicos: ContinerServicos) -> None:
    servicos.autenticacao.cadastrar_usuario("Maria", "maria@teste.com", "123456", "cliente")

    with pytest.raises(ErroAutenticacao):
        servicos.autenticacao.cadastrar_usuario("Outra Maria", "MARIA@teste.com", "654321", "anunciante")


def test_autenticar_retorna_usuario_quando_credenciais_estao_corretas(
    servicos: ContinerServicos,
) -> None:
    criado = servicos.autenticacao.cadastrar_usuario(
        nome=" Paula ",
        email="paula@loja.com",
        senha="senha_correta",
        perfil="anunciante",
    )
    autenticado = servicos.autenticacao.autenticar("PAULA@loja.com", "senha_correta")

    assert autenticado.id == criado.id
    assert autenticado.nome == "Paula"
    assert autenticado.eh_anunciante() is True


def test_autenticar_rejeita_senha_incorreta(servicos: ContinerServicos) -> None:
    servicos.autenticacao.cadastrar_usuario("Pedro", "pedro@teste.com", "123456", "cliente")

    with pytest.raises(ErroAutenticacao):
        servicos.autenticacao.autenticar("pedro@teste.com", "senha_errada")


def test_autenticar_rejeita_email_nao_cadastrado(servicos: ContinerServicos) -> None:
    with pytest.raises(ErroAutenticacao):
        servicos.autenticacao.autenticar("inexistente@teste.com", "123456")


def test_obter_usuario_existente_por_id(servicos: ContinerServicos) -> None:
    criado = servicos.autenticacao.cadastrar_usuario("Rita", "rita@teste.com", "123456", "cliente")
    assert criado.id is not None

    encontrado = servicos.autenticacao.obter_usuario(criado.id)
    assert encontrado.email == "rita@teste.com"


def test_obter_usuario_inexistente_lanca_erro_nao_encontrado(servicos: ContinerServicos) -> None:
    with pytest.raises(ErroNaoEncontrado):
        servicos.autenticacao.obter_usuario(9999)