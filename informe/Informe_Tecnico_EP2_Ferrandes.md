# Informe Técnico EP2 — Agente Ferrandes (FERRANDES)

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
