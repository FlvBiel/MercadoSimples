"""Rotas de cadastro de conta, login e encerramento de sessão."""

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from src.excecoes import ErroMercado
from src.rotas.auxiliares import obter_servicos, obter_usuario_logado

bp_autenticacao = Blueprint("autenticacao", __name__)


@bp_autenticacao.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    """Permite criar uma nova conta como cliente ou anunciante."""
    if obter_usuario_logado() is not None:
        return redirect(url_for("catalogo.inicio"))

    dados_formulario = {"nome": "", "email": "", "perfil": "cliente"}
    if request.method == "POST":
        nome = request.form.get("nome", "")
        email = request.form.get("email", "")
        senha = request.form.get("senha", "")
        perfil = request.form.get("perfil", "cliente")
        dados_formulario = {"nome": nome, "email": email, "perfil": perfil}

        servicos = obter_servicos()
        try:
            usuario = servicos.autenticacao.cadastrar_usuario(
                nome=nome,
                email=email,
                senha=senha,
                perfil=perfil,
            )
            session.clear()
            session["usuario_id"] = usuario.id
            flash(f"Bem-vindo(a), {usuario.nome}! Conta criada com sucesso.", "sucesso")
            if usuario.eh_anunciante():
                return redirect(url_for("anunciante.painel"))
            return redirect(url_for("catalogo.inicio"))
        except ErroMercado as erro:
            flash(str(erro), "erro")

    return render_template("cadastro.html", formulario=dados_formulario)


@bp_autenticacao.route("/entrar", methods=["GET", "POST"])
def entrar():
    """Autentica um usuário existente com e-mail e senha."""
    if obter_usuario_logado() is not None:
        return redirect(url_for("catalogo.inicio"))

    email_informado = ""
    if request.method == "POST":
        email_informado = request.form.get("email", "")
        senha = request.form.get("senha", "")

        servicos = obter_servicos()
        try:
            usuario = servicos.autenticacao.autenticar(email=email_informado, senha=senha)
            session.clear()
            session["usuario_id"] = usuario.id
            flash(f"Olá, {usuario.nome}!", "sucesso")
            if usuario.eh_anunciante():
                return redirect(url_for("anunciante.painel"))
            return redirect(url_for("catalogo.inicio"))
        except ErroMercado as erro:
            flash(str(erro), "erro")

    return render_template("entrar.html", email=email_informado)


@bp_autenticacao.route("/sair", methods=["GET", "POST"])
def sair():
    """Encerra a sessão atual do usuário."""
    session.clear()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("catalogo.inicio"))