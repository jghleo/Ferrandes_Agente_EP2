"""Pruebas del recuperador de contexto semantico (IL2.2 / IE4).

Ademas de la relevancia por consulta, se mide la calidad del retriever con un
conjunto etiquetado (hit-rate@k y MRR).
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.buscar_contexto import evaluar_recuperacion, recuperar_contexto  # noqa: E402
from src.datos import cargar_datos  # noqa: E402


class TestRecuperacionSemantica(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datos = cargar_datos()

    def test_relevancia_por_consulta(self):
        r = recuperar_contexto(self.datos, "stock de tornillo inoxidable", top_k=1)
        self.assertEqual(r[0]["id"], "TOR-001")

        r = recuperar_contexto(self.datos, "como devuelvo un producto", top_k=1)
        self.assertEqual(r[0]["tipo"], "faq")

        r = recuperar_contexto(self.datos, "cuantas horas demora el despacho en concepcion", top_k=3)
        ids = [d["id"] for d in r]
        self.assertTrue({"faq_despacho", "pol_despacho"} & set(ids))

    def test_variante_morfologica(self):
        """Normalizacion de raiz: 'ubicados' empareja con la politica de ubicacion."""
        r = recuperar_contexto(self.datos, "donde estan ubicados", top_k=1)
        self.assertEqual(r[0]["id"], "pol_ubicacion")

    def test_score_ordenado_y_presente(self):
        r = recuperar_contexto(self.datos, "taladro percutor", top_k=3)
        self.assertTrue(r)
        scores = [d["score"] for d in r]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertTrue(all(0 < s <= 1.0 for s in scores))

    def test_sin_coincidencias(self):
        r = recuperar_contexto(self.datos, "zzzz qqqq", top_k=3)
        self.assertEqual(r, [])

    def test_metricas_de_calidad(self):
        """El retriever etiquetado debe tener hit-rate@3 alto (>= 0.8)."""
        metricas = evaluar_recuperacion(self.datos, top_k=3)
        self.assertEqual(metricas["n_casos"], 8)
        self.assertGreaterEqual(metricas["hit_rate"], 0.8)
        self.assertGreaterEqual(metricas["mrr"], 0.8)


if __name__ == "__main__":
    unittest.main()
