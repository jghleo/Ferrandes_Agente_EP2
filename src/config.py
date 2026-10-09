"""Configuracion central del proyecto Ferrandes EP2.

Concentra rutas, umbrales y reglas de negocio configurable del agente.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS_DIR = Path(__file__).resolve().parent / "datos"
EVIDENCIA_DIR = RAIZ / "evidencia"
LOG_PATH = EVIDENCIA_DIR / "logs_agente.jsonl"
DB_PATH = RAIZ / "datos_ferrandes.db"

# Reglas de negocio
IVA = 0.19
CUPO_MINIMO_APROBACION = 1_000_000          # monto desde el cual se exige aprobacion de vendedor
DESCUENTOS = [                              # listo de (monto_desde, porcentaje), mayor a menor
    (1_000_000, 0.08),
    (500_000, 0.05),
    (0, 0.0),
]
GRATIS_DESPACHO_DESDE = 100_000

# Intenciones reconocidas por el analizador de consultas
INTENCIONES = {
    "cotizacion": ["cotiz", "presupuesto", "cuanto cuesta comprar", "precio de lista"],
    "pedido_nuevo": ["pedir", "comprar", "ordenar", "quiero adquirir", "hacer un pedido"],
    "stock": ["stock", "inventario", "disponibilidad", "hay unidades", "tienen"],
    "precio": ["precio", "valor", "cuanto cuesta", "cuesta"],
    "catalogo": ["catalogo", "producto", "ficha", "que venden", "buscar"],
    "estado_pedido": ["estado de mi pedido", "donde va mi pedido", "seguimiento", "etapa"],
    "reposicion": ["reponer", "reposicion", "orden de compra proveedor", "falta stock"],
    "confirmar_pedido": ["confirmar", "confirma el pedido", "confirmo", "quedo confirmado"],
    "credito": ["credito", "cupo", "factura a 30 dias", "cuenta corriente"],
    "despacho": ["despacho", "envio", "entrega", "demora la entrega"],
    "normativa": ["norma", "reglamento", "obligatorio", "epp debo usar", "seguridad en altura",
                  "certificacion", "ley", "exige la ley"],
    "soporte": ["devolver", "devolucion", "garantia", "problema con mi compra", "reclamo", "ticket"],
}

STOPWORDS = {
    "el", "la", "los", "las", "de", "del", "en", "y", "a", "que", "que", "es", "un", "una",
    "para", "por", "con", "mi", "mis", "su", "sus", "me", "se", "puedo", "puede", "como",
    "donde", "cual", "mas", "si", "no", "le", "lo", "al", "o", "sobre", "hay", "quiero",
}


def aplicar_descuento(monto: float) -> tuple[float, int]:
    """Devuelve (monto_descuento, porcentaje_aplicado) segun tramos."""
    for monto_desde, porcentaje in DESCUENTOS:
        if monto >= monto_desde:
            return round(monto * porcentaje), int(porcentaje * 100)
    return 0.0, 0