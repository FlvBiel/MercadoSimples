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


def test_cliente_bloqueado_ao_tentar_acessar_painel_do_anunciante(
    cliente_web: FlaskClient,
) -> None:
    cliente_web.post(
        "/cadastro",
        data={
            "nome": "Comprador",
            "email": "comprador@email.com",
            "senha": "senha123",
            "perfil": "cliente",
        },
    )

    resposta = cliente_web.get("/painel", follow_redirects=True)
    assert "Apenas contas de anunciante podem acessar esta área." in resposta.get_data(as_text=True)


def test_anunciante_bloqueado_ao_tentar_acessar_carrinho_de_compras(
    cliente_web: FlaskClient,
) -> None:
    cliente_web.post(
        "/cadastro",
        data={
            "nome": "Anunciante",
            "email": "anunciante@email.com",
            "senha": "senha123",
            "perfil": "anunciante",
        },
    )

    resposta = cliente_web.get("/carrinho", follow_redirects=True)
    assert "Apenas contas de cliente podem utilizar o carrinho" in resposta.get_data(as_text=True)


def test_fluxo_http_completo_de_carrinho_pagamento_e_consulta_de_saldo(
    cliente_web: FlaskClient,
) -> None:
    cliente_web.post(
        "/cadastro",
        data={
            "nome": "Helena Vendedora",
            "email": "helena@loja.com",
            "senha": "senha123",
            "perfil": "anunciante",
        },
    )
    cliente_web.post(
        "/anunciar",
        data={
            "titulo": "Garrafa Térmica",
            "descricao": "Inox 500ml",
            "preco": "75,00",
            "estoque": "10",
            "categoria": "Casa",
        },
    )
    cliente_web.get("/sair")

    cliente_web.post(
        "/cadastro",
        data={
            "nome": "Bruno Cliente",
            "email": "bruno@cliente.com",
            "senha": "senha123",
            "perfil": "cliente",
        },
    )
    cliente_web.post("/carrinho/adicionar/1", data={"quantidade": "2"})
    resposta_compra = cliente_web.post("/finalizar-compra", follow_redirects=True)
    html_pedidos = resposta_compra.get_data(as_text=True)
    assert "Pagamento aprovado!" in html_pedidos
    assert "R$ 150,00" in html_pedidos

    cliente_web.get("/sair")
    cliente_web.post(
        "/entrar",
        data={"email": "helena@loja.com", "senha": "senha123"},
    )
    resposta_saldo = cliente_web.get("/saldo")
    html_saldo = resposta_saldo.get_data(as_text=True)
    assert "R$ 150,00" in html_saldo
    assert "Bruno Cliente" in html_saldo


def test_anunciante_edita_altera_preco_e_remove_anuncio_pelas_rotas_web(
    cliente_web: FlaskClient,
) -> None:
    cliente_web.post(
        "/cadastro",
        data={
            "nome": "Loja Alfa",
            "email": "alfa@loja.com",
            "senha": "senha123",
            "perfil": "anunciante",
        },
    )
    cliente_web.post(
        "/anunciar",
        data={
            "titulo": "Teclado Compacto",
            "descricao": "ABNT2",
            "preco": "200,00",
            "estoque": "5",
            "categoria": "Eletrônicos",
        },
    )

    pagina_edicao = cliente_web.get("/produto/1/editar")
    assert pagina_edicao.status_code == 200

    resp_edicao = cliente_web.post(
        "/produto/1/editar",
        data={
            "titulo": "Teclado Mecânico ABNT2",
            "descricao": "Switch marrom",
            "preco": "230,00",
            "estoque": "7",
            "categoria": "Eletrônicos",
            "imagem_url": "https://exemplo.com/teclado.png",
        },
        follow_redirects=True,
    )
    assert "Anúncio atualizado com sucesso!" in resp_edicao.get_data(as_text=True)

    resp_preco = cliente_web.post(
        "/produto/1/preco",
        data={"preco": "215,50"},
        follow_redirects=True,
    )
    assert "Preço atualizado com sucesso!" in resp_preco.get_data(as_text=True)

    resp_remocao = cliente_web.post("/produto/1/remover", follow_redirects=True)
    assert "Anúncio removido com sucesso." in resp_remocao.get_data(as_text=True)


def test_cliente_visualiza_atualiza_remove_e_esvazia_carrinho_via_web(
    cliente_web: FlaskClient,
) -> None:
    cliente_web.post(
        "/cadastro",
        data={
            "nome": "Vendedor",
            "email": "vend@loja.com",
            "senha": "senha123",
            "perfil": "anunciante",
        },
    )
    cliente_web.post(
        "/anunciar",
        data={
            "titulo": "Livro Teste",
            "descricao": "",
            "preco": "40,00",
            "estoque": "6",
            "categoria": "Livros",
        },
    )
    cliente_web.post(
        "/anunciar",
        data={
            "titulo": "Caneta Tinteiro",
            "descricao": "",
            "preco": "60,00",
            "estoque": "6",
            "categoria": "Outros",
        },
    )
    cliente_web.get("/sair")

    cliente_web.post(
        "/cadastro",
        data={
            "nome": "Leitor",
            "email": "leitor@cliente.com",
            "senha": "senha123",
            "perfil": "cliente",
        },
    )
    cliente_web.post("/carrinho/adicionar/1", data={"quantidade": "1"})
    cliente_web.post("/carrinho/adicionar/2", data={"quantidade": "1"})

    resp_att = cliente_web.post(
        "/carrinho/atualizar/1",
        data={"quantidade": "3"},
        follow_redirects=True,
    )
    assert "R$ 180,00" in resp_att.get_data(as_text=True)

    resp_rem = cliente_web.post("/carrinho/remover/2", follow_redirects=True)
    assert "Item removido do carrinho." in resp_rem.get_data(as_text=True)

    resp_limpar = cliente_web.post("/carrinho/limpar", follow_redirects=True)
    assert "Seu carrinho está vazio" in resp_limpar.get_data(as_text=True)


def test_visitante_redirecionado_para_login_em_area_restrita_e_falha_de_login(
    cliente_web: FlaskClient,
) -> None:
    resp_restrita = cliente_web.get("/painel", follow_redirects=True)
    assert "Faça login para continuar." in resp_restrita.get_data(as_text=True)

    resp_login_invalido = cliente_web.post(
        "/entrar",
        data={"email": "naoexiste@email.com", "senha": "errada"},
        follow_redirects=True,
    )
    assert "E-mail ou senha incorretos." in resp_login_invalido.get_data(as_text=True)