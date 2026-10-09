"""Servicios compartidos del agente: acceso a datos, memoria y numeradores.

En el diseno de orquestacion (ver README, diagrama de arquitectura) este objeto
actua como el "contenedor de dependencias" que el agente, el planificador y las
herramientas comparten, garantizando un unico estado consistente (registro de
trazabilidad en memoria de largo plazo).
"""
from .config import DB_PATH
from .datos import cargar_datos, producto_por_id, cliente_por_id
from .memoria.corto_plazo import MemoriaCortoPlazo
from .memoria.largo_plazo import MemoriaLargoPlazo


class Servicios:
    def __init__(self, datos=None, memoria_corto=None, memoria_largo=None, db_path=None):
        self.datos = datos if datos is not None else cargar_datos()
        self.mc = memoria_corto if memoria_corto is not None else MemoriaCortoPlazo()
        self.ml = memoria_largo if memoria_largo is not None else MemoriaLargoPlazo(db_path or DB_PATH)
        self.ml.inicializar()

    # -- acceso a datos -----------------------------------------------------
    @property
    def productos(self):
        return self.datos["productos"]

    @property
    def clientes(self):
        return self.datos["clientes"]

    def producto(self, producto_id: str):
        return producto_por_id(self.productos, producto_id)

    def cliente(self, cliente_id: str):
        return cliente_por_id(self.clientes, cliente_id)

    # -- utilidades de negocio ----------------------------------------------
    def precio_con_descuento(self, monto: float):
        """Devuelve (monto, descuento, porcentaje_aplicado, total_iva_incluido)."""
        from .config import IVA, aplicar_descuento
        descuento, porcentaje = aplicar_descuento(monto)
        neto = monto - descuento
        total = round(neto * (1 + IVA), 0)
        return monto, descuento, porcentaje, total