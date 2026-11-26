"""Rotas exclusivas de clientes para carrinho de compras, pagamento e pedidos."""

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from src.excecoes import ErroMercado
from src.rotas.auxiliares import exigir_perfil, obter_servicos, obter_usuario_logado

bp_cliente = Blueprint("cliente", __name__)


@bp_cliente.get("/carrinho")
@exigir_perfil("cliente")
def ver_carrinho():
    """Exibe todos os itens selecionados pelo cliente e o valor total."""
    servicos = obter_servicos()
    carrinho = servicos.carrinho.reconstruir_carrinho(session.get("carrinho"))
    session["carrinho"] = carrinho.para_dicionario()
    return render_template("carrinho.html", carrinho=carrinho)


@bp_cliente.post("/carrinho/adicionar/<int:produto_id>")
@exigir_perfil("cliente")
def adicionar_carrinho(produto_id: int):
    """Adiciona um produto ao carrinho do cliente."""
    quantidade = request.form.get("quantidade", "1")
    servicos = obter_servicos()
    try:
        session["carrinho"] = servicos.carrinho.adicionar_item(
            session.get("carrinho"),
            produto_id=produto_id,
            quantidade=quantidade,
        )
        flash("Produto adicionado ao carrinho!", "sucesso")
    except ErroMercado as erro:
        flash(str(erro), "erro")
        return redirect(url_for("catalogo.detalhe_produto", produto_id=produto_id))

    return redirect(url_for("cliente.ver_carrinho"))


@bp_cliente.post("/carrinho/atualizar/<int:produto_id>")
@exigir_perfil("cliente")
def atualizar_carrinho(produto_id: int):
    """Atualiza a quantidade desejada de um item no carrinho."""
    quantidade = request.form.get("quantidade", "1")
    servicos = obter_servicos()
    try:
        session["carrinho"] = servicos.carrinho.atualizar_item(
            session.get("carrinho"),
            produto_id=produto_id,
            quantidade=quantidade,
        )
        flash("Quantidade atualizada no carrinho.", "sucesso")
    except ErroMercado as erro:
        flash(str(erro), "erro")

    return redirect(url_for("cliente.ver_carrinho"))


@bp_cliente.post("/carrinho/remover/<int:produto_id>")
@exigir_perfil("cliente")
def remover_carrinho(produto_id: int):
    """Remove um item específico do carrinho de compras."""
    servicos = obter_servicos()
    session["carrinho"] = servicos.carrinho.remover_item(
        session.get("carrinho"),
        produto_id=produto_id,
    )
    flash("Item removido do carrinho.", "sucesso")
    return redirect(url_for("cliente.ver_carrinho"))


@bp_cliente.post("/carrinho/limpar")
@exigir_perfil("cliente")
def limpar_carrinho():
    """Remove todos os itens do carrinho de uma só vez."""
    servicos = obter_servicos()
    session["carrinho"] = servicos.carrinho.limpar_carrinho()
    flash("Carrinho esvaziado.", "sucesso")
    return redirect(url_for("cliente.ver_carrinho"))


@bp_cliente.post("/finalizar-compra")
@exigir_perfil("cliente")
def finalizar_compra():
    """Aprova o pagamento simulado de todo o carrinho em uma única operação."""
    usuario = obter_usuario_logado()
    assert usuario is not None and usuario.id is not None
    servicos = obter_servicos()

    carrinho = servicos.carrinho.reconstruir_carrinho(session.get("carrinho"))
    try:
        pedido = servicos.pedido.finalizar_compra(usuario.id, carrinho)
        session["carrinho"] = servicos.carrinho.limpar_carrinho()
        flash(
            f"Pagamento aprovado! Pedido #{pedido.id} confirmado ({pedido.codigo_transacao}).",
            "sucesso",
        )
        return redirect(url_for("cliente.meus_pedidos"))
    except ErroMercado as erro:
        flash(str(erro), "erro")
        return redirect(url_for("cliente.ver_carrinho"))


@bp_cliente.get("/pedidos")
@exigir_perfil("cliente")
def meus_pedidos():
    """Lista os pedidos já pagos pelo cliente."""
    usuario = obter_usuario_logado()
    assert usuario is not None and usuario.id is not None
    servicos = obter_servicos()

    pedidos = servicos.pedido.listar_pedidos_cliente(usuario.id)
    return render_template("pedidos.html", pedidos=pedidos)