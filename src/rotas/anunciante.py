"""Rotas exclusivas de anunciantes para gestão de produtos e consulta de saldo."""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from src.excecoes import ErroMercado, ErroNaoEncontrado
from src.rotas.auxiliares import (
    exigir_perfil,
    obter_servicos,
    obter_usuario_logado,
    salvar_imagem_enviada,
)
from src.validadores import CATEGORIAS_PERMITIDAS

bp_anunciante = Blueprint("anunciante", __name__)


@bp_anunciante.get("/painel")
@exigir_perfil("anunciante")
def painel():
    """Exibe o painel do anunciante com resumo de saldo e itens anunciados."""
    usuario = obter_usuario_logado()
    assert usuario is not None and usuario.id is not None
    servicos = obter_servicos()

    anuncios = servicos.catalogo.listar_meus_anuncios(usuario.id)
    resumo = servicos.pedido.obter_resumo_financeiro_anunciante(usuario.id)
    return render_template(
        "painel_anunciante.html",
        anuncios=anuncios,
        resumo=resumo,
    )


@bp_anunciante.route("/anunciar", methods=["GET", "POST"])
@exigir_perfil("anunciante")
def anunciar():
    """Exibe e processa o formulário de criação de novo anúncio."""
    usuario = obter_usuario_logado()
    assert usuario is not None and usuario.id is not None
    servicos = obter_servicos()

    formulario = {
        "titulo": "",
        "descricao": "",
        "preco": "",
        "estoque": "1",
        "categoria": "Outros",
        "imagem_url": "",
    }

    if request.method == "POST":
        formulario = {
            "titulo": request.form.get("titulo", ""),
            "descricao": request.form.get("descricao", ""),
            "preco": request.form.get("preco", ""),
            "estoque": request.form.get("estoque", ""),
            "categoria": request.form.get("categoria", "Outros"),
            "imagem_url": request.form.get("imagem_url", ""),
        }
        try:
            caminho_upload = salvar_imagem_enviada(request.files.get("arquivo_imagem"))
            imagem_final = caminho_upload if caminho_upload else formulario["imagem_url"]

            servicos.catalogo.anunciar_produto(
                anunciante_id=usuario.id,
                titulo=formulario["titulo"],
                descricao=formulario["descricao"],
                preco=formulario["preco"],
                estoque=formulario["estoque"],
                categoria=formulario["categoria"],
                imagem_url=imagem_final,
            )
            flash("Produto anunciado com sucesso!", "sucesso")
            return redirect(url_for("anunciante.painel"))
        except ErroMercado as erro:
            flash(str(erro), "erro")

    return render_template(
        "formulario_produto.html",
        modo="criar",
        formulario=formulario,
        categorias=CATEGORIAS_PERMITIDAS,
        produto=None,
    )


@bp_anunciante.route("/produto/<int:produto_id>/editar", methods=["GET", "POST"])
@exigir_perfil("anunciante")
def editar(produto_id: int):
    """Permite ao anunciante alterar dados, preço, estoque ou imagem do seu produto."""
    usuario = obter_usuario_logado()
    assert usuario is not None and usuario.id is not None
    servicos = obter_servicos()

    try:
        produto = servicos.catalogo.obter_produto_ativo(produto_id)
    except ErroNaoEncontrado:
        flash("Produto não encontrado.", "erro")
        return redirect(url_for("anunciante.painel"))

    if produto.anunciante_id != usuario.id:
        flash("Você só pode editar os seus próprios anúncios.", "erro")
        return redirect(url_for("anunciante.painel"))

    formulario = {
        "titulo": produto.titulo,
        "descricao": produto.descricao,
        "preco": f"{produto.preco:.2f}",
        "estoque": str(produto.estoque),
        "categoria": produto.categoria,
        "imagem_url": produto.imagem_url,
    }

    if request.method == "POST":
        formulario = {
            "titulo": request.form.get("titulo", ""),
            "descricao": request.form.get("descricao", ""),
            "preco": request.form.get("preco", ""),
            "estoque": request.form.get("estoque", ""),
            "categoria": request.form.get("categoria", "Outros"),
            "imagem_url": request.form.get("imagem_url", ""),
        }
        try:
            caminho_upload = salvar_imagem_enviada(request.files.get("arquivo_imagem"))
            imagem_final = caminho_upload if caminho_upload else formulario["imagem_url"]

            servicos.catalogo.editar_produto(
                anunciante_id=usuario.id,
                produto_id=produto_id,
                titulo=formulario["titulo"],
                descricao=formulario["descricao"],
                preco=formulario["preco"],
                estoque=formulario["estoque"],
                categoria=formulario["categoria"],
                imagem_url=imagem_final,
            )
            flash("Anúncio atualizado com sucesso!", "sucesso")
            return redirect(url_for("anunciante.painel"))
        except ErroMercado as erro:
            flash(str(erro), "erro")

    return render_template(
        "formulario_produto.html",
        modo="editar",
        formulario=formulario,
        categorias=CATEGORIAS_PERMITIDAS,
        produto=produto,
    )


@bp_anunciante.post("/produto/<int:produto_id>/preco")
@exigir_perfil("anunciante")
def alterar_preco(produto_id: int):
    """Altera rapidamente o preço de um produto diretamente pelo painel."""
    usuario = obter_usuario_logado()
    assert usuario is not None and usuario.id is not None
    novo_preco = request.form.get("preco", "")

    servicos = obter_servicos()
    try:
        servicos.catalogo.alterar_preco_produto(usuario.id, produto_id, novo_preco)
        flash("Preço atualizado com sucesso!", "sucesso")
    except ErroMercado as erro:
        flash(str(erro), "erro")
    return redirect(url_for("anunciante.painel"))


@bp_anunciante.post("/produto/<int:produto_id>/remover")
@exigir_perfil("anunciante")
def remover(produto_id: int):
    """Remove um item anunciado para que não apareça mais à venda."""
    usuario = obter_usuario_logado()
    assert usuario is not None and usuario.id is not None

    servicos = obter_servicos()
    try:
        servicos.catalogo.remover_produto(usuario.id, produto_id)
        flash("Anúncio removido com sucesso.", "sucesso")
    except ErroMercado as erro:
        flash(str(erro), "erro")
    return redirect(url_for("anunciante.painel"))


@bp_anunciante.get("/saldo")
@exigir_perfil("anunciante")
def saldo():
    """Exibe o saldo a receber e o extrato detalhado de vendas do anunciante."""
    usuario = obter_usuario_logado()
    assert usuario is not None and usuario.id is not None

    servicos = obter_servicos()
    resumo = servicos.pedido.obter_resumo_financeiro_anunciante(usuario.id)
    return render_template("saldo_anunciante.html", resumo=resumo)