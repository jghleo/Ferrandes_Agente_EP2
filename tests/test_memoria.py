"""Pruebas de memoria (IL2.2): corto plazo, largo plazo y recuperacion semantica."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.servicios import Servicios  # noqa: E402


class TestMemoriaCortoPlazo(unittest.TestCase):
    def test_buffer_y_resumen(self):
        from src.memoria.corto_plazo import MemoriaCortoPlazo
        m = MemoriaCortoPlazo(max_turnos=4)
        m.agregar("usuario", "hola")
        m.agregar("agente", "hola, soy el agente de Ferrandes")
        self.assertEqual(len(m), 2)
        resumen = m.resumir()
        self.assertIn("hola", resumen)

    def test_saturacion(self):
        from src.memoria.corto_plazo import MemoriaCortoPlazo
        m = MemoriaCortoPlazo(max_turnos=2)
        m.agregar("u", "1")
        m.agregar("a", "2")
        m.agregar("u", "3")
        self.assertTrue(m.esta_saturada())
        # el turno mas antiguo se evapo: solo quedan 2
        self.assertEqual(len(m), 2)


class TestMemoriaLargoPlazo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "memoria.db"

    def tearDown(self):
        self.tmp.cleanup()

    def test_persistencia_entre_sesiones(self):
        """Continuidad de tareas: la cotizacion de la sesion A se retoma en la B."""
        from src.memoria.largo_plazo import MemoriaLargoPlazo
        from src.herramientas.escritura import crear_cotizacion, confirmar_pedido

        m1 = MemoriaLargoPlazo(self.db)
        m1.inicializar()
        nro = m1.nueva_cotizacion()
        m1.guardar_cotizacion(nro, "CL-001", [{"producto_id": "TOR-001"}], 1000, 0, 0, 190, 1190)

        m2 = MemoriaLargoPlazo(self.db)   # nueva conexion = "nueva sesion"
        m2.inicializar()
        cot = m2.get_cotizacion(nro)
        self.assertIsNotNone(cot)
        self.assertEqual(cot["cliente_id"], "CL-001")

    def test_upsert_cliente(self):
        from src.memoria.largo_plazo import MemoriaLargoPlazo
        m = MemoriaLargoPlazo(self.db)
        m.inicializar()
        m.upsert_cliente({"id": "CL-999", "nombre": "Test SpA", "ciudad": "Conc",
                          "credito": True, "cupo_credito": 500000, "saldo_usado": 0,
                          "metodo_pago_favorito": "transferencia", "preferencias": [],
                          "etiquetas": ["test"], "ultima_interaccion": None})
        c = m.get_cliente("CL-999")
        self.assertEqual(c["nombre"], "Test SpA")

    def test_recuperacion_semantica(self):
        from src.datos import cargar_datos
        from src.buscar_contexto import recuperar_contexto
        datos = cargar_datos()

        doc1 = recuperar_contexto(datos, "stock de tornillo inoxidable", top_k=1)
        self.assertTrue(doc1)
        self.assertEqual(doc1[0]["id"], "TOR-001")

        doc2 = recuperar_contexto(datos, "horario de atencion", top_k=1)
        self.assertEqual(doc2[0]["tipo"], "politica")

        doc3 = recuperar_contexto(datos, "como devuelvo un producto", top_k=1)
        self.assertEqual(doc3[0]["tipo"], "faq")


if __name__ == "__main__":
    unittest.main()