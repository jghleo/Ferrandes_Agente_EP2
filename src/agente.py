"""Agente orquestador local (referencia funcional, IL2.1-IL2.3).

Ejecuta el ciclo completo del agente: interpreta la intencion, recupera contexto
semantico (RAG), selecciona herramientas, las ejecuta (consulta/escritura/
razonamiento), decide de forma adaptativa via el Planificador y registra toda la
trazabilidad en memoria de corto y largo plazo. Este ejecutor no requiere LLM y
es el que genera la evidencia de pruebas del repositorio; cuando se configura
ANTHROPIC_API_KEY, el agente LangChain (agente_langchain.py) usa exactamente las
mismas herramientas sobre el LLM real.
"""
import json
import re
import uuid
from datetime import datetime

from .buscar_contexto import recuperar_contexto
from .config import LOG_PATH
from .decisiones import clasificar_intencion
from .herramientas.escritura import crear_ticket_escalamiento
from .planificador import Planificador
from .servicios import Servicios

PATRONES = {
    "producto": re.compile(r"\b(?:TOR|HER|EPP|ELE|FIJ|SOL)-\d{3}\b", re.IGNORECASE),
    "cliente": re.compile(r"\bCL-\d{3}\b", re.IGNORECASE),
    "pedido": re.compile(r"\bPAT-\d{6}\b", re.IGNORECASE),
    "cotizacion": re.compile(r"\bCOT-\d{6}\b", re.IGNORECASE),
    "items": re.compile(r"\b(?:TOR|HER|EPP|ELE|FIJ|SOL)-\d{3}\s*:\s*\d+\b", re.IGNORECASE),
}


def extraer_producto(texto) -> str | None:
    m = PATRONES["producto"].search(texto.upper())
    return m.group(0) if m else None


def extraer_cliente(texto) -> str | None:
    m = PATRONES["cliente"].search(texto.upper())
    return m.group(0) if m else None


def extraer_items(texto) -> str | None:
    m = PATRONES["items"].findall(texto.upper())
    if m:
        return ", ".join(m)
    return None


def extraer_nro(texto, patron) -> str | None:
    m = PATRONES[patron].search(texto.upper())
    return m.group(0) if m else None


RESPUESTA_NORMATIVA = (
    "Esta consulta requiere criterio de un especialista en Prevencion de "
    "Riesgos: la seleccion de EPP y el cumplimiento normativo dependen de la "
    "obra y su evaluacion de riesgo. He creado un ticket para que el "
    "especialista te contacte. Mientras tanto, todo nuestro EPP tiene "
    "certificacion y puedes revisar las fichas de los productos."
)


class AgenteFerrandes:
    def __init__(self, servicios: Servicios | None = None, sesion_id: str | None = None):
        self.servicios = servicios or Servicios()
        self.sesion_id = sesion_id or f"ses-{uuid.uuid4().hex[:8]}"
        self.planificador = Planificador(self.servicios)

    # ------------------------------------------------------------- respuesta
    def responder(self, consulta: str, cliente_id: str | None = None) -> str:
        self.servicios.mc.agregar("usuario", consulta)
        cliente_id = cliente_id or extraer_cliente(consulta)

        intencion = clasificar_intencion(consulta)
        herramientas_usadas: list[str] = []
        contexto = recuperar_contexto(self.servicios.datos, consulta, top_k=3)
        pasos: list[dict] = []

        respuesta = self._ejecutar(intencion, consulta, cliente_id,
                                   herramientas_usadas, contexto, pasos)

        self.servicios.mc.agregar("agente", respuesta)
        if cliente_id:
            self.servicios.ml.registrar_interaccion(
                cliente_id, self.sesion_id, intencion or "general", consulta
            )
        self._escribir_log(consulta, intencion, herramientas_usadas, contexto,
                           pasos, respuesta, cliente_id)
        return respuesta

    # ------------------------------------------------------------- acciones
    def _ejecutar(self, intencion, consulta, cliente_id, herramientas, contexto, pasos):
        s = self.servicios
        cliente_id = cliente_id or "CL-001"  # en el caso simulado el agente pide contexto; demo usa CL-001

        if intencion == "stock":
            producto = extraer_producto(consulta)
            if not producto:
                return "¿Que producto quieres consultar? Indica su codigo (ej. TOR-001)."
            from .herramientas.consulta import consultar_stock
            herramientas.append("consultar_stock"); pasos.append({"etapa": "CONSULTA_STOCK", "herramienta": "consultar_stock"})
            return consultar_stock(s, producto)

        if intencion == "precio":
            producto = extraer_producto(consulta)
            if not producto:
                return "¿De que producto quieres el precio? Indica su codigo."
            from .herramientas.consulta import consultar_precio
            herramientas.append("consultar_precio"); pasos.append({"etapa": "CONSULTA_PRECIO", "herramienta": "consultar_precio"})
            return consultar_precio(s, producto)

        if intencion == "catalogo":
            from .herramientas.consulta import buscar_catalogo
            termino = consulta.replace("catalogo", "").replace("buscar", " ").strip() or "ferreteria"
            herramientas.append("buscar_catalogo"); pasos.append({"etapa": "CONSULTA_CATALOGO", "herramienta": "buscar_catalogo"})
            return buscar_catalogo(s, termino)

        if intencion == "estado_pedido":
            nro = extraer_nro(consulta, "pedido")
            if not nro:
                return "Indica el numero de tu pedido (formato PAT-XXXXXX)."
            from .herramientas.consulta import consultar_pedido
            herramientas.append("consultar_pedido"); pasos.append({"etapa": "CONSULTA_PEDIDO", "herramienta": "consultar_pedido"})
            return consultar_pedido(s, nro)

        if intencion == "confirmar_pedido":
            nro_cot = extraer_nro(consulta, "cotizacion")
            if not nro_cot:
                return "Indica el numero de la cotizacion a confirmar (formato COT-XXXXXX)."
            from .herramientas.escritura import confirmar_pedido
            herramientas.append("confirmar_pedido")
            pasos.append({"etapa": "CONFIRMAR_PEDIDO", "herramienta": "confirmar_pedido"})
            return confirmar_pedido(s, nro_cot)

        if intencion in ("cotizacion", "pedido_nuevo"):
            items = extraer_items(consulta)
            if not items:
                return ("Para cotizar/pedir indica los items en formato 'TOR-001:50, "
                        "EPP-001:20' y el cliente (CL-XXX).")
            resultado = self.planificador.procesar_pedido(cliente_id, items)
            herramientas.extend(r["herramienta"] or "planificacion" for r in resultado["pasos"])
            pasos.extend(resultado["pasos"])
            return resultado["resumen"]

        if intencion == "reposicion":
            producto = extraer_producto(consulta)
            if not producto:
                return "Indica el producto a reponer (ej. TOR-002)."
            from .herramientas.razonamiento import decidir_reposicion
            from .herramientas.escritura import generar_orden_reposicion
            herramientas += ["decidir_reposicion", "generar_orden_reposicion"]
            pasos = [{"etapa": "REPOSICION", "herramienta": "decidir_reposicion"}]
            decision = decidir_reposicion(s, producto)
            if "REQUERIDA" not in decision:
                return decision
            return decision + "\n" + generar_orden_reposicion(s, producto, "auto")

        if intencion == "credito":
            from .herramientas.razonamiento import evaluar_riesgo_credito
            herramientas.append("evaluar_riesgo_credito")
            pasos.append({"etapa": "RIESGO_CREDITO", "herramienta": "evaluar_riesgo_credito"})
            return evaluar_riesgo_credito(s, cliente_id, 0)

        if intencion == "normativa":
            motivo = f"Consulta normativa: {consulta}"
            ticket = s.ml.crear_ticket(cliente_id or "SIN-CLIENTE", motivo)
            herramientas.append("crear_ticket_escalamiento")
            pasos.append({"etapa": "DERIVACION_NORMATIVA", "herramienta": "crear_ticket_escalamiento"})
            return RESPUESTA_NORMATIVA + f"\n[Ticket {ticket} creado]"

        if intencion == "soporte":
            motivo = f"Solicitud de soporte: {consulta}"
            ticket = s.ml.crear_ticket(cliente_id or "SIN-CLIENTE", motivo)
            herramientas.append("crear_ticket_escalamiento")
            pasos.append({"etapa": "SOPORTE", "herramienta": "crear_ticket_escalamiento"})
            return (f"Ticket {ticket} creado. Politica de devolucion de Ferrandes: "
                    f"{self.servicios.datos['politicas']['devoluciones']}")

        # Consulta general -> respuesta basada en contexto recuperado (RAG)
        if contexto:
            origen = [c["id"] for c in contexto]
            pasos.append({"etapa": "RAG_RECUPERAR_CONTEXTO", "herramienta": "recuperar_contexto",
                          "resultado": f"fuentes: {', '.join(origen)}"})
            texto = contexto[0]["texto"]
            return (
                f"Segun la informacion de Ferrandes ({contexto[0]['id']}): {texto}"
                + ("\n[Para mas detalle puedo consultar otras fichas o generar una cotizacion.]"
                   if len(contexto) > 0 else "")
            )

        return ("Puedo ayudarte con: stock y precios (ej. 'stock de TOR-001'), catalogo, "
                "cotizaciones y pedidos (ej. 'cotizar CL-001 TOR-001:50, EPP-001:20'), "
                "despachos, credito y derivaciones tecnicas. Indica tu consulta.")

    # ------------------------------------------------------------- trazabilidad
    def _escribir_log(self, consulta, intencion, herramientas, contexto, pasos, respuesta, cliente_id):
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entrada = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "sesion_id": self.sesion_id,
            "cliente_id": cliente_id,
            "intencion": intencion,
            "consulta": consulta,
            "herramientas_usadas": herramientas,
            "pasos": pasos,
            "fuentes_rag": [c["id"] for c in contexto],
            "respuesta": respuesta,
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False) + "\n")