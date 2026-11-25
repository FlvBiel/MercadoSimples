"""Funções puras de validação e formatação de dados do domínio."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re

from src.excecoes import ErroValidacao

CATEGORIAS_PERMITIDAS = (
    "Eletrônicos",
    "Livros",
    "Roupas",
    "Casa",
    "Esportes",
    "Outros",
)

PERFIS_PERMITIDOS = ("cliente", "anunciante")

EXTENSOES_IMAGEM_PERMITIDAS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}

_PADRAO_EMAIL = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validar_nome(nome: str) -> str:
    """Valida e normaliza o nome de exibição do usuário."""
    if not isinstance(nome, str):
        raise ErroValidacao("O nome deve ser um texto válido.")
    limpo = nome.strip()
    if len(limpo) < 2:
        raise ErroValidacao("O nome deve ter pelo menos 2 caracteres.")
    if len(limpo) > 100:
        raise ErroValidacao("O nome deve ter no máximo 100 caracteres.")
    return limpo


def validar_email(email: str) -> str:
    """Valida e normaliza o endereço de e-mail."""
    if not isinstance(email, str):
        raise ErroValidacao("O e-mail deve ser um texto válido.")
    limpo = email.strip().lower()
    if not limpo or len(limpo) > 150 or not _PADRAO_EMAIL.match(limpo):
        raise ErroValidacao("Informe um endereço de e-mail válido.")
    return limpo


def validar_senha(senha: str) -> str:
    """Valida os requisitos mínimos da senha."""
    if not isinstance(senha, str) or len(senha) < 6:
        raise ErroValidacao("A senha deve ter pelo menos 6 caracteres.")
    if len(senha) > 128:
        raise ErroValidacao("A senha deve ter no máximo 128 caracteres.")
    return senha


def validar_perfil(perfil: str) -> str:
    """Valida o tipo de conta do usuário (cliente ou anunciante)."""
    if not isinstance(perfil, str):
        raise ErroValidacao("Perfil de usuário inválido.")
    limpo = perfil.strip().lower()
    if limpo not in PERFIS_PERMITIDOS:
        raise ErroValidacao("O perfil deve ser 'cliente' ou 'anunciante'.")
    return limpo

def validar_titulo_produto(titulo: str) -> str:
    """Valida o título de um anúncio de produto."""
    if not isinstance(titulo, str):
        raise ErroValidacao("O título do produto deve ser um texto válido.")
    limpo = titulo.strip()
    if len(limpo) < 3:
        raise ErroValidacao("O título do produto deve ter pelo menos 3 caracteres.")
    if len(limpo) > 120:
        raise ErroValidacao("O título do produto deve ter no máximo 120 caracteres.")
    return limpo


def validar_descricao_produto(descricao: str) -> str:
    """Valida a descrição de um produto anunciado."""
    if descricao is None:
        return ""
    if not isinstance(descricao, str):
        raise ErroValidacao("A descrição deve ser um texto válido.")
    limpo = descricao.strip()
    if len(limpo) > 1000:
        raise ErroValidacao("A descrição deve ter no máximo 1000 caracteres.")
    return limpo


def validar_preco(valor: Decimal | float | int | str) -> Decimal:
    """Converte e valida o preço unitário de um produto."""
    if valor is None or isinstance(valor, bool):
        raise ErroValidacao("Informe um preço válido.")
    texto = str(valor).strip().replace(",", ".")
    if not texto:
        raise ErroValidacao("Informe um preço válido.")
    try:
        decimal = Decimal(texto).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise ErroValidacao("O preço informado não é um número válido.") from exc

    if decimal <= Decimal("0.00"):
        raise ErroValidacao("O preço deve ser maior que zero.")
    if decimal > Decimal("1000000.00"):
        raise ErroValidacao("O preço excede o limite máximo permitido.")
    return decimal


def validar_estoque(quantidade: int | str) -> int:
    """Valida a quantidade em estoque de um produto."""
    if isinstance(quantidade, bool) or quantidade is None:
        raise ErroValidacao("Informe uma quantidade de estoque válida.")
    try:
        inteiro = int(str(quantidade).strip())
    except ValueError as exc:
        raise ErroValidacao("O estoque deve ser um número inteiro.") from exc

    if inteiro < 0:
        raise ErroValidacao("O estoque não pode ser negativo.")
    if inteiro > 100000:
        raise ErroValidacao("O estoque excede o limite máximo permitido.")
    return inteiro


def validar_quantidade_compra(quantidade: int | str) -> int:
    """Valida a quantidade solicitada para compra no carrinho."""
    if isinstance(quantidade, bool) or quantidade is None:
        raise ErroValidacao("Informe uma quantidade válida.")
    try:
        inteiro = int(str(quantidade).strip())
    except ValueError as exc:
        raise ErroValidacao("A quantidade deve ser um número inteiro.") from exc

    if inteiro < 1:
        raise ErroValidacao("A quantidade deve ser de pelo menos 1 unidade.")
    if inteiro > 1000:
        raise ErroValidacao("A quantidade por item não pode ultrapassar 1000 unidades.")
    return inteiro


def validar_categoria(categoria: str | None) -> str:
    """Valida a categoria de um produto anunciado."""
    if not categoria or not isinstance(categoria, str) or not categoria.strip():
        return "Outros"
    limpa = categoria.strip()
    if limpa not in CATEGORIAS_PERMITIDAS:
        raise ErroValidacao(f"Categoria inválida: {limpa}.")
    return limpa


def validar_url_imagem(url: str | None) -> str:
    """Valida URL ou caminho relativo de imagem de um produto."""
    if not url:
        return ""
    if not isinstance(url, str):
        raise ErroValidacao("Caminho de imagem inválido.")
    limpa = url.strip()
    if not limpa:
        return ""
    if len(limpa) > 500:
        raise ErroValidacao("A URL da imagem é longa demais.")
    prefixos_validos = ("http://", "https://", "/static/", "/uploads/")
    if not limpa.startswith(prefixos_validos):
        raise ErroValidacao(
            "A URL da imagem deve iniciar com http://, https://, /static/ ou /uploads/."
        )
    return limpa


def arquivo_imagem_permitido(nome_arquivo: str) -> bool:
    """Verifica se o nome de arquivo possui extensão de imagem suportada."""
    if not nome_arquivo or "." not in nome_arquivo:
        return False
    extensao = nome_arquivo.rsplit(".", 1)[1].lower()
    return extensao in EXTENSOES_IMAGEM_PERMITIDAS


def decimal_para_centavos(valor: Decimal) -> int:
    """Converte um valor Decimal em reais para inteiro em centavos."""
    quantizado = valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(quantizado * 100)


def centavos_para_decimal(centavos: int) -> Decimal:
    """Converte um valor inteiro em centavos para Decimal em reais."""
    return (Decimal(int(centavos)) / Decimal(100)).quantize(Decimal("0.01"))


def formatar_moeda(valor: Decimal | float | int) -> str:
    """Formata um valor numérico no padrão monetário brasileiro (R$ 1.234,56)."""
    decimal = Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    texto_en = f"{decimal:,.2f}"
    texto_br = texto_en.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {texto_br}"