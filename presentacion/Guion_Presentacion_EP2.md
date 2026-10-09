# Guion de presentación — EP2 Agente Ferrandes

**Formato:** 20 minutos (10 expo + 10 preguntas) · 2 integrantes · apoyo visual PPT.

> **Reglas de la pauta:** participación equitativa, lenguaje técnico, respaldo con
> evidencia, demo en vivo (IE7–IE10).

---

## Distribución de tiempos (10 min de exposición)

| Tiempo | Bloque | Responsable |
|---|---|---|
| 0:00–1:30 | Problema y contexto del caso | Integrante A |
| 1:30–3:30 | Diseño del agente: herramientas y framework (LangChain) | Integrante B |
| 3:30–5:00 | Memoria corto/largo plazo y recuperación semántica | Integrante A |
| 5:00–6:30 | Planificación y decisiones adaptativas (ejemplos) | Integrante B |
| 6:30–8:30 | **Demo en vivo** (`python scripts/demo.py`) | Integrante A (teclado) |
| 8:30–9:30 | Evidencia + decisiones de diseño justificadas | Integrante B |
| 9:30–10:00 | Cierre y conclusión | Ambos |

## Mensajes clave que hay que defender

### 1. Problema (IA)
- FERRANDES procesa cotizaciones/pedidos B2B de forma manual → horas de demora y
  errores de cálculo de IVA/descuentos.
- La EP1 dejó la base RAG; la EP2 exige **acción** (escritura/razonamiento), no solo respuesta.

### 2. Diseño (IB)
- **Frameworks:** LangChain `create_agent` (grafo `start → model → tools → model → end`).
- **13 herramientas** organizadas por familia: consulta (lectura), escritura
  (persistente), razonamiento (decisión). Cada una declarada una sola vez y
  expuesta como `StructuredTool` → **escalabilidad** y compatibilidad (IE2).
- Alternativa de modelo: `ChatAnthropic` real o `FerretiaLLMSimulado` (LangChain
  compatible, sin costo). Esto permite evaluar el grafo completo sin API key.

### 3. Memoria (IA)
- Corto plazo: buffer de sesión + resumen comprimido.
- Largo plazo: SQLite (clientes, cotizaciones, pedidos con historial de etapas,
  tickets, OC). **Continuidad de tareas**: cotización de sesión A → estado en
  sesión B (mostrar el test `test_persistencia_entre_sesiones`).
- Recuperación semántica: retriever por palabras clave (RAG) sobre catálogo,
  políticas y FAQs — continuidad del enfoque EP1.

### 4. Planificación (IB) — claves para IE7/IE9
- Esquema priorizado de 6 etapas (`crear_plan_pedido` en `src/planificador.py`).
- **Decisiones adaptativas** (mostrar evidencias):
  1. Faltante de stock → emite OC automática y agenda entrega (decisión ESTRATEGIA).
  2. Monto > cupo/umbral → EN_APROBACION + ticket (decisión BLOQUEA).
  3. Cliente nuevo → pago contra entrega (regla de crédito).
  4. Consulta normativa → deriva a especialista (guardrail, no inventa).

### 5. Demo en vivo (IA) — script exacto
1. `python tests/ejecutar_tests.py` → mostrar "Ran 29 tests… OK".
2. `python scripts/demo.py` y recorrer 2-3 escenarios:
   - Escenario A: consulta de stock.
   - Escenario B: pedido con faltante (reposición adaptativa).
   - Escenario C: escalamiento por crédito.
3. Mostrar `evidencia/logs_agente.jsonl` y el archivo `datos_ferrandes.db` (memoria).
4. (Opcional) `python scripts/smoke_langchain.py` → grafo del framework + tools.

### 6. Evidencia y justificación (IB)
- 29 pruebas unitarias; 3 familias de herramientas validadas por tests de
  memoria, planificación e integración.
- Tabla de escenarios con estados finales: PEDIDO_CONFIRMADO, EN_APROBACION,
  DERIVADO.
- Diagramas de orquestación (arquitectura + flujo) en `assets/`.

## Preguntas frecuentes que pueden hacer y respuestas sugeridas

- **¿Por qué LangChain y no otro framework?** Por *más documentado*, admite cambio
  de modelo (Claude o simulado), y su grafo de orquestación es explícito (fácil de
  justificar en IE8/IE9). Alternativas consideradas: Haystack (OCR/QA, menos loop
  de herramientas) y AutoGen (multiusuario, más orientado a conversación múltiple).
- **¿Cómo se garantiza que el agente no inventa?** Las respuestas salen solo de
  resultados de herramientas (SOP); las consultas normativas se derivan por regla.
- **¿La memoria es escalable?** SQLite simula una base organizacional; se migra a
  PostgreSQL/vector DB manteniendo el mismo esquema.
- **¿Qué pasa sin API key?** El agente local funciona 100% offline; el grafo
  LangChain usa un modelo simulado que emite tool calls deterministas.

## Checklist antes de presentar
- [ ] Completar nombres de integrantes en PPT, informe, README.
- [ ] Redactar reflexiones individuales sin IA (sección 9 del informe).
- [ ] Probar `python scripts/demo.py` en la máquina de la sala.
- [ ] Tener abierto el repo en GitHub/GitLab.
- [ ] Declarar el uso de IA y citar referencias APA en el informe.