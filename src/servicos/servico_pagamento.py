"""Simulador simples de gateway de pagamento sem uso de dinheiro real."""

from dataclasses import dataclass
from decimal import Decimal
import uuid

from src.validadores import validar_preco


@dataclass(frozen=True)
class ResultadoPagamento:
    """Representa a resposta do processamento de um pagamento."""

    aprovado: bool
    codigo_transacao: str
    valor: Decimal
    mensagem: str


class SimuladorPagamento:
    """Aprova pagamentos instantaneamente de forma simulada para fins acadêmicos."""

    def __init__(self, aprovar_sempre: bool = True) -> None:
        self.aprovar_sempre = aprovar_sempre

    def aprovar_pagamento(self, cliente_id: int, valor: Decimal) -> ResultadoPagamento:
        """Processa a cobrança única do pedido e retorna o resultado."""
        valor_validado = validar_preco(valor)
        if not self.aprovar_sempre:
            return ResultadoPagamento(
                aprovado=False,
                codigo_transacao="",
                valor=valor_validado,
                mensagem="Pagamento recusado pelo simulador financeiro.",
            )

        codigo = f"PAG-{cliente_id}-{uuid.uuid4().hex[:8].upper()}"
        return ResultadoPagamento(
            aprovado=True,
            codigo_transacao=codigo,
            valor=valor_validado,
            mensagem="Pagamento aprovado com sucesso.",
        )