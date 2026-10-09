"""Herramientas de RAZONAMIENTO y planificacion (IL2.3, IL5).

Ejecutan logica de decision: evaluacion de credito, politica de reposicion de
stock y la orquestacion completa de un pedido. Son las funciones que permiten al
agente tomar decisiones adaptativas ante condiciones cambiantes (stock faltante,
cupo insuficiente, cliente nuevo).
"""
from ..config import CUPO_MINIMO_APROBACION

REGLA_NORMATIVA = (
    "La seleccion de EPP y el cumplimiento de normativas de seguridad "
    "(ej. trabajo en altura) deben ser validados por un especialista en "
    "seguridad (Prevencion de Riesgos), ya que dependen de la obra y su "
    "evaluacion de riesgo."
)


def evaluar_riesgo_credito(servicios, cliente_id: str, monto_total: float) -> str:
    cliente = servicios.cliente(cliente_id)
    if not cliente:
        return "Cliente no registrado: derivar a vendedor para apertura de ficha."
    monto_total = float(monto_total)

    if not cliente.get("credito"):
        if "nuevo-lead" in cliente.get("etiquetas", []) or "sin-historial" in cliente.get("etiquetas", []):
            return (
                f"DECISION: PAGO_CONTRA_ENTREGA. Cliente {cliente['nombre']} es nuevo "
                "y no tiene historial de credito. Se solicita pago contra entrega o "
                "contado hasta revision del vendedor."
            )
        return (
            f"DECISION: CONTADO. El cliente {cliente['nombre']} opera sin credito "
            "habilitado; la operacion se paga en efectivo/debito."
        )

    cupo_disponible = cliente.get("cupo_credito", 0) - cliente.get("saldo_usado", 0)
    if monto_total > cupo_disponible:
        return (
            f"DECISION: REQUIERE_APROBACION. El monto ${monto_total:,.0f} supera el cupo "
            f"disponible de {cliente['nombre']} (${cupo_disponible:,.0f}). Se genera ticket "
            "de escalamiento para aprobacion del vendedor."
        )
    if monto_total >= CUPO_MINIMO_APROBACION:
        return (
            f"DECISION: REQUIERE_APROBACION_POR_MONTO. El monto ${monto_total:,.0f} supera "
            f"el umbral de ${CUPO_MINIMO_APROBACION:,.0f}; el vendedor debe validar la operacion."
        )
    return (
        f"DECISION: CREDITO_OK. {cliente['nombre']} opera con credito; cupo disponible "
        f"${cupo_disponible:,.0f} cubre el total ${monto_total:,.0f}."
    )


def decidir_reposicion(servicios, producto_id: str) -> str:
    producto = servicios.producto(producto_id)
    if not producto:
        return f"No existe el producto {producto_id}."
    stock = producto["stock_actual"]
    minimo = producto["stock_minimo"]
    if stock <= 0:
        nivel = "CRITICO (agotado)"
    elif stock < minimo:
        nivel = "BAJO"
    else:
        nivel = "OK"
    if stock >= minimo:
        return (
            f"REPOSICION: NO REQUERIDA. {producto['id']} tiene {stock} unidades "
            f"(minimo {minimo})."
        )
    cantidad_sugerida = max(minimo - stock, 1)
    return (
        f"REPOSICION: REQUERIDA. {producto['id']} esta en estado {nivel} con {stock} "
        f"unidades (minimo {minimo}). Se sugiere emitir orden de compra por "
        f"{cantidad_sugerida} unidades a {producto['proveedor']}; reposicion en "
        f"{producto['tiempo_reposicion_dias']} dias."
    )


def planificar_pedido(servicios, cliente_id: str, items: str) -> str:
    """Herramienta macroutilizada por el agente LangChain (o LLM real) para
    orquestar un pedido completo en una sola llamada. El ejecutor local
    (Planificador) descompone el mismo flujo en pasos individuales para
    evidencia paso a paso; ambos comparten la logica de <procesar_pedido>."""
    from ..planificador import Planificador

    planificador = Planificador(servicios)
    return planificador.procesar_pedido(cliente_id, items)["resumen"]