"""Fábrica da aplicação web Flask para a plataforma MercadoSimples."""

from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, session

from src.banco import BancoDados
from src.configuracao import obter_configuracao
from src.repositorios import (
    RepositorioPedido,
    RepositorioProduto,
    RepositorioUsuario,
)
from src.rotas import (
    bp_anunciante,
    bp_autenticacao,
    bp_catalogo,
    bp_cliente,
)
from src.rotas.auxiliares import ContinerServicos, obter_servicos, obter_usuario_logado
from src.servicos import (
    ServicoAutenticacao,
    ServicoCarrinho,
    ServicoCatalogo,
    ServicoPedido,
    SimuladorPagamento,
)
from src.validadores import formatar_moeda


def criar_app(config_teste: dict[str, Any] | None = None) -> Flask:
    """Cria, configura e inicializa uma instância da aplicação Flask."""
    app = Flask(__name__)
    config = obter_configuracao(config_teste)
    app.config.update(config)

    Path(app.config["PASTA_UPLOADS"]).mkdir(parents=True, exist_ok=True)

    banco = BancoDados(app.config["CAMINHO_BANCO"])
    banco.inicializar()

    repo_usuario = RepositorioUsuario(banco)
    repo_produto = RepositorioProduto(banco)
    repo_pedido = RepositorioPedido(banco)

    servicos = ContinerServicos(
        banco=banco,
        autenticacao=ServicoAutenticacao(repo_usuario),
        catalogo=ServicoCatalogo(repo_produto, repo_usuario),
        carrinho=ServicoCarrinho(repo_produto),
        pedido=ServicoPedido(
            banco=banco,
            repositorio_usuario=repo_usuario,
            repositorio_produto=repo_produto,
            repositorio_pedido=repo_pedido,
            simulador_pagamento=SimuladorPagamento(),
        ),
    )
    app.extensions["servicos"] = servicos

    app.jinja_env.filters["moeda"] = formatar_moeda

    @app.context_processor
    def injetar_contexto_global() -> dict[str, Any]:
        usuario = obter_usuario_logado()
        qtd_carrinho = 0
        if usuario is not None and usuario.eh_cliente():
            carrinho = obter_servicos().carrinho.reconstruir_carrinho(session.get("carrinho"))
            qtd_carrinho = carrinho.quantidade_total_itens()
        return {
            "usuario_atual": usuario,
            "quantidade_carrinho": qtd_carrinho,
        }

    @app.get("/saude")
    def verificar_saude():
        """Rota leve de verificação de disponibilidade para ambientes em produção."""
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def pagina_nao_encontrada(_erro: Exception):
        return render_template("erro_404.html", mensagem="Página não encontrada."), 404

    app.register_blueprint(bp_catalogo)
    app.register_blueprint(bp_autenticacao)
    app.register_blueprint(bp_anunciante)
    app.register_blueprint(bp_cliente)

    return app