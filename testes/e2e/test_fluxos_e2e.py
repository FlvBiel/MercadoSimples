"""Testes end-to-end (E2E) com navegador real utilizando Playwright."""

from src.rotas.auxiliares import ContinerServicos
from pathlib import Path
import threading
from typing import Iterator

import pytest
from playwright.sync_api import Browser, Page, expect, sync_playwright
from werkzeug.serving import make_server

from src import criar_app


@pytest.fixture(scope="module")
def navegador() -> Iterator[Browser]:
    """Inicializa uma instância headless do Chromium compartilhada no módulo."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture()
def servidor_vivo(tmp_path: Path) -> Iterator[tuple[str, ContinerServicos]]:
    """Inicia a aplicação Flask em uma porta livre real com banco SQLite isolado."""
    app = criar_app(
        {
            "TESTING": True,
            "SECRET_KEY": "chave-e2e-mercado-simples",
            "CAMINHO_BANCO": str(tmp_path / "e2e.db"),
            "PASTA_UPLOADS": str(tmp_path / "uploads"),
        }
    )
    servidor = make_server("127.0.0.1", 0, app, threaded=True)
    porta = servidor.server_port
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()

    servicos: ContinerServicos = app.extensions["servicos"]
    yield f"http://127.0.0.1:{porta}", servicos

    servidor.shutdown()
    thread.join(timeout=5)


@pytest.fixture()
def pagina(navegador: Browser) -> Iterator[Page]:
    """Cria um contexto de navegação limpo (cookies e sessão isolados) por teste."""
    contexto = navegador.new_context()
    page = contexto.new_page()
    yield page
    contexto.close()


def test_e2e_anunciante_cadastra_conta_e_publica_produto_com_imagem(
    pagina: Page,
    servidor_vivo: tuple[str, ContinerServicos],
    tmp_path: Path,
) -> None:
    url_base, _ = servidor_vivo
    caminho_imagem = tmp_path / "foto_produto.svg"
    caminho_imagem.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80">'
        '<rect width="80" height="80" fill="#0f766e"/></svg>',
        encoding="utf-8",
    )

    pagina.goto(f"{url_base}/cadastro")
    pagina.get_by_label("Nome completo").fill("Marina Artesanato")
    pagina.get_by_label("E-mail").fill("marina@loja.com")
    pagina.get_by_label("Senha").fill("senha123")
    pagina.get_by_label("Tipo de conta").select_option("anunciante")
    pagina.get_by_role("button", name="Concluir Cadastro").click()

    expect(pagina.get_by_role("heading", name="Meus Produtos Anunciados")).to_be_visible()

    pagina.get_by_role("link", name="+ Anunciar Produto").click()
    pagina.get_by_label("Título do produto").fill("Vaso de Cerâmica Artesanal")
    pagina.get_by_label("Categoria").select_option("Casa")
    pagina.get_by_label("Preço unitário (R$)").fill("125,90")
    pagina.get_by_label("Quantidade em estoque").fill("6")
    pagina.get_by_label("Descrição").fill("Peça feita à mão esmaltada.")
    pagina.get_by_label("Enviar foto do produto (opcional)").set_input_files(str(caminho_imagem))
    pagina.get_by_role("button", name="Publicar Anúncio").click()

    expect(pagina.get_by_text("Produto anunciado com sucesso!")).to_be_visible()
    expect(pagina.get_by_role("link", name="Vaso de Cerâmica Artesanal")).to_be_visible()

    pagina.get_by_role("link", name="Produtos", exact=True).click()
    cartao = pagina.get_by_test_id("cartao-produto")
    expect(cartao).to_have_count(1)
    expect(cartao).to_contain_text("Vaso de Cerâmica Artesanal")
    expect(cartao).to_contain_text("R$ 125,90")
    atributo_src = cartao.locator("img").get_attribute("src")
    assert atributo_src is not None and atributo_src.startswith("/uploads/prod_")


def test_e2e_anunciante_altera_preco_e_remove_item_anunciado(
    pagina: Page,
    servidor_vivo: tuple[str, ContinerServicos],
) -> None:
    url_base, servicos = servidor_vivo
    anunciante = servicos.autenticacao.cadastrar_usuario(
        "Roberto Tech", "roberto@tech.com", "senha123", "anunciante"
    )
    assert anunciante.id is not None
    servicos.catalogo.anunciar_produto(
        anunciante.id, "Cadeira Ergonômica", "Ajuste lombar", "750.00", 3, "Casa"
    )
    servicos.catalogo.anunciar_produto(
        anunciante.id, "Luminária Antiga", "Item temporário", "90.00", 1, "Casa"
    )

    pagina.goto(f"{url_base}/entrar")
    pagina.get_by_label("E-mail").fill("roberto@tech.com")
    pagina.get_by_label("Senha").fill("senha123")
    pagina.get_by_role("button", name="Entrar").click()

    campo_preco = pagina.get_by_label("Novo preço de Cadeira Ergonômica")
    campo_preco.fill("699,90")
    linha_cadeira = pagina.locator("tr", has_text="Cadeira Ergonômica")
    linha_cadeira.get_by_role("button", name="Salvar Preço").click()
    expect(pagina.get_by_text("Preço atualizado com sucesso!")).to_be_visible()

    linha_luminaria = pagina.locator("tr", has_text="Luminária Antiga")
    linha_luminaria.get_by_role("button", name="Remover").click()
    expect(pagina.get_by_text("Anúncio removido com sucesso.")).to_be_visible()

    pagina.goto(url_base)
    expect(pagina.get_by_text("Cadeira Ergonômica")).to_be_visible()
    expect(pagina.get_by_text("R$ 699,90")).to_be_visible()
    expect(pagina.get_by_text("Luminária Antiga")).to_have_count(0)