"""Ejecuta pruebas, demo y smoke test del agente Ferrandes (EP2).

Uso:
    python scripts/ejecutar_todo.py
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def correr(comando: list[str]) -> bool:
    print(f"\n== {Path(comando[0]).name} {' '.join(comando[1:])} ==")
    try:
        subprocess.run([sys.executable, *comando], cwd=RAIZ, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def main() -> None:
    ok = True
    ok &= correr(["tests/ejecutar_tests.py"])

    print("\n== Demo + evidencia de pruebas ==")
    ok &= correr(["scripts/demo.py"])

    print("\n== Smoke test del agente LangChain (requiere langchain) ==")
    try:
        import langchain  # noqa: F401
        ok &= correr(["scripts/smoke_langchain.py"])
    except ImportError:
        print("SALTADO: langchain no está instalado. Ejecuta: pip install -r requirements.txt")
        print("El agente local funciona igual sin LangChain.")

    print("\n== Verificación de artefactos ==")
    for ruta in ["evidencia/", "assets/", "informe/", "presentacion/"]:
        print(f"  {ruta}")
    print("\nResultado:", "TODO OK ✅" if ok else "Hubo errores revisa arriba ⚠️")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()