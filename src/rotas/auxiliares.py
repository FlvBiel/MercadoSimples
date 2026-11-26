"""Funções utilitárias, decoradores de acesso e upload para as rotas web."""

from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional
import uuid

from flask import current_app, flash, g, redirect, session, url_for
from werkzeug.datastructures import FileStorage

from src.banco import BancoDados
from src.excecoes import ErroNaoEncontrado, ErroValidacao
from src.modelos import Usuario
from src.servicos import (
    ServicoAutenticacao,
    ServicoCarrinho,
    ServicoCatalogo,
    ServicoPedido,
)
from src.validadores import arquivo_imagem_permitido


@dataclass
class ContinerServicos:
    """Agrupa instâncias do banco e dos serviços de domínio da aplicação."""

    banco: BancoDados
    autenticacao: ServicoAutenticacao
    catalogo: ServicoCatalogo
    carrinho: ServicoCarrinho
    pedido: ServicoPedido


def obter_servicos() -> ContinerServicos:
    """Recupera o contêiner de serviços registrado na aplicação Flask."""
    return current_app.extensions["servicos"]


def obter_usuario_logado() -> Optional[Usuario]:
    """Carrega e armazena em cache de requisição o usuário autenticado na sessão."""
    if "usuario_atual" in g:
        return g.usuario_atual

    usuario_id = session.get("usuario_id")
    if not usuario_id:
        g.usuario_atual = None
        return None

    servicos = obter_servicos()
    try:
        usuario = servicos.autenticacao.obter_usuario(int(usuario_id))
    except (ErroNaoEncontrado, ValueError, TypeError):
        session.pop("usuario_id", None)
        g.usuario_atual = None
        return None

    g.usuario_atual = usuario
    return usuario


def exigir_autenticacao(funcao: Callable[..., Any]) -> Callable[..., Any]:
    """Garante que exista um usuário logado antes de executar a rota."""

    @wraps(funcao)
    def envoltorio(*args: Any, **kwargs: Any) -> Any:
        if obter_usuario_logado() is None:
            flash("Faça login para continuar.", "aviso")
            return redirect(url_for("autenticacao.entrar"))
        return funcao(*args, **kwargs)

    return envoltorio


def exigir_perfil(perfil_esperado: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Restringe o acesso da rota a um perfil específico ('cliente' ou 'anunciante')."""

    def decorador(funcao: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(funcao)
        def envoltorio(*args: Any, **kwargs: Any) -> Any:
            usuario = obter_usuario_logado()
            if usuario is None:
                flash("Faça login para continuar.", "aviso")
                return redirect(url_for("autenticacao.entrar"))
            if usuario.perfil != perfil_esperado:
                if perfil_esperado == "anunciante":
                    flash("Apenas contas de anunciante podem acessar esta área.", "erro")
                else:
                    flash(
                        "Apenas contas de cliente podem utilizar o carrinho e realizar compras.",
                        "erro",
                    )
                return redirect(url_for("catalogo.inicio"))
            return funcao(*args, **kwargs)

        return envoltorio

    return decorador


def salvar_imagem_enviada(arquivo: FileStorage | None) -> str:
    """Valida e grava em disco um arquivo de imagem enviado por formulário."""
    if arquivo is None or not arquivo.filename:
        return ""
    if not arquivo_imagem_permitido(arquivo.filename):
        raise ErroValidacao(
            "Formato de imagem não suportado. Utilize PNG, JPG, JPEG, GIF, WEBP ou SVG."
        )

    extensao = arquivo.filename.rsplit(".", 1)[1].lower()
    nome_seguro = f"prod_{uuid.uuid4().hex[:12]}.{extensao}"
    pasta_destino = Path(current_app.config["PASTA_UPLOADS"])
    pasta_destino.mkdir(parents=True, exist_ok=True)
    arquivo.save(pasta_destino / nome_seguro)
    return f"/uploads/{nome_seguro}"