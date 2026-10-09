"""Clasificacion de intenciones y el generador de decisiones (IL2.3).

`clasificar_intencion` traduce la consulta del usuario a una de las intenciones
conocidas por el agente. `GeneradorDecisionesLocal` es la politica deterministica
que el agente usa para elegir la siguiente herramienta en ausencia de un LLM
(equivalente al fallback de la EP1). Cuando se configura ANTHROPIC_API_KEY, el
mismo modulo sirve de respaldo si la llamada al LLM falla.
"""
from .config import INTENCIONES


def clasificar_intencion(consulta: str) -> str | None:
    """Encaja la consulta con la intencion de negocio mas probable."""
    c = consulta.lower()
    coincidencias: dict[str, int] = {}
    for intencion, claves in INTENCIONES.items():
        for clave in claves:
            if clave in c:
                coincidencias[intencion] = coincidencias.get(intencion, 0) + len(clave.split())
    if not coincidencias:
        return None
    return max(coincidencias, key=coincidencias.get)


class GeneradorDecisionesLocal:
    """Politica de decision por reglas (fallback determinista)."""

    def decidir(self, intencion: str | None, consulta: str) -> list[dict]:
        """Devuelve una lista de acciones (herramienta, argumentos) a ejecutar."""
        if intencion == "stock":
            return [{"herramienta": "consultar_stock", "argumentos": {"producto_id": "?"}}]
        if intencion == "precio":
            return [{"herramienta": "consultar_precio", "argumentos": {"producto_id": "?"}}]
        if intencion == "catalogo":
            return [{"herramienta": "buscar_catalogo", "argumentos": {"termino": "?"}}]
        if intencion == "estado_pedido":
            return [{"herramienta": "consultar_pedido", "argumentos": {"nro_pedido": "?"}}]
        if intencion == "cotizacion":
            return [{"herramienta": "crear_cotizacion", "argumentos": {"cliente_id": "?", "items": "?"}}]
        if intencion in ("pedido_nuevo",):
            return [{"herramienta": "planificar_pedido", "argumentos": {"cliente_id": "?", "items": "?"}}]
        if intencion == "reposicion":
            return [{"herramienta": "decidir_reposicion", "argumentos": {"producto_id": "?"}},
                    {"herramienta": "generar_orden_reposicion", "argumentos": {"producto_id": "?", "cantidad": "auto"}}]
        if intencion == "credito":
            return [{"herramienta": "evaluar_riesgo_credito", "argumentos": {"cliente_id": "?", "monto_total": 0}}]
        if intencion == "normativa":
            return [{"herramienta": "crear_ticket_escalamiento", "argumentos": {"cliente_id": "?", "motivo": "?"}}]
        return []