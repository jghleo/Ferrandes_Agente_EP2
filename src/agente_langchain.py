"""Agente funcional LangChain (IL2.1, IL2.2, IL2.3).

Compone el agente con el framework LangChain `create_agent` (grafo
modelo -> herramientas -> modelo) sobre las herramientas de la empresa.

Dos modos de ejecucion:
1. REAL:  si existe ANTHROPIC_API_KEY en el entorno, se usa Claude
   (ChatAnthropic) con tool calling nativo.
2. OFFLINE (evaluacion): se usa `FerretiaLLMSimulado`, un modelo de chat
   LangChain determinista que reimplementa la politica de decision del agente
   local. Permite probar el grafo y el loop de herramientas sin API ni costo,
   tal como el fallback de respuesta simulada de la EP1.

Ambos modos ejecutan las MISMAS herramientas (StructuredTool), por lo que la
orquestacion es identica.
"""
import os

from .agente import extraer_producto, extraer_items, extraer_nro, extraer_cliente
from .decisiones import clasificar_intencion
from .servicios import Servicios

ANTHROPIC_MODEL = os.environ.get("FERRANDES_MODEL", "claude-sonnet-4-6")

# LangChain es una dependencia OPCIONAL: si no está instalada, el agente local
# (src/agente.py) sigue funcionando sin problemas.
try:
    from langchain.agents import create_agent
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import AIMessage, ToolMessage
    from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

    LANGCHAIN_DISPONIBLE = True
except ImportError:  # pragma: no cover
    create_agent = None
    BaseChatModel = object
    AIMessage = ToolMessage = ChatGeneration = ChatGenerationChunk = ChatResult = None
    LANGCHAIN_DISPONIBLE = False

SYSTEM_PROMPT = (
    "Eres el agente virtual de la Ferreteria Industrial Andes (FERRANDES), "
    "Concepcion, Chile. Tu objetivo es automatizar el flujo B2B de ventas: "
    "resolver consultas de stock, precios, catalogo, estado de pedidos y "
    "cotizaciones usando SOLO las herramientas disponibles. Reglas: "
    "1) para pedidos usa la herramienta planificar_pedido; "
    "2) nunca inventes precios ni stock: usa las herramientas; "
    "3) las preguntas sobre normativas de seguridad o certificaciones EPP "
    "deben derivarse con crear_ticket_escalamiento; "
    "4) responde en espanol, breve y profesional."
)


class FerretiaLLMSimulado(BaseChatModel):
    """Modelo de chat LangChain determinista para operar offline.

    Replica la politica de decision del agente local: clasifica la intencion de
    la consulta, emite la(s) llamada(s) de herramienta adecuada(s) y produce la
    respuesta final a partir de los resultados. Permite validar el ciclo
    completo (grafo + herramientas) sin costo de API.
    """

    def __init__(self, servicios: Servicios | None = None, **kwargs):
        super().__init__(**kwargs)
        self._servicios = servicios or Servicios()
        self._tools = []

    @property
    def _llm_type(self) -> str:
        return "ferrandes-simulado"

    def bind_tools(self, tools, **kwargs):  # noqa: D102
        self._tools = list(tools)
        return self

    # --------------------------------------------------- politica de decision
    def _decidir_toolcall(self, consulta: str) -> dict:
        intencion = clasificar_intencion(consulta)
        producto = extraer_producto(consulta)
        cliente = extraer_cliente(consulta) or "CL-001"

        if intencion == "stock":
            return {"name": "consultar_stock", "args": {"producto_id": producto}}
        if intencion == "precio":
            return {"name": "consultar_precio", "args": {"producto_id": producto}}
        if intencion == "catalogo":
            termino = consulta.replace("catalogo", "").replace("buscar", " ").strip() or "ferreteria"
            return {"name": "buscar_catalogo", "args": {"termino": termino}}
        if intencion == "estado_pedido":
            return {"name": "consultar_pedido",
                    "args": {"nro_pedido": extraer_nro(consulta, "pedido") or "PAT-000000"}}
        if intencion in ("cotizacion", "pedido_nuevo"):
            return {"name": "planificar_pedido",
                    "args": {"cliente_id": cliente, "items": extraer_items(consulta) or "TOR-001:1"}}
        if intencion == "confirmar_pedido":
            return {"name": "confirmar_pedido",
                    "args": {"nro_cotizacion": extraer_nro(consulta, "cotizacion") or "COT-000000"}}
        if intencion == "reposicion":
            return {"name": "decidir_reposicion", "args": {"producto_id": producto}}
        if intencion == "credito":
            return {"name": "evaluar_riesgo_credito",
                    "args": {"cliente_id": cliente, "monto_total": 0.0}}
        if intencion == "normativa":
            return {"name": "crear_ticket_escalamiento",
                    "args": {"cliente_id": cliente, "motivo": f"Consulta normativa: {consulta}"}}
        return {}

    # ----------------------------------------------------------- motor LLM
    def _generar(self, messages) -> AIMessage:
        herramientas_ejecutadas = [
            m.name for m in messages if isinstance(m, ToolMessage)
        ]
        ultima_consulta = ""
        for m in messages:
            if hasattr(m, "type") and m.type == "human":
                ultima_consulta = str(getattr(m, "content", ""))
        ultimo_tool = None
        if herramientas_ejecutadas:
            ultimo_tool = herramientas_ejecutadas[-1]

        if not herramientas_ejecutadas:
            tc = self._decidir_toolcall(ultima_consulta)
            if tc:
                return AIMessage(content="", tool_calls=[{**tc, "id": f"call_{len(messages)}"}])
            return AIMessage(content=self._respuesta_general(ultima_consulta))

        # Reponer stock: segunda llamada al tool una vez evaluado el primero
        if ultimo_tool == "decidir_reposicion":
            resultado = [m.content for m in messages if isinstance(m, ToolMessage)][-1]
            if "REQUERIDA" in str(resultado):
                return AIMessage(content="", tool_calls=[{
                    "name": "generar_orden_reposicion",
                    "args": {"producto_id": extraer_producto(ultima_consulta), "cantidad": "auto"},
                    "id": f"call_{len(messages)}",
                }])

        # Respuesta final a partir del resultado de la(s) herramienta(s)
        contenido_detalle = [str(m.content) for m in messages if isinstance(m, ToolMessage)][-1]
        return AIMessage(content=f"Resultado de Ferrandes:\n{contenido_detalle}")

    def _respuesta_general(self, consulta: str) -> str:
        from .buscar_contexto import recuperar_contexto
        contexto = recuperar_contexto(self._servicios.datos, consulta, top_k=2)
        if contexto:
            return (f"Segun {contexto[0]['id']} de Ferrandes: {contexto[0]['texto']} "
                    "Puedo ayudarte con stock, precios, cotizaciones o pedidos.")
        return ("Puedo ayudarte con stock y precios, catalogo, cotizaciones y pedidos, "
                "despachos o derivaciones tecnicas (con ticket de especialista).")

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=self._generar(messages))])

    async def _astream(self, messages, stop=None, run_manager=None, **kwargs):
        yield ChatGenerationChunk(message=self._generar(messages))


def crear_agente_langchain(servicios: Servicios | None = None, api_key: str | None = None):
    """Construye el agente LangChain. Si no se entrega api_key, opera offline."""
    if not LANGCHAIN_DISPONIBLE:  # pragma: no cover
        raise ImportError(
            "LangChain no está instalado. Ejecuta: pip install -r requirements.txt"
        )
    servicios = servicios or Servicios()
    herramientas = construir_herramientas_langchain_import(servicios)

    if api_key:
        from langchain_anthropic import ChatAnthropic
        modelo = ChatAnthropic(model=ANTHROPIC_MODEL, api_key=api_key)
    else:
        modelo = FerretiaLLMSimulado(servicios=servicios)

    return create_agent(
        model=modelo,
        tools=herramientas,
        system_prompt=SYSTEM_PROMPT,
        name="AgenteFerrandes",
    )


def construir_herramientas_langchain_import(servicios):
    """Importador diferido para evitar ciclos de import en el paquete."""
    from .herramientas_langchain import construir_herramientas_langchain
    return construir_herramientas_langchain(servicios)


async def consultar_langchain(agente, consulta: str) -> list:
    """Ejecuta una consulta contra el agente LangChain y devuelve la bitacora
    de mensajes (Human -> AIMessage(tool_call) -> ToolMessage -> ... -> final)."""
    resultado = await agente.ainvoke({"messages": [{"role": "user", "content": consulta}]})
    return resultado.get("messages", [])