"""Ponto de entrada WSGI e execução local da plataforma MercadoSimples."""

import os

from src import criar_app

app = criar_app()

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", "5000"))
    modo_debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=porta, debug=modo_debug)