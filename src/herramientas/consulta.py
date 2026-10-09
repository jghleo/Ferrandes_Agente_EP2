"""Herramientas de CONSULTA (lectura/query).

Corresponden al tipo "herramientas de consulta" exigido por IL2.1: leen el
estado de las fuentes de datos sin modificarlas. No generan efectos colaterales.
"""
import json

from ..config import IVA


def _formatear(producto: dict) -> str:
    return (
        f"{producto['id']} - {producto['nombre']} "
        f"(categoria: {producto['categoria']}, unidad: {producto['unidad']})"
    )


def consultar_stock(servicios, producto_id: str) -> str:
    producto = servicios.producto(producto_id)
    if not producto:
        return f"No existe el producto {producto_id} en el catalogo."
    estado = "OK"
    if producto["stock_actual"] < producto["stock_minimo"]:
        estado = "BAJO (se requiere reposicion)"
    return (
        f"Stock de {_formatear(producto)}: {producto['stock_actual']} unidades "
        f"(stock minimo recomendado: {producto['stock_minimo']}). Estado: {estado}."
    )


def consultar_precio(servicios, producto_id: str) -> str:
    producto = servicios.producto(producto_id)
    if not producto:
        return f"No existe el producto {producto_id} en el catalogo."
    neto = producto["precio_unitario"]
    total = round(neto * (1 + IVA), 0)
    return (
        f"Precio de {_formatear(producto)}: ${neto:,.0f} neto + IVA "
        f"= ${total:,.0f} total por {producto['unidad']}."
    )


def buscar_catalogo(servicios, termino: str) -> str:
    from ..buscar_contexto import tokenizar

    termino_norm = tokenizar(termino)
    if not termino_norm:
        return "Indica una palabra clave para buscar en el catalogo."
    resultados = []
    for p in servicios.productos:
        texto = f"{p['nombre']} {p['descripcion']} {p['categoria']} " + " ".join(p["tags"])
        if termino_norm & tokenizar(texto):
            resultados.append(_formatear(p))
    if not resultados:
        return f"No se encontraron productos para '{termino}'."
    return "Productos encontrados:\n" + "\n".join(f"- {r}" for r in resultados)


def obtener_ficha_tecnica(servicios, producto_id: str) -> str:
    producto = servicios.producto(producto_id)
    if not producto:
        return f"No existe el producto {producto_id} en el catalogo."
    return (
        f"Ficha tecnica de {_formatear(producto)}:\n"
        f"- Descripcion: {producto['descripcion']}\n"
        f"- Proveedor: {producto['proveedor']}\n"
        f"- Tiempo de reposicion estimado: {producto['tiempo_reposicion_dias']} dias\n"
        f"- Precio unitario (neto): ${producto['precio_unitario']:,.0f}"
    )


def consultar_pedido(servicios, nro_pedido: str) -> str:
    pedido = servicios.ml.get_pedido(str(nro_pedido).upper())
    if not pedido:
        return f"No existe el pedido {nro_pedido}. Verifica el numero (formato PAT-XXXXXX)."
    etapas = "; ".join(f"{e['etapa']} ({e['ts']})" for e in pedido["historial_etapas"])
    return (
        f"Pedido {pedido['nro']} del cliente {pedido['cliente_id']}: "
        f"etapa actual '{pedido['etapa']}'. Historial de etapas: {etapas}. "
        f"Items: {json.dumps(pedido['items'], ensure_ascii=False)}"
    )


def consultar_cotizacion(servicios, nro_cotizacion: str) -> str:
    cot = servicios.ml.get_cotizacion(str(nro_cotizacion).upper())
    if not cot:
        return f"No existe la cotizacion {nro_cotizacion} (formato COT-XXXXXX)."
    return (
        f"Cotizacion {cot['nro']} del cliente {cot['cliente_id']} (estado {cot['estado']}):\n"
        f"- Subtotal: ${cot['subtotal']:,.0f}\n"
        f"- Descuento aplicado: {cot['porcentaje_descuento']}% (${cot['descuento']:,.0f})\n"
        f"- IVA 19%: ${cot['iva']:,.0f}\n"
        f"- Total: ${cot['total']:,.0f}"
    )