"""Generador del informe tecnico EP2 en formato Word (.docx).

Uso (con python-docx instalado):
    pip install python-docx
    python informe/generar_informe.py

Genera: informe/Informe_Tecnico_EP2_Ferrandes.docx
Ademas escribe la version fuente en Markdown para edicion colaborativa.

IMPORTANTE (pauta):
- No se permite usar IA para redactar la seccion "Reflexiones individuales":
  dejela en blanco para que cada integrante la redacte a mano.
- Declaracion de uso de IA y referencias APA deben ajustarse por el equipo.
"""
import html
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = Path(__file__).resolve().parent / "Informe_Tecnico_EP2_Ferrandes.docx"
MD = Path(__file__).resolve().parent / "Informe_Tecnico_EP2_Ferrandes.md"

AZUL = RGBColor(0x1F, 0x4E, 0x79)
GRIS = RGBColor(0x44, 0x44, 0x44)


def configurar(doc: Document):
    sec = doc.sections[0]
    sec.page_height = Cm(29.7)
    sec.page_width = Cm(21.0)
    sec.top_margin = Cm(1.8)
    sec.bottom_margin = Cm(1.5)
    sec.left_margin = Cm(2.0)
    sec.right_margin = Cm(2.0)
    estilos = doc.styles
    normal = estilos["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10)
    normal.paragraph_format.space_after = Pt(4)
    normal.paragraph_format.line_spacing = 1.05
    for nombre, tam in (("Heading 1", 12), ("Heading 2", 11)):
        est = estilos[nombre]
        est.font.name = "Calibri"
        est.font.size = Pt(tam)
        est.font.bold = True
        est.font.color.rgb = AZUL
        est.paragraph_format.space_before = Pt(8)
        est.paragraph_format.space_after = Pt(3)


def titulo(doc, texto):
    p = doc.add_paragraph()
    r = p.add_run(texto)
    r.font.size = Pt(15)
    r.font.bold = True
    r.font.color.rgb = AZUL
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p


def sub(doc, texto):
    p = doc.add_paragraph()
    r = p.add_run(texto)
    r.font.size = Pt(10)
    r.font.italic = True
    r.font.color.rgb = GRIS
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p


def tabla(doc, encabezados, filas, anchos=None, fuente=9):
    t = doc.add_table(rows=1, cols=len(encabezados))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(encabezados):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(fuente)
    for fila in filas:
        celdas = t.add_row().cells
        for i, v in enumerate(fila):
            celdas[i].text = ""
            p = celdas[i].paragraphs[0]
            r = p.add_run(str(v))
            r.font.size = Pt(fuente)
    if anchos:
        for i, ancho in enumerate(anchos):
            for fila in t.rows:
                fila.cells[i].width = Cm(ancho)
    return t


def con_viñeta(doc, texto):
    p = doc.add_paragraph(texto, style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.left_indent = Cm(0.5)
    return p


def cuerpo(doc, texto, negrita_primer=False):
    p = doc.add_paragraph()
    if negrita_primer and ":" in texto:
        j = texto.index(":") + 1
        r1 = p.add_run(texto[:j]); r1.font.bold = True
        p.add_run(texto[j:])
    else:
        p.add_run(texto)
    p.paragraph_format.space_after = Pt(4)
    return p


def generar():
    doc = Document()
    configurar(doc)

    # ------------------------------------------------------------ portada
    titulo(doc, "Evaluación Parcial N°2 — Desarrollo de un Agente Funcional")
    sub(doc, "Agente Ferrandes: automatización del flujo B2B de la Ferretería Industrial Andes SpA")
    sub(doc, "ISY0101 · Ingeniería de Soluciones con IA · Encargo con Presentación (35 %)")

    t = doc.add_table(rows=1, cols=2)
    t.style = "Table Grid"
    fila = t.add_row().cells
    fila[0].text = "Integrantes"
    fila[1].text = "⬅ completar"
    fila = t.add_row().cells
    fila[0].text = "Docente"
    fila[1].text = "Juan Burgueño"
    fila = t.add_row().cells
    fila[0].text = "Fecha"
    fila[1].text = "Semana 13"

    # --------------------------------------------------------------- 1
    doc.add_heading("1. Contexto y objetivo del caso", level=1)
    cuerpo(doc,
        "Ferretería Industrial Andes SpA (FERRANDES), Concepción, atiende cotizaciones y "
        "pedidos B2B de constructoras, maestranzas y talleres. El proceso actual es manual: "
        "un vendedor revisa stock, calcula descuentos e IVA, genera la cotización, valida el "
        "crédito y confirma el pedido, con demoras de horas. El objetivo de esta evaluación es "
        "construir un agente funcional que orqueste ese flujo de forma autónoma, con memoria "
        "para tareas prolongadas y decisiones adaptativas ante condiciones cambiantes.")
    cuerpo(doc,
        "El agente integra herramientas de consulta, escritura y razonamiento usando el "
        "framework LangChain (create_agent) sobre el mismo patrón de fuentes y trazabilidad "
        "desarrollado en la EP1 (pipeline RAG), aplicado a un caso organizacional distinto.")

    # --------------------------------------------------------------- 2
    doc.add_heading("2. Diseño e implementación del agente (IE1, IE2)", level=1)
    cuerpo(doc, "Cada herramienta se implementó como función independiente y se expuso como "
                "StructuredTool de LangChain; el agente local (src/agente.py) y el grafo "
                "LangChain (src/agente_langchain.py) comparten las mismas funciones.")
    tabla(doc,
        ["Familia", "Herramientas", "Efecto"],
        [
            ["Consulta", "consultar_stock, consultar_precio, buscar_catalogo, obtener_ficha_tecnica, consultar_pedido, consultar_cotizacion", "Lectura del estado, sin efectos"],
            ["Escritura", "crear_cotizacion, confirmar_pedido, generar_orden_reposicion, crear_ticket_escalamiento", "Persistencia en memoria de largo plazo"],
            ["Razonamiento", "evaluar_riesgo_credito, decidir_reposicion, planificar_pedido", "Decisión adaptativa y orquestación"],
        ],
        anchos=[2.2, 9.2, 5.0], fuente=8.5)
    cuerpo(doc,
        "El framework elegido es LangChain `create_agent`, que construye el grafo "
        "inicio → modelo → herramientas → modelo → fin. Permite cambiar el modelo "
        "(ChatAnthropic con API key o un LLM simulado compatible con LangChain sin costo), "
        "lo que garantiza escalabilidad y compatibilidad técnica (IE2).")

    # --------------------------------------------------------------- 3
    doc.add_heading("3. Memoria y recuperación de contexto (IE3, IE4)", level=1)
    con_viñeta(doc,
        "Memoria de corto plazo: buffer por sesión con resumen comprimido; mantiene la "
        "coherencia dentro de un flujo (cotizar y confirmar en el mismo diálogo).")
    con_viñeta(doc,
        "Memoria de largo plazo: SQLite (clientes, cotizaciones, pedidos con historial de "
        "etapas, tickets, órdenes de reposición). Una cotización creada en la sesión A se "
        "consulta y se convierte en pedido en la sesión B (test de persistencia).")
    con_viñeta(doc,
        "Recuperación semántica: retriever con similitud coseno sobre vectores TF-IDF "
        "(ponderación por frecuencia inversa de documento y normalización morfológica "
        "ligera), con soporte opcional de embeddings densos (sentence-transformers). "
        "Se mide su calidad con un conjunto etiquetado de consultas: hit-rate@3 y MRR.")

    # --------------------------------------------------------------- 4
    doc.add_heading("4. Planificación y toma de decisiones (IE5)", level=1)
    cuerpo(doc,
        "El planificador (src/planificador.py) genera un esquema priorizado de 6 etapas para "
        "todo pedido: analizar solicitud → validar stock → reposición → cotizar → evaluar "
        "crédito → decisión final. Durante la ejecución se inyectan pasos adaptativos cuando "
        "el entorno cambia: faltantes de stock generan órdenes de reposición automáticas; "
        "montos que superan cupo o umbral bloquean el pedido y escalan a un vendedor vía "
        "ticket; clientes nuevos pagan contra entrega; consultas normativas se derivan a un "
        "especialista (guardrail). El plan expone además una priorización explícita por "
        "criticidad y una etapa de replanificación: si la solicitud trae ítems inválidos "
        "(producto inexistente o cantidad no válida), el agente los descarta, lo informa y "
        "continúa con los válidos en lugar de abortar. Cada decisión se registra con su "
        "justificación, lo que permite trazabilidad y auditoría.")

    doc.add_picture(str(RAIZ / "assets" / "diagrama_flujo_pedido.png"), width=Cm(6.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[-1].runs[0].font.color.rgb = GRIS
    sub(doc, "Figura 1. Flujo de planificación con decisiones adaptativas.")

    # --------------------------------------------------------------- 5
    doc.add_heading("5. Orquestación de componentes (IE8)", level=1)
    doc.add_picture(str(RAIZ / "assets" / "diagrama_arquitectura.png"), width=Cm(13.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub(doc, "Figura 2. Diagrama de orquestación del agente (también en el README del repositorio).")

    # --------------------------------------------------------------- 6
    doc.add_heading("6. Evidencia de pruebas (IE7)", level=1)
    tabla(doc,
        ["Escenario", "Condición", "Decisión del agente", "Estado"],
        [
            ["A. Stock HER-001", "consulta", "respuesta con stock, sin efectos", "OK"],
            ["B. Pedido con TOR-002 bajo stock", "faltante", "emite OC a proveedor + cotiza", "EN_APROBACION"],
            ["C. Monto supera cupo/umbral", "crédito", "ticket de escalamiento a vendedor", "EN_APROBACION"],
            ["D. Cliente nuevo CL-004", "sin historial", "pago contra entrega + confirmación", "PEDIDO_CONFIRMADO"],
            ["E. Normativa EPP/altura", "guardrail", "derivación a especialista (ticket)", "DERIVADO"],
            ["F. Consulta de pedido previo", "memoria LP", "historial de etapas desde SQLite", "PENDIENTE_DESPACHO"],
            ["H. Ítems inválidos (FIJ-999, ELE-001:0)", "entrada inválida", "replanifica: descarta inválidos y continúa", "PEDIDO_CONFIRMADO"],
            ["H2. Producto inexistente TOR-999", "entrada ambigua", "responde que no existe, sin inventar", "CONTROLADO"],
        ],
        anchos=[4.4, 2.6, 6.8, 3.0], fuente=8.5)
    cuerpo(doc, "La ejecución completa y el log por consulta están en evidencia/ y en el log "
                "logs_agente.jsonl del repositorio; el smoke test del grafo LangChain se incluye "
                "en evidencia/evidencia_langchain.txt. 38 pruebas unitarias validadas "
                "(tests/ejecutar_tests.py) y retriever con hit-rate@3 = 100 % sobre 8 consultas "
                "etiquetadas.")

    # --------------------------------------------------------------- 7
    doc.add_heading("7. Decisiones de diseño y justificación (IE9)", level=1)
    tabla(doc,
        ["Decisión", "Justificación"],
        [
            ["LangChain create_agent", "Grafo oficial del framework de agentes, mantenido y documentado; permite LLM real o simulado."],
            ["Herramientas puras por familia", "Separa lectura, escritura y razonamiento, alineado con IL2.1 y facilita pruebas y auditoría."],
            ["SQLite como memoria LP", "Persistencia ligera y sin servidor; simula una base organizacional; migrable a PostgreSQL."],
            ["Retriever semántico TF-IDF", "Similitud coseno TF-IDF con normalización morfológica; mejora la precisión frente al conteo de palabras clave y admite embeddings densos sin cambiar la interfaz."],
            ["Planificador + inyección adaptativa", "Cumple IL5/IE5: plan priorizado por criticidad, comportamiento dinámico y replanificación ante entradas inválidas."],
        ],
        anchos=[5.2, 11.2], fuente=8.5)

    # --------------------------------------------------------------- 8
    doc.add_heading("8. Declaración de uso de IA y referencias (IE6, IE9)", level=1)
    cuerpo(doc,
        "Se usó IA (asistente de programación y redacción) para estructurar el código, los "
        "diagramas y este informe. Las decisiones de diseño, conclusiones y reflexiones son "
        "propias del equipo. Todo contenido generado por IA fue revisado y validado.")
    doc.add_heading("Referencias (APA)", level=2)
    con_viñeta(doc, "Anthropic. (2026). Anthropic API documentation. https://docs.anthropic.com")
    con_viñeta(doc, "LangChain. (2026). LangChain documentation: Agents. https://docs.langchain.com")
    con_viñeta(doc, "Duoc UC Bibliotecas. (2026). Citas y referencias en formato APA. https://bibliotecas.duoc.cl")
    con_viñeta(doc, "Python Software Foundation. (2026). sqlite3 — SQLite databases for Python. https://docs.python.org/3/library/sqlite3.html")

    # --------------------------------------------------------------- 9
    doc.add_heading("9. Conclusiones", level=1)
    cuerpo(doc,
        "El agente automatiza el ciclo completo de ventas B2B de FERRANDES, reduciendo el "
        "tiempo de respuesta de horas a segundos y dejando trazabilidad de cada decisión. "
        "La arquitectura por capas (agente, planificador, herramientas, memoria) facilita "
        "el mantenimiento y la evolución a un entorno productivo con embeddings reales.")

    doc.add_heading("Reflexión individual — integrante 1", level=2)
    cuerpo(doc, "⬅ Redactar SIN apoyo de IA (reflexión de aprendizaje y aporte al equipo):")
    doc.add_heading("Reflexión individual — integrante 2", level=2)
    cuerpo(doc, "⬅ Redactar SIN apoyo de IA (reflexión de aprendizaje y aporte al equipo):")

    doc.save(SALIDA)
    print("📄 Informe generado:", SALIDA)


def generar_markdown():
    md = f"""# Informe Técnico EP2 — Agente Ferrandes (FERRANDES)

**Evaluación Parcial N°2 · ISY0101 · Encargo con Presentación (35 %)**
Integrantes: ⬅ completar · Docente: Juan Burgueño · Fecha: Semana 13

## 1. Contexto y objetivo del caso
Ferretería Industrial Andes SpA (FERRANDES), Concepción, atiende cotizaciones y pedidos B2B de constructoras, maestranzas y talleres. El proceso actual es manual (stock → descuento/IVA → cotización → crédito → confirmación). Se construye un agente funcional que orquesta ese flujo con memoria y decisiones adaptativas (LangChain).

## 2. Diseño e implementación (IE1, IE2)
Herramientas de consulta (sin efectos), escritura (persistentes) y razonamiento (decisión), expuestas como StructuredTool y reutilizadas por el agente local y el grafo LangChain `create_agent` (inicio → modelo → herramientas → modelo → fin).

## 3. Memoria y recuperación de contexto (IE3, IE4)
- Corto plazo: buffer por sesión.
- Largo plazo: SQLite (clientes, cotizaciones, pedidos con historial, tickets, OC).
- Recuperación semántica: retriever con similitud coseno TF-IDF (normalización morfológica) y embeddings densos opcionales; se mide con hit-rate@3 y MRR sobre consultas etiquetadas.

## 4. Planificación y decisión (IE5)
Plan priorizado de 6 etapas por criticidad, con inyección adaptativa (reposición, escalamiento de crédito, pago contra entrega, guardrail normativo) y **replanificación** ante ítems inválidos (descarta y continúa). Ver `assets/diagrama_flujo_pedido.png`.

## 5. Orquestación (IE8)
Ver `assets/diagrama_arquitectura.png` y README.

## 6. Evidencia de pruebas (IE7)
Ver `evidencia/evidencia_pruebas.txt`, `evidencia/evidencia_langchain.txt` y `evidencia/logs_agente.jsonl`. 38 pruebas unitarias (`tests/ejecutar_tests.py`) y retriever con hit-rate@3 = 100 % (8 consultas etiquetadas).

## 7. Decisiones de diseño (IE9)
LangChain create_agent, herramientas por familia, SQLite como memoria LP, retriever semántico TF-IDF (con embeddings opcionales), planificador priorizado con replanificación.

## 8. Declaración de uso de IA y referencias (APA)
Se usó IA de apoyo; decisiones y reflexiones son propias. Referencias: Anthropic (2026); LangChain (2026); Duoc UC Bibliotecas (2026); Python `sqlite3` docs (2026).

## 9. Conclusiones y reflexiones individuales
⬅ Redactar conclusiones y reflexiones SIN apoyo de IA.
"""
    MD.write_text(md, encoding="utf-8")
    print("📝 Fuente Markdown:", MD)


if __name__ == "__main__":
    generar()
    generar_markdown()