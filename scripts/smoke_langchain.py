"""Smoke test del agente LangChain (create_agent) en modo OFFLINE.

No requiere API key: usa FerretiaLLMSimulado (modelo de chat determinista
compatible con LangChain) para validar que el grafo de orquestacion
start -> model -> tools -> model -> end ejecuta herramientas reales.

Genera evidencia en evidencia/evidencia_langchain.txt.

Uso (con las dependencias instaladas):
    pip install -r requirements.txt
    python scripts/smoke_langchain.py

Nota: con ANTHROPIC_API_KEY configurada, el mismo script usa ChatAnthropic
y las herramientas llamadas seran decididas por Claude en lugar del modelo
simulado (ver src/agente_langchain.py).
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DB_PATH  # noqa: E402
from src.agente_langchain import crear_agente_langchain, consultar_langchain  # noqa: E402
from src.servicios import Servicios  # noqa: E402


def render_mensaje(m) -> str:
    tipo = m.type
    contenido = (str(m.content)[:200] + "...") if m.content and len(str(m.content)) > 200 else (str(m.content) if m.content else "")
    tool_calls = getattr(m, "tool_calls", None)
    if tool_calls:
        detalle = ", ".join(f"{tc.get('name')}({tc.get('args')})" for tc in tool_calls)
        return f"[{tipo}] tooll_call -> {detalle}"
    nombre = getattr(m, "name", None)
    if nombre:
        return f"[{tipo}] name={nombre} respuesta={contenido!r}"
    return f"[{tipo}] {contenido!r}"


async def main() -> None:
    DB_PATH.unlink(missing_ok=True)
    servicios = Servicios(db_path=DB_PATH)
    agente = crear_agente_langchain(servicios)

    lineas: list[str] = []
    lineas.append("SMOKE TEST AGENTE LANGCHAIN (create_agent) - FERRANDES EP2")
    lineas.append("Modo: OFFLINE (modelo simulado) | herramientas: StructuredTool")
    lineas.append("=" * 70)
    graph_lines = []
    for linea in agente.get_graph().draw_ascii().splitlines():
        graph_lines.append(linea)
    lineas.extend(["GRAFO DE ORQUESTACION (intents):"] + graph_lines)

    consultas = [
        "tienes stock del taladro HER-001?",
        "quiero hacer un pedido CL-002 con TOR-002:100 y ELE-002:50",
        "que EPP me exige la normativa para trabajo en altura?",
    ]
    for c in consultas:
        lineas.append("\n" + "=" * 70)
        lineas.append("CONSULTA: " + c)
        mensajes = await consultar_langchain(agente, c)
        for m in mensajes:
            lineas.append(render_mensaje(m))

    salida = "\n".join(lineas) + "\n"
    print(salida)
    evidencia = Path(__file__).resolve().parent.parent / "evidencia"
    evidencia.mkdir(exist_ok=True)
    (evidencia / "evidencia_langchain.txt").write_text(salida, encoding="utf-8")
    print("Evidencia guardada en evidencia/evidencia_langchain.txt")


if __name__ == "__main__":
    asyncio.run(main())