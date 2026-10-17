"""Demo del agente Ferrandes (EP2).

Ejecuta los escenarios de negocio del caso Ferreteria Industrial Andes y genera
la evidencia de pruebas en evidencia/evidencia_pruebas.txt, el log de
trazabilidad evidencia/logs_agente.jsonl y la base de memoria
datos_ferrandes.db (memoria de largo plazo persistente).

Uso:
    python scripts/demo.py
"""
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DB_PATH
from src.agente import AgenteFerrandes
from src.servicios import Servicios


def main():
    # Base de datos nueva por ejecucion (evidencia reproducible)
    DB_PATH.unlink(missing_ok=True)

    servicios = Servicios(db_path=DB_PATH)
    linea_separador = "=" * 78

    escenarios = [
        (
            "ESCENARIO A - CONSULTA (herramienta de consulta)",
            "tienes stock del taladro HER-001?",
            "CL-001",
            True,
        ),
        (
            "ESCENARIO B - FLUJO COMPLETO DE PEDIDO CON ADAPTACION (falta stock de TOR-002)",
            "quiero hacer un pedido CL-002 con TOR-002:100 y ELE-001:20 y ELE-002:50",
            "CL-002",
            True,
        ),
        (
            "ESCENARIO C - DECISION ADAPTATIVA POR CREDITO (monto supera el cupo/umbral)",
            "hacer un pedido CL-002 con SOL-001:80 y HER-001:30",
            "CL-002",
            True,
        ),
        (
            "ESCENARIO D - CLIENTE NUEVO: PAGO CONTRA ENTREGA (regla de credito)",
            "cotizar CL-004 con EPP-001:40 y EPP-002:10",
            "CL-004",
            True,
        ),
        (
            "ESCENARIO D2 - CONFIRMACION SEGUN ESTADO EN MEMORIA (idempotencia)",
            "confirma el pedido de la cotizacion COT-000003",
            "CL-004",
            True,
        ),
        (
            "ESCENARIO E - GUARDRAIL: DERIVACION NORMATIVA A ESPECIALISTA",
            "que EPP me exige la normativa para trabajo en altura?",
            "CL-002",
            True,
        ),
        (
            "ESCENARIO F1 - MEMORIA DE CORTO PLAZO: dialogo previo (sesion 1)",
            "hola, soy de Constructora Montemar",
            "CL-001",
            True,
        ),
        (
            "ESCENARIO F2 - MEMORIA DE LARGO PLAZO: retomando cotizacion previa",
            "estado de mi pedido PAT-000001",
            "CL-001",
            True,
        ),
        (
            "ESCENARIO G - RECUPERACION SEMANTICA (RAG) PARA PREGUNTA GENERAL",
            "cuantas horas demora el despacho en concepcion?",
            None,
            True,
        ),
        (
            "ESCENARIO H - REPLANIFICACION ANTE ITEMS INVALIDOS (producto inexistente / cantidad 0)",
            "quiero cotizar CL-001 con TOR-001:5, FIJ-999:3 y ELE-001:0",
            "CL-001",
            True,
        ),
        (
            "ESCENARIO H2 - ENTRADA AMBIGUA (producto/cliente inexistente)",
            "tienes stock del producto TOR-999?",
            "CL-999",
            True,
        ),
    ]

    agente = AgenteFerrandes(servicios, sesion_id="demo-2026")
    lineas: list[str] = []
    for titulo, consulta, cliente_id, _ in escenarios:
        print(f"\n{linea_separador}\n{titulo}\nCONSULTA: {consulta}\n{'-' * 78}")
        lineas.append(f"\n{linea_separador}\n{titulo}\nCONSULTA: {consulta}\n{'-' * 78}")
        try:
            respuesta = agente.responder(consulta, cliente_id=cliente_id)
        except Exception as e:  # noqa: BLE001
            respuesta = f"[ERROR EN ESCENARIO]\n{traceback.format_exc(limit=3)}"
        print(respuesta)
        lineas.append(respuesta)

    # --------------------------------------------------------- resumen y cierre
    separador_cierre = f"\n{linea_separador}\nRESUMEN DE TRAZABILIDAD"
    print(separador_cierre)
    lineas.append(separador_cierre)

    resumen = servicios.ml
    lineas.append(
        f"- Interacciones registradas en memoria de largo plazo: "
        f"{_contar(resumen, 'interacciones')}"
    )
    lineas.append(
        f"- Cotizaciones generadas: {_contar(resumen, 'cotizaciones')} | "
        f"Pedidos: {_contar(resumen, 'pedidos')} | "
        f"Tickets de escalamiento: {_contar(resumen, 'tickets')} | "
        f"Ordenes de reposicion (OC): {_contar(resumen, 'ordenes_reposicion')}"
    )
    lineas.append(f"- Turnos en memoria de corto plazo de la sesion demo: {len(servicios.mc)}")
    lineas.append(f"- Log de trazabilidad: evidencia/logs_agente.jsonl")
    lineas.append(f"- Base de datos de memoria persistente: {DB_PATH.name}")

    # metricas del retriever semantico (IE4)
    from src.buscar_contexto import evaluar_recuperacion
    metricas = evaluar_recuperacion(servicios.datos, top_k=3)
    lineas.append(
        f"- Retriever semantico TF-IDF: {metricas['n_casos']} consultas etiquetadas, "
        f"hit-rate@{metricas['top_k']}={metricas['hit_rate']:.0%}, MRR={metricas['mrr']:.2f}"
    )

    print("\n".join(l for l in lineas[-7:]))

    # ------------------------------------------------------------- guardar evidencia
    evidencia_dir = Path(__file__).resolve().parent.parent / "evidencia"
    evidencia_dir.mkdir(exist_ok=True)
    with open(evidencia_dir / "evidencia_pruebas.txt", "w", encoding="utf-8") as f:
        f.write(
            "DEMO AGENTE FERRANDES - EVALUACION PARCIAL 2 (ISY0101)\n"
            "Ferreteria Industrial Andes SpA (FERRANDES), Concepcion, Chile\n"
        )
        f.write("\n".join(lineas))
        f.write(f"\n\nEjecutado el {__import__('datetime').datetime.now().isoformat(timespec='seconds')}\n")
    print(f"\nEvidencia guardada en {evidencia_dir / 'evidencia_pruebas.txt'}")


def _contar(ml, tabla: str) -> int:
    with ml._con() as con:
        return con.execute(f"SELECT COUNT(*) AS c FROM {tabla}").fetchone()["c"]


if __name__ == "__main__":
    main()