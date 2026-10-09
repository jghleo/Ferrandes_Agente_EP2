"""Pruebas de las herramientas del agente (IL2.1): consulta, escritura y razonamiento."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.servicios import Servicios  # noqa: E402


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.servicios = Servicios(db_path=Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.tmp.cleanup()


class TestConsulta(BaseTest):
    def test_consultar_stock(self):
        from src.herramientas.consulta import consultar_stock
        texto = consultar_stock(self.servicios, "TOR-001")
        self.assertIn("850", texto)
        self.assertIn("TOR-001", texto)

    def test_consultar_stock_bajo_avisa_reposicion(self):
        from src.herramientas.consulta import consultar_stock
        texto = consultar_stock(self.servicios, "TOR-002")
        self.assertIn("BAJO", texto)

    def test_consultar_precio_con_iva(self):
        from src.herramientas.consulta import consultar_precio
        texto = consultar_precio(self.servicios, "EPP-001")
        # 8.990 neto + 19% = 10.698
        self.assertIn("10,698", texto)

    def test_buscar_catalogo(self):
        from src.herramientas.consulta import buscar_catalogo
        texto = buscar_catalogo(self.servicios, "taladro")
        self.assertIn("HER-001", texto)

    def test_ficha_tecnica(self):
        from src.herramientas.consulta import obtener_ficha_tecnica
        texto = obtener_ficha_tecnica(self.servicios, "SOL-001")
        self.assertIn("proveedor", texto.lower())


class TestEscritura(BaseTest):
    def test_crear_cotizacion_con_descuento(self):
        from src.herramientas.escritura import crear_cotizacion
        # subtotal: 850 x 120 = 102.000 + EPP-001 50 x 8990 = 449.500  -> 551.500 -> 5%
        txt = crear_cotizacion(self.servicios, "CL-001", "TOR-001:850, EPP-001:50")
        self.assertIn("COT-", txt)
        self.assertIn("5%", txt)

    def test_flujo_cotizacion_pedido(self):
        from src.herramientas.escritura import crear_cotizacion, confirmar_pedido
        from src.herramientas.consulta import consultar_pedido
        cot = crear_cotizacion(self.servicios, "CL-003", "ELE-002:200")
        nro_cot = "COT-" + cot.split("COT-")[1].split(" ")[0]
        pedido = confirmar_pedido(self.servicios, nro_cot)
        self.assertIn("PAT-", pedido)
        nro_ped = "PAT-" + pedido.split("PAT-")[1].split(" ")[0].strip()
        estado = consultar_pedido(self.servicios, nro_ped)
        self.assertIn("PENDIENTE_DESPACHO", estado)

    def test_orden_reposicion_auto(self):
        from src.herramientas.escritura import generar_orden_reposicion
        txt = generar_orden_reposicion(self.servicios, "TOR-002", "auto")
        self.assertIn("OC-", txt)
        # 150-12 = 138 unidades sugeridas
        self.assertIn("138", txt)

    def test_ticket_escalamiento(self):
        from src.herramientas.escritura import crear_ticket_escalamiento
        txt = crear_ticket_escalamiento(self.servicios, "CL-001", "validacion EPP en altura")
        self.assertIn("TKT-", txt)


class TestRazonamiento(BaseTest):
    def test_riesgo_credito_cliente_nuevo(self):
        from src.herramientas.razonamiento import evaluar_riesgo_credito
        txt = evaluar_riesgo_credito(self.servicios, "CL-004", 500_000)
        self.assertIn("PAGO_CONTRA_ENTREGA", txt)

    def test_riesgo_credito_cupo_insuficiente(self):
        from src.herramientas.razonamiento import evaluar_riesgo_credito
        # CL-002: cupo 2M, usado 450k -> disponible 1.55M; superado con 2M
        txt = evaluar_riesgo_credito(self.servicios, "CL-002", 2_000_000)
        self.assertIn("REQUIERE_APROBACION", txt)

    def test_riesgo_credito_ok(self):
        from src.herramientas.razonamiento import evaluar_riesgo_credito
        txt = evaluar_riesgo_credito(self.servicios, "CL-001", 100_000)
        self.assertIn("CREDITO_OK", txt)

    def test_decidir_reposicion(self):
        from src.herramientas.razonamiento import decidir_reposicion
        self.assertIn("REQUERIDA", decidir_reposicion(self.servicios, "SOL-001"))
        self.assertIn("NO REQUERIDA", decidir_reposicion(self.servicios, "ELE-002"))


if __name__ == "__main__":
    unittest.main()