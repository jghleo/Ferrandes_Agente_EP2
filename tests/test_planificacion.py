"""Pruebas del planificador y las decisiones adaptativas (IL2.3 / IL5)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.servicios import Servicios  # noqa: E402
from src.planificador import Planificador  # noqa: E402


class BasePlan(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.servicios = Servicios(db_path=Path(self.tmp.name) / "plan.db")
        self.planificador = Planificador(self.servicios)

    def tearDown(self):
        self.tmp.cleanup()


class TestDiseñoPlan(BasePlan):
    def test_esquema_priorizado(self):
        plan = self.planificador.crear_plan_pedido("CL-001", "TOR-001:50")
        prioridades = [p.prioridad for p in plan]
        self.assertEqual(prioridades, sorted(prioridades))      # secuencia ordenada
        etapas = [p.etapa for p in plan]
        self.assertIn("4. CREAR_COTIZACION", etapas)
        self.assertIn("6. DECIDIR_FLUJO_FINAL", etapas)

    def test_precondiciones_de_cadena(self):
        plan = self.planificador.crear_plan_pedido("CL-001", "TOR-001:50")
        crear = next(p for p in plan if p.etapa == "4. CREAR_COTIZACION")
        final = next(p for p in plan if p.etapa == "6. DECIDIR_FLUJO_FINAL")
        self.assertEqual(crear.precondicion, "items_validos")
        self.assertEqual(final.precondicion, "decision_credito")


class TestFlujoPedido(BasePlan):
    def test_pedido_con_stock_suficiente(self):
        r = self.planificador.procesar_pedido("CL-001", "TOR-001:100, EPP-001:50")
        self.assertEqual(r["estado_final"], "PEDIDO_CONFIRMADO")
        self.assertIsNotNone(r["pedido"])
        self.assertIn("COT-", r["cotizacion"])

    def test_pedido_con_faltante_inyecta_reposicion(self):
        """Adaptacion: TOR-002 tiene stock 12 < solicitud, el plan inyecta OC."""
        r = self.planificador.procesar_pedido("CL-002", "TOR-002:100, ELE-002:50")
        etapas = [p["etapa"] for p in r["pasos"]]
        self.assertTrue(any("3b. EMITIR_ORDEN_COMPRA (TOR-002)" in e for e in etapas))
        tipos = {d["tipo"] for d in r["decisiones"]}
        self.assertIn("ADAPTACION", tipos)
        self.assertIn("ESTRATEGIA", tipos)

    def test_pedido_con_cupo_superado_escala(self):
        """Adaptacion: CL-002 (cupo disponible 1.55M) no cubre un total de 2M."""
        r = self.planificador.procesar_pedido(
            "CL-002", "HER-001:1, HER-001:1, HER-001:1, ELE-001:20, ELE-001:25, SOL-001:10"
        )
        # calculamos un monto alto: forzamos con cantidades que superen el cupo
        # (ver assertion del ticket)
        self.assertEqual(r["estado_final"], "EN_APROBACION")
        self.assertIsNotNone(r["ticket"])

    def test_cliente_nuevo_pago_contra_entrega(self):
        r = self.planificador.procesar_pedido("CL-004", "EPP-001:10")
        decisiones = " ".join(d["detalle"] + " " + d["razon"] for d in r["decisiones"])
        self.assertIn("PEDIDO_CONFIRMADO", r["estado_final"])
        self.assertIn("PAGO_CONTRA_ENTREGA", decisiones)


if __name__ == "__main__":
    unittest.main()