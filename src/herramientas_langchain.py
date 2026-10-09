"""Integracion de las herramientas del agente con LangChain (IL2.1, IL2.2).

Cada herramienta del repertorio (consulta, escritura y razonamiento) se expone
como un `StructuredTool` de LangChain con su esquema de argumentos generado
dinamicamente. De esta forma el agente LangChain (create_agent) y el agente
local comparten exactamente las mismas funciones de negocio.
"""
from pydantic import create_model, Field

from .herramientas import REPERTORIO

TIPOS = {
    "producto_id": (str, "Codigo del producto, ej. TOR-001."),
    "items": (str, "Items en formato 'TOR-001:50, EPP-001:20'."),
    "cliente_id": (str, "Codigo del cliente, ej. CL-001."),
    "termino": (str, "Palabra clave de busqueda en el catalogo."),
    "nro_pedido": (str, "Numero de pedido en formato PAT-XXXXXX."),
    "nro_cotizacion": (str, "Numero de cotizacion en formato COT-XXXXXX."),
    "cantidad": (str, "Cantidad a reponer; 'auto' calcula segun stock minimo."),
    "motivo": (str, "Motivo de la solicitud o del ticket de escalamiento."),
    "monto_total": (float, "Monto total de la operacion en pesos chilenos."),
}


def _schema(nombre: str, params: list[str]):
    campos = {}
    for p in params:
        tipo, desc = TIPOS.get(p, (str, f"Parametro {p}."))
        campos[p] = (tipo, Field(description=desc))
    return create_model(f"{nombre}Args", **campos)


def construir_herramientas_langchain(servicios) -> list:
    """Construye los StructuredTool de LangChain cerrando sobre 'servicios'."""
    from langchain_core.tools import StructuredTool

    herramientas = []

    def fabricar(nombre: str, descripcion: str, fn, params: list[str]):
        def wrapper(**kwargs):
            try:
                return fn(servicios, **kwargs)
            except Exception as e:  # noqa: BLE001 - el tool debe responder texto
                return f"[Error de herramienta] {e}"

        wrapper.__name__ = nombre
        wrapper.__doc__ = descripcion
        return StructuredTool.from_function(
            func=wrapper,
            name=nombre,
            description=descripcion,
            args_schema=_schema(nombre, params),
        )

    for nombre, descripcion, fn, params in REPERTORIO:
        herramientas.append(fabricar(nombre, descripcion, fn, params))
    return herramientas