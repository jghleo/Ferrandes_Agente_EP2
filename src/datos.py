"""Carga de fuentes de datos de la empresa (catalogo, clientes, politicas, faqs)."""
import json
from pathlib import Path

from .config import DATOS_DIR


def _cargar(nombre: str) -> list | dict:
    ruta = Path(DATOS_DIR) / nombre
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def cargar_datos() -> dict:
    return {
        "productos": _cargar("catalogo_productos.json"),
        "clientes": _cargar("clientes.json"),
        "politicas": _cargar("politicas.json"),
        "faqs": _cargar("faqs.json"),
    }


def producto_por_id(productos: list, producto_id: str) -> dict | None:
    return next((p for p in productos if p["id"] == producto_id.upper()), None)


def cliente_por_id(clientes: list, cliente_id: str) -> dict | None:
    return next((c for c in clientes if c["id"] == cliente_id.upper()), None)