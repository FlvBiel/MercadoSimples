"""Rotas públicas do catálogo de produtos e entrega de imagens enviadas."""

from flask import Blueprint, current_app, render_template, request, send_from_directory

from src.excecoes import ErroNaoEncontrado
from src.rotas.auxiliares import obter_servicos
from src.validadores import CATEGORIAS_PERMITIDAS

bp_catalogo = Blueprint("catalogo", __name__)


@bp_catalogo.get("/")
def inicio():
    """Exibe a vitrine principal com busca por termo, filtro de categoria e ordenação."""
    busca = request.args.get("busca", "").strip()
    categoria = request.args.get("categoria", "").strip()
    ordenacao = request.args.get("ordenacao", "recentes").strip()

    servicos = obter_servicos()
    produtos = servicos.catalogo.pesquisar_produtos(
        busca=busca,
        categoria=categoria,
        ordenacao=ordenacao,
    )
    return render_template(
        "inicio.html",
        produtos=produtos,
        categorias=CATEGORIAS_PERMITIDAS,
        busca_atual=busca,
        categoria_atual=categoria,
        ordenacao_atual=ordenacao,
    )


@bp_catalogo.get("/produto/<int:produto_id>")
def detalhe_produto(produto_id: int):
    """Exibe a página de detalhes de um produto ativo."""
    servicos = obter_servicos()
    try:
        produto = servicos.catalogo.obter_produto_ativo(produto_id)
    except ErroNaoEncontrado:
        return render_template("erro_404.html", mensagem="Produto não encontrado."), 404

    return render_template("detalhe_produto.html", produto=produto)


@bp_catalogo.get("/uploads/<path:nome_arquivo>")
def servir_upload(nome_arquivo: str):
    """Entrega arquivos de imagem enviados pelos anunciantes."""
    return send_from_directory(current_app.config["PASTA_UPLOADS"], nome_arquivo)