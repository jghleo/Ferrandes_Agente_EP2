"""Pruebas de integracion del agente completo (IL2.1 a IL2.3)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agente import AgenteFerrandes  # noqa: E402
from src.servicios import Servicios  # noqa: E402


class TestAgente(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.servicios = Servicios(db_path=Path(self.tmp.name) / "agente.db")
        self.agente = AgenteFerrandes(self.servicios)

    def tearDown(self):
        self.tmp.cleanup()

    def test_consulta_simple_stock(self):
        r = self.agente.responder("tienes stock del taladro HER-001?")
        self.assertIn("34", r)

    def test_consulta_flujo_pedido_completo(self):
        r = self.agente.responder("quiero hacer un pedido CL-001 con TOR-001:100 y EPP-001:50")
        self.assertIn("PEDIDO_CONFIRMADO", r)
        self.assertIn("PAT-", r)

    def test_derivacion_normativa(self):
        r = self.agente.responder("que EPP exige la norma para trabajo en altura?")
        self.assertIn("especialista", r)
        self.assertIn("TKT-", r)

    def test_memoria_corto_plazo_activa(self):
        self.agente.responder("hola")
        self.agente.responder("me ayudas?")
        self.assertEqual(len(self.servicios.mc), 4)  # 2 usuario + 2 agente

    def test_interaccion_registrada_en_largo_plazo(self):
        self.agente.responder("precio de ELE-001", cliente_id="CL-001")
        with self.servicios.ml._con() as con:
            n = con.execute("SELECT COUNT(*) AS c FROM interacciones").fetchone()["c"]
        self.assertEqual(n, 1)


if __name__ == "__main__":
    unittest.main()