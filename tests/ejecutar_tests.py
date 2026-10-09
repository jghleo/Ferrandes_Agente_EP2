"""Ejecutor de pruebas del proyecto (sin dependencias externas).

Uso:
    python tests/ejecutar_tests.py
"""
import sys
import unittest
from pathlib import Path

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent), pattern="test_*.py")
    resultado = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if resultado.wasSuccessful() else 1)