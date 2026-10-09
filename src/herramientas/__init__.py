"""Herramientas del agente: consulta (lectura), escritura y razonamiento."""
from . import consulta, escritura, razonamiento

__all__ = ["consulta", "escritura", "razonamiento"]

# Registro unico de herramientas para el grafo LangChain y el ejecutor local.
# Formato: (nombre, descripcion, funcion, argumentos_esperados)
REPERTORIO = [
    # ---- consulta ----
    ("consultar_stock", "Consulta el stock actual y el stock minimo de un producto por su id.", consulta.consultar_stock, ["producto_id"]),
    ("consultar_precio", "Consulta el precio unitario de un producto por su id.", consulta.consultar_precio, ["producto_id"]),
    ("buscar_catalogo", "Busca productos del catalogo por palabras clave (termino de busqueda).", consulta.buscar_catalogo, ["termino"]),
    ("obtener_ficha_tecnica", "Entrega la ficha tecnica de un producto por su id.", consulta.obtener_ficha_tecnica, ["producto_id"]),
    ("consultar_pedido", "Consulta el estado y el historial de etapas de un pedido (nro tipo PAT-XXXXXX).", consulta.consultar_pedido, ["nro_pedido"]),
    ("consultar_cotizacion", "Consulta el detalle de una cotizacion (nro tipo COT-XXXXXX).", consulta.consultar_cotizacion, ["nro_cotizacion"]),
    # ---- escritura ----
    ("crear_cotizacion", "Genera una cotizacion formal para un cliente. items en formato 'PROD:cantidad,PROD2:cantidad'.", escritura.crear_cotizacion, ["cliente_id", "items"]),
    ("confirmar_pedido", "Convierte una cotizacion aprobada en pedido (nro tipo PAT-XXXXXX, etapa PENDIENTE_DESPACHO).", escritura.confirmar_pedido, ["nro_cotizacion"]),
    ("generar_orden_reposicion", "Emite una orden de compra a proveedor para reponer stock de un producto.", escritura.generar_orden_reposicion, ["producto_id", "cantidad"]),
    ("crear_ticket_escalamiento", "Crea un ticket para que un vendedor humano atienda una solicitud.", escritura.crear_ticket_escalamiento, ["cliente_id", "motivo"]),
    # ---- razonamiento ----
    ("evaluar_riesgo_credito", "Evalua si un cliente puede pagar con credito segun cupo y reglas de la empresa.", razonamiento.evaluar_riesgo_credito, ["cliente_id", "monto_total"]),
    ("decidir_reposicion", "Decide si conviene reponer un producto segun su stock actual vs stock minimo.", razonamiento.decidir_reposicion, ["producto_id"]),
    ("planificar_pedido", "Orquesta el flujo completo de pedido: valida stock, calcula descuentos, crea cotizacion, evalua credito y confirma o deriva.", razonamiento.planificar_pedido, ["cliente_id", "items"]),
]


def nombre_a_funcion(nombre: str):
    """Resuelve el nombre de una herramienta a su funcion."""
    for n, _, fn, _ in REPERTORIO:
        if n == nombre:
            return fn
    raise KeyError(f"Herramienta no registrada: {nombre}")