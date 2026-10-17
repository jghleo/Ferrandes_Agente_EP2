"""Herramientas de ESCRITURA.

Corresponden al tipo "herramientas de escritura" exigido por IL2.1: producen
efectos persistentes en el estado de la organizacion (cotizaciones, pedidos,
ordenes de reposicion, tickets) y quedan registrados en la memoria de largo
plazo (trazabilidad).
"""
import json

from ..config import IVA, aplicar_descuento


def _parse_items_tolerante(servicios, items: str) -> tuple[list[dict], list[str]]:
    """Parsea items sin abortar: devuelve (validos, invalidos).

    Permite que el planificador aplique una REPLANIFICACION: descartar los
    items invalidos, informar al usuario y continuar con los validos, en lugar
    de abortar todo el flujo. `invalidos` describe los problemas detectados.
    """
    validos: list[dict] = []
    invalidos: list[str] = []
    for parte in str(items).replace(";", ",").split(","):
        parte = parte.strip()
        if not parte:
            continue
        if ":" not in parte:
            invalidos.append(f"{parte} (falta cantidad)")
            continue
        prod_id, cant = parte.split(":", 1)
        prod_id = prod_id.strip()
        producto = servicios.producto(prod_id)
        if not producto:
            invalidos.append(f"{prod_id} (producto desconocido)")
            continue
        try:
            cantidad = int(cant.strip())
        except ValueError:
            invalidos.append(f"{prod_id} (cantidad no numerica)")
            continue
        if cantidad <= 0:
            invalidos.append(f"{prod_id} (cantidad <= 0)")
            continue
        validos.append({
            "producto_id": producto["id"],
            "nombre": producto["nombre"],
            "cantidad": cantidad,
            "precio_unitario": producto["precio_unitario"],
        })
    return validos, invalidos


def _parse_items(servicios, items: str) -> list[dict]:
    """Parsea 'TOR-001:50, EPP-001:20' a lista de items validados.

    Version estricta: lanza ValueError si hay items invalidos o ninguno valido.
    """
    detalle, invalidos = _parse_items_tolerante(servicios, items)
    if invalidos:
        raise ValueError(f"Producto desconocido: {', '.join(invalidos)}")
    if not detalle:
        raise ValueError("Debes indicar items en formato 'PROD:cantidad, PROD2:cantidad'.")
    return detalle


def crear_cotizacion(servicios, cliente_id: str, items: str) -> str:
    cliente = servicios.cliente(cliente_id)
    if not cliente:
        return f"Cliente no registrado: {cliente_id}."
    detalle = _parse_items(servicios, items)

    subtotal = sum(i["cantidad"] * i["precio_unitario"] for i in detalle)
    descuento, porcentaje = aplicar_descuento(subtotal)
    neto = subtotal - descuento
    iva = round(neto * IVA, 0)
    total = round(neto + iva, 0)

    nro = servicios.ml.nueva_cotizacion()
    servicios.ml.guardar_cotizacion(
        nro, cliente_id, detalle, subtotal, descuento, porcentaje, iva, total
    )
    lineas = "\n".join(
        f"- {i['cantidad']} x {i['producto_id']} {i['nombre']} "
        f"= ${i['cantidad'] * i['precio_unitario']:,.0f}"
        for i in detalle
    )
    return (
        f"Cotizacion {nro} generada para {cliente['nombre']} ({cliente_id}):\n"
        f"{lineas}\n"
        f"Subtotal: ${subtotal:,.0f} | Descuento: {porcentaje}% (${descuento:,.0f}) | "
        f"IVA 19%: ${iva:,.0f} | TOTAL: ${total:,.0f}."
    )


def confirmar_pedido(servicios, nro_cotizacion: str) -> str:
    cot = servicios.ml.get_cotizacion(str(nro_cotizacion).upper())
    if not cot:
        return f"No existe la cotizacion {nro_cotizacion}."
    if cot["estado"] != "PENDIENTE_CONFIRMACION":
        return f"La cotizacion {nro_cotizacion} ya fue procesada (estado {cot['estado']})."

    nro_pedido = servicios.ml.nuevo_pedido()
    historial = [{"etapa": "PENDIENTE_DESPACHO", "ts": servicios.ml.ts()}]
    servicios.ml.guardar_pedido(
        nro_pedido, cot["nro"], cot["cliente_id"], cot["items"], "PENDIENTE_DESPACHO", historial
    )
    with servicios.ml._con() as con:
        con.execute(
            "UPDATE cotizaciones SET estado = 'CONFIRMADA' WHERE nro = ?", (cot["nro"],)
        )
    return (
        f"Pedido {nro_pedido} confirmado (cliente {cot['cliente_id']}, "
        f"total ${cot['total']:,.0f}). Etapa inicial: PENDIENTE_DESPACHO."
    )


def generar_orden_reposicion(servicios, producto_id: str, cantidad="auto") -> str:
    producto = servicios.producto(producto_id)
    if not producto:
        return f"No existe el producto {producto_id}."
    if str(cantidad).lower() == "auto":
        cantidad_final = max(producto["stock_minimo"] - producto["stock_actual"], 1)
    else:
        cantidad_final = int(cantidad)
    nro_oc = servicios.ml.registrar_oc(producto["id"], cantidad_final, producto["proveedor"])
    return (
        f"Orden de compra {nro_oc} emitida: {cantidad_final} unidades de "
        f"{producto['id']} {producto['nombre']} al proveedor {producto['proveedor']}. "
        f"Reposicion estimada en {producto['tiempo_reposicion_dias']} dias."
    )


def crear_ticket_escalamiento(servicios, cliente_id: str, motivo: str) -> str:
    cliente = servicios.cliente(cliente_id)
    nombre = cliente["nombre"] if cliente else cliente_id
    nro = servicios.ml.crear_ticket(cliente_id if cliente else "SIN-CLIENTE", motivo)
    return (
        f"Ticket {nro} creado para {nombre}: '{motivo}'. "
        f"Un vendedor especialista de Ferrandes lo revisara en menos de 24 hrs habiles."
    )