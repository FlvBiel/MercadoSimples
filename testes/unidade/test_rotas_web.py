"""Testes das rotas HTTP através do cliente público de testes do Flask."""

import io
from flask.testing import FlaskClient


def test_rota_saude_retorna_status_ok(cliente_web: FlaskClient) -> None:
    resposta = cliente_web.get("/saude")
    assert resposta.status_code == 200
    assert resposta.get_json() == {"status": "ok"}


def test_visitante_visualiza_catalogo_vazio_inicial(cliente_web: FlaskClient) -> None:
    resposta = cliente_web.get("/")
    assert resposta.status_code == 200
    assert "Nenhum produto encontrado" in resposta.get_data(as_text=True)


def test_produto_inexistente_retorna_pagina_404(cliente_web: FlaskClient) -> None:
    resposta = cliente_web.get("/produto/999")
    assert resposta.status_code == 404
    assert "404" in resposta.get_data(as_text=True)


def test_cadastro_e_upload_de_imagem_de_produto_pelo_anunciante(
    cliente_web: FlaskClient,
) -> None:
    cliente_web.post(
        "/cadastro",
        data={
            "nome": "Loja Central",
            "email": "central@loja.com",
            "senha": "senha123",
            "perfil": "anunciante",
        },
        follow_redirects=True,
    )

    svg_bytes = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'
    resposta = cliente_web.post(
        "/anunciar",
        data={
            "titulo": "Câmera Instantânea",
            "descricao": "Acompanha filme",
            "preco": "399,90",
            "estoque": "4",
            "categoria": "Eletrônicos",
            "arquivo_imagem": (io.BytesIO(svg_bytes), "camera.svg"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert "Produto anunciado com sucesso!" in html
    assert "Câmera Instantânea" in html


def test_upload_de_arquivo_com_extensao_invalida_exibe_erro(
    cliente_web: FlaskClient,
) -> None:
    cliente_web.post(
        "/cadastro",
        data={
            "nome": "Vendedor",
            "email": "vendedor@loja.com",
            "senha": "senha123",
            "perfil": "anunciante",
        },
    )

    resposta = cliente_web.post(
        "/anunciar",
        data={
            "titulo": "Produto Teste",
            "descricao": "",
            "preco": "20,00",
            "estoque": "2",
            "categoria": "Outros",
            "arquivo_imagem": (io.BytesIO(b"binario"), "malicioso.exe"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert "Formato de imagem não suportado" in resposta.get_data(as_text=True)