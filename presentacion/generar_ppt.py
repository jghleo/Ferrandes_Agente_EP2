"""Generador de la presentacion de la defensa EP2 (PPT).

Uso (con python-pptx instalado):
    pip install python-pptx
    python presentacion/generar_ppt.py
"""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = Path(__file__).resolve().parent / "Presentacion_EP2_Ferrandes.pptx"

AZUL = RGBColor(0x1F, 0x4E, 0x79)
CELESTE = RGBColor(0x2E, 0x86, 0xDE)
BLANCO = RGBColor(0xFF, 0xFF, 0xFF)
GRIS = RGBColor(0x60, 0x60, 0x60)
NARANJA = RGBColor(0xE6, 0x7E, 0x22)


def nueva_presentacion() -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def diapositiva(prs, titulo: str):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # en blanco
    # franja superior
    superior = slide.shapes.add_textbox(0, 0, prs.slide_width, Inches(1.0))
    tf = superior.text_frame
    tf.margin_left = Inches(0.5)
    tf.margin_top = Inches(0.15)
    p = tf.paragraphs[0]
    p.text = titulo
    p.font.size = Pt(30)
    p.font.bold = True
    p.font.color.rgb = BLANCO
    # fondo de franja via rectangulo
    fondo = slide.shapes.add_shape(1, 0, 0, prs.slide_width, Inches(1.0))  # MSO_SHAPE.RECTANGLE
    fondo.fill.solid()
    fondo.fill.fore_color.rgb = AZUL
    fondo.line.fill.background()
    fondo.shadow.inherit = False
    # reordenar: poner el fondo detras (el texto se dibuja despues de nuevo)
    slide.shapes._spTree.remove(fondo._element)
    slide.shapes._spTree.insert(2, fondo._element)
    return slide


def caja_bullets(slide, items, left, top, width, height, tam=16, color=GRIS):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    primera = True
    for item in items:
        p = tf.paragraphs[0] if primera else tf.add_paragraph()
        primera = False
        p.text = item
        p.font.size = Pt(tam)
        p.font.color.rgb = color
        p.space_after = Pt(8)
    return tb


def generar():
    prs = nueva_presentacion()

    # ------------------------------------------------- 1 portada
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    fondo = slide.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height)
    fondo.fill.solid(); fondo.fill.fore_color.rgb = AZUL; fondo.line.fill.background(); fondo.shadow.inherit = False
    tb = slide.shapes.add_textbox(Inches(1), Inches(1.6), Inches(11), Inches(4))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = "Agente Ferrandes"
    p.font.size = Pt(54); p.font.bold = True; p.font.color.rgb = BLANCO
    p = tf.add_paragraph(); p.text = "Automatización del flujo B2B — Ferretería Industrial Andes SpA"
    p.font.size = Pt(22); p.font.color.rgb = CELESTE
    p = tf.add_paragraph(); p.text = "Evaluación Parcial N°2 · ISY0101 · Ingeniería de Soluciones con IA"
    p.font.size = Pt(18); p.font.color.rgb = BLANCO
    p = tf.add_paragraph(); p.text = "Integrantes: ⬅ completar  |  Docente: Juan Burgueño"
    p.font.size = Pt(16); p.font.color.rgb = CELESTE

    # ------------------------------------------------- 2 contexto
    s = diapositiva(prs, "Contexto y problema")
    caja_bullets(s, [
        "FERRANDES (Concepción): venta y distribución B2B de tornillería, herramientas, EPP y materiales.",
        "Proceso actual manual: stock → descuento/IVA → cotización → crédito → confirmación.",
        "Demoras de horas, errores de cálculo y sin trazabilidad (SLA 48h de despacho).",
        "EP1: prototipo RAG de asistente (respuestas).",
        "EP2: agente FUNCIONAL que ejecuta acciones y decide (LangChain).",
    ], 0.7, 1.3, 12, 5, tam=18)

    # ------------------------------------------------- 3 solución
    s = diapositiva(prs, "Solución: agente orquestador")
    caja_bullets(s, [
        "3 familias de herramientas: CONSULTA · ESCRITURA · RAZONAMIENTO (13 tools).",
        "Memoria de corto plazo (sesión) + largo plazo (SQLite) para flujos prolongados.",
        "Planificador: esquema priorizado de 6 etapas con inyección adaptativa.",
        "Framework: LangChain create_agent (grafo start→model→tools→model→end).",
        "LLM real (Claude) o modelo simulado sin costo para evaluar.",
    ], 0.7, 1.3, 12, 5, tam=18)

    # ------------------------------------------------- 4 arquitectura
    s = diapositiva(prs, "Arquitectura y orquestación")
    s.shapes.add_picture(str(RAIZ / "assets" / "diagrama_arquitectura.png"),
                         Inches(3.0), Inches(1.2), height=Inches(5.6))

    # ------------------------------------------------- 5 herramientas
    s = diapositiva(prs, "Herramientas del agente (IL2.1)")
    datos = [
        ("CONSULTA", "stock, precio, catálogo, ficha, pedido, cotización", "lectura sin efectos"),
        ("ESCRITURA", "cotización, pedido, orden de reposición, ticket", "persistente + trazabilidad"),
        ("RAZONAMIENTO", "riesgo de crédito, reposición, plan de pedido", "decisión adaptativa"),
    ]
    top = 1.4
    for nombre, lista, efecto in datos:
        tb = s.shapes.add_textbox(Inches(0.7), Inches(top), Inches(12), Inches(1.5))
        tf = tb.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = nombre
        p.font.size = Pt(20); p.font.bold = True; p.font.color.rgb = NARANJA
        p = tf.add_paragraph(); p.text = f"{lista} → {efecto}"
        p.font.size = Pt(16); p.font.color.rgb = GRIS
        top += 1.85

    # ------------------------------------------------- 6 memoria
    s = diapositiva(prs, "Memoria y recuperación de contexto (IL2.2)")
    caja_bullets(s, [
        "Corto plazo: buffer por sesión + resumen comprimido (coherencia en el diálogo).",
        "Largo plazo (SQLite): clientes, cotizaciones, pedidos con historial de etapas, tickets y OC.",
        "Continuidad: cotización de la sesión A → confirmación/estado en la sesión B (persistencia real).",
        "Recuperación semántica (RAG): retriever sobre catálogo, políticas y FAQs (mismo enfoque EP1).",
        "Trazabilidad: evidencia/logs_agente.jsonl con fuentes y decisiones por consulta.",
    ], 0.7, 1.3, 12, 5, tam=17)

    # ------------------------------------------------- 7 planificación
    s = diapositiva(prs, "Planificación y decisiones adaptativas (IL2.3)")
    s.shapes.add_picture(str(RAIZ / "assets" / "diagrama_flujo_pedido.png"),
                         Inches(0.5), Inches(1.15), height=Inches(6.0))
    caja_bullets(s, [
        "Stock bajo → OC automática + entrega programada.",
        "Monto > cupo/umbral → EN_APROBACION + ticket.",
        "Cliente nuevo → pago contra entrega.",
        "Normativa EPP → deriva a especialista (guardrail).",
    ], 4.6, 1.5, 8.2, 5, tam=16, color=NARANJA)

    # ------------------------------------------------- 8 demo
    s = diapositiva(prs, "Demo en vivo")
    caja_bullets(s, [
        "1) Consulta de stock y precio (herramienta de consulta).",
        "2) Pedido con faltante TOR-002: el agente emite OC y cotiza (adaptación).",
        "3) Pedido que supera cupo: escalamiento a vendedor con ticket.",
        "4) Memoria: estado del pedido PAT-000001 retomado en otra consulta.",
        "Comando: python scripts/demo.py (sin API, sin costo).",
    ], 0.7, 1.3, 12, 5, tam=18)

    # ------------------------------------------------- 9 evidencias
    s = diapositiva(prs, "Evidencia y resultados")
    caja_bullets(s, [
        "29 pruebas unitarias validadas (tests/ejecutar_tests.py) — todas 'ok'.",
        "9 escenarios de negocio en evidencia/evidencia_pruebas.txt.",
        "Smoke test del grafo LangChain offline: evidencia/evidencia_langchain.txt.",
        "Flujos: PEDIDO_CONFIRMADO, EN_APROBACION, DERIVADO (guardrail).",
        "README + diagramas de orquestación + informe técnico (5 páginas).",
    ], 0.7, 1.3, 12, 5, tam=17)

    # ------------------------------------------------- 10 cierre
    s = diapositiva(prs, "Cierre")
    caja_bullets(s, [
        "Decisiones de diseño justificadas por alineación con el flujo (IE9).",
        "Autonomía demostrada: decisión adaptativa ante stock, crédito y normativa.",
        "Repositorio: código + documentación + evidencia reproducible.",
        "Siguiente paso: embeddings reales (Chroma/FAISS) y despliegue en la organización.",
        "¡Gracias! Preguntas →",
    ], 0.7, 1.3, 12, 5, tam=18)

    prs.save(SALIDA)
    print("📊 Presentación generada:", SALIDA)


if __name__ == "__main__":
    generar()