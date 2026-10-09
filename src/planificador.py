"""Planificador de tareas del agente (IL2.3, IE5 / IL5).

Disena un esquema de planificacion con etapas priorizadas para convertir una
solicitud de pedido en un flujo de trabajo ejecutable. Durante la ejecucion:

1. Genera el plan base (lista ordenada de pasos con prioridad y precondiciones).
2. Ejecuta cada paso e inyecta pasos ADAPTATIVOS cuando las condiciones cambian
   (stock faltante -> decision de reposicion; credito insuficiente o cliente
   nuevo -> escalamiento con ticket).
3. Registra cada paso y cada decision en un "bitacora" que alimenta la memoria
   de largo plazo y la evidencia de trazabilidad.

Este orquestador es la implementacion de referencia del flujo; el agente
LangChain (src/agente_langchain.py) y el agente local (src/agente.py) lo
reutilizan para garantizar un comportamiento consistente.
"""
from dataclasses import dataclass, field

from .herramientas import escritura, razonamiento


@dataclass
class PasoPlan:
    """Un paso del plan con prioridad, herramienta opcional y precondicion."""
    etapa: str
    descripcion: str
    prioridad: int
    herramienta: str | None = None
    precondicion: str | None = None  # nombre de clave en el estado que debe existir


@dataclass
class Decision:
    tipo: str          # ADAPTACION | APRUEBA | BLOQUEA | ESTRATEGIA
    detalle: str
    razon: str = ""


class Planificador:
    def __init__(self, servicios):
        self.servicios = servicios

    # ------------------------------------------------------- diseno del plan
    def crear_plan_pedido(self, cliente_id: str, items: str) -> list[PasoPlan]:
        """Esquema base de planificacion (documentable en el informe, IL5)."""
        return [
            PasoPlan(
                etapa="1. ANALIZAR_SOLICITUD",
                descripcion="Valida que el cliente exista y parsea los items solicitados.",
                prioridad=1,
            ),
            PasoPlan(
                etapa="2. VALIDAR_STOCK",
                descripcion="Para cada item, consulta stock actual y stock minimo.",
                prioridad=2,
            ),
            PasoPlan(
                etapa="3. DECIDIR_REPOSICION",
                descripcion="Si hay items bajo minimo, decide emitir orden de compra (se inyecta de forma adaptativa).",
                prioridad=3,
                precondicion="hay_faltantes",
            ),
            PasoPlan(
                etapa="4. CREAR_COTIZACION",
                descripcion="Calcula subtotal, descuento por volumen, IVA y genera la cotizacion.",
                prioridad=4,
                precondicion="items_validos",
                herramienta="crear_cotizacion",
            ),
            PasoPlan(
                etapa="5. EVALUAR_RIESGO_CREDITO",
                descripcion="Evalua cupo disponible y reglas de credito segun el total.",
                prioridad=5,
                precondicion="nro_cotizacion",
                herramienta="evaluar_riesgo_credito",
            ),
            PasoPlan(
                etapa="6. DECIDIR_FLUJO_FINAL",
                descripcion="Confirma el pedido o deriva a aprobacion/ticket segun la decision de credito.",
                prioridad=6,
                precondicion="decision_credito",
            ),
        ]

    # ------------------------------------------------------- ejecucion
    def procesar_pedido(self, cliente_id: str, items: str) -> dict:
        """Ejecuta el plan base con inyeccion adaptativa y devuelve bitacora."""
        s = self.servicios
        plan = self.crear_plan_pedido(cliente_id, items)
        estado: dict = {}
        pasos_ejecutados: list[dict] = []
        decisiones: list[dict] = []

        def registrar_paso(etapa, herramienta, resultado):
            pasos_ejecutados.append({"etapa": etapa, "herramienta": herramienta,
                                     "resultado": resultado})

        def registrar_decision(tipo, detalle, razon=""):
            decisiones.append({"tipo": tipo, "detalle": detalle, "razon": razon})

        # --- paso 1: analizar solicitud -------------------------------------
        cliente = s.cliente(cliente_id)
        if not cliente:
            registrar_paso("1. ANALIZAR_SOLICITUD", None,
                           f"Cliente {cliente_id} no registrado.")
            return self._resumen(cliente_id, items, "ERROR", pasos_ejecutados,
                                 decisiones, error="Cliente no registrado.")
        estado["cliente"] = cliente
        try:
            from .herramientas.escritura import _parse_items
            detalle_items = _parse_items(s, items)
        except ValueError as e:
            registrar_paso("1. ANALIZAR_SOLICITUD", None, str(e))
            return self._resumen(cliente_id, items, "ERROR", pasos_ejecutados,
                                 decisiones, error=str(e))
        estado["items"] = detalle_items
        estado["items_validos"] = True
        registrar_paso(
            "1. ANALIZAR_SOLICITUD", "analizar_solicitud",
            f"{len(detalle_items)} items validos para {cliente['nombre']}.",
        )

        # --- paso 2: validar stock (pasa por cada item) ----------------------
        faltantes = []
        for item in detalle_items:
            prod = s.producto(item["producto_id"])
            resultado = f"{item['producto_id']}: stock {prod['stock_actual']}/{prod['stock_minimo']}"
            if item["cantidad"] > prod["stock_actual"] or prod["stock_actual"] < prod["stock_minimo"]:
                faltantes.append(item["producto_id"])
            registrar_paso("2. VALIDAR_STOCK", "consultar_stock", resultado)
        estado["hay_faltantes"] = bool(faltantes)
        if faltantes:
            registrar_decision(
                "ADAPTACION", f"Items bajo stock: {', '.join(faltantes)}.",
                "El plan base se extiende con pasos de reposicion antes de cotizar.",
            )

        # --- paso 3: reposicion adaptativa (solo si hay faltantes) ------------
        for prod_id in faltantes:
            paso_repos = PasoPlan("3. DECIDIR_REPOSICION", f"Reponer {prod_id}.", 3,
                                  herramienta="decidir_reposicion")
            resultado_decidir = razonamiento.decidir_reposicion(s, prod_id)
            registrar_paso(paso_repos.etapa, paso_repos.herramienta, resultado_decidir)
            oc = escritura.generar_orden_reposicion(s, prod_id, "auto")
            registrar_paso(f"3b. EMITIR_ORDEN_COMPRA ({prod_id})",
                           "generar_orden_reposicion", oc)
            registrar_decision(
                "ESTRATEGIA",
                f"Orden de compra emitida para {prod_id}; entrega se programa cuando llegue reposicion.",
                "Decision adaptativa: imagen de no perder la venta y mantener SLA de despacho.",
            )

        # --- paso 4: crear cotizacion -----------------------------------------
        resultado_cot = escritura.crear_cotizacion(s, cliente_id, items)
        nro_cotizacion = self._extraer_nro(resultado_cot, "COT")
        estado["nro_cotizacion"] = nro_cotizacion
        registrar_paso("4. CREAR_COTIZACION", "crear_cotizacion", resultado_cot)
        if nro_cotizacion:
            cot = s.ml.get_cotizacion(nro_cotizacion)
            estado["total"] = cot["total"]

        # --- paso 5: evaluar riesgo de credito --------------------------------
        resultado_riesgo = razonamiento.evaluar_riesgo_credito(
            s, cliente_id, estado.get("total", 0)
        )
        estado["decision_credito"] = resultado_riesgo
        registrar_paso("5. EVALUAR_RIESGO_CREDITO", "evaluar_riesgo_credito", resultado_riesgo)
        registrar_decision(
            "EVALUACION_CREDITO",
            resultado_riesgo.split("DECISION: ")[-1],
            "Politica de credito y cupo aplicada de forma adaptativa segun el cliente.",
        )

        # --- paso 6: flujo final (adaptativo) ----------------------------------
        if "REQUIERE_APROBACION" in resultado_riesgo:
            motivo = f"Validacion requiere aprobacion de vendedor (cotizacion {nro_cotizacion})."
            ticket = s.ml.crear_ticket(cliente_id, motivo)
            registrar_paso("6. DECIDIR_FLUJO_FINAL", "crear_ticket_escalamiento",
                           f"Ticket {ticket} abierto; pedido queda EN_APROBACION.")
            registrar_decision("BLOQUEA", "Pedido en espera de aprobacion humana.",
                               "Regla de negocio: montos altos o cupo insuficiente requieren validacion.")
            estado["estado_final"] = "EN_APROBACION"
            estado["ticket"] = ticket
        else:
            resultado_pedido = escritura.confirmar_pedido(s, nro_cotizacion)
            nro_pedido = self._extraer_nro(resultado_pedido, "PAT")
            estado["estado_final"] = "PEDIDO_CONFIRMADO"
            estado["nro_pedido"] = nro_pedido
            registrar_paso("6. DECIDIR_FLUJO_FINAL", "confirmar_pedido", resultado_pedido)
            registrar_decision("APRUEBA", "Pedido confirmado y programado para despacho.",
                               "Cupo disponible y condiciones de la operacion cumplidas.")

        return self._resumen(cliente_id, items, estado.get("estado_final", "ERROR"),
                             pasos_ejecutados, decisiones, estado=estado,
                             cotizacion=nro_cotizacion,
                             pedido=estado.get("nro_pedido"),
                             ticket=estado.get("ticket"))

    # ------------------------------------------------------- utilidades
    @staticmethod
    def _extraer_nro(texto: str, prefijo: str) -> str | None:
        palabras = texto.split()
        for p in palabras:
            if p.startswith(prefijo) and "-" in p:
                return p.strip(".,")
        return None

    def _resumen(self, cliente_id, items, estado_final, pasos, decisiones,
                 estado=None, cotizacion=None, pedido=None, ticket=None, error=None):
        estado = estado or {}
        total = estado.get("total")
        lineas = [f"FLUJO DE PEDIDO (cliente {cliente_id}) -> {estado_final}"]
        if error:
            lineas.append(f"ERROR: {error}")
        for paso in pasos:
            lineas.append(f"  [{paso['etapa']}] ({paso['herramienta'] or 'analisis'}): {paso['resultado']}")
        for d in decisiones:
            lineas.append(f"  DECISION {d['tipo']}: {d['detalle']} -- {d['razon']}")
        if cotizacion:
            lineas.append(f"  Cotizacion: {cotizacion} | Total: ${total:,.0f}" if total else f"  Cotizacion: {cotizacion}")
        if pedido:
            lineas.append(f"  Pedido: {pedido}")
        if ticket:
            lineas.append(f"  Ticket de escalamiento: {ticket}")
        return {
            "cliente_id": cliente_id,
            "items_solicitados": items,
            "estado_final": estado_final,
            "pasos": pasos,
            "decisiones": decisiones,
            "cotizacion": cotizacion,
            "pedido": pedido,
            "ticket": ticket,
            "resumen": "\n".join(lineas),
        }