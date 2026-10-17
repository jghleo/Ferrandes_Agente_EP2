"""Generador del notebook de Google Colab para ejecutar la EP2.

No requiere dependencias: genera colab/EP2_Agente_Ferrandes_Colab.ipynb
"""
import json
from pathlib import Path

SALIDA = Path(__file__).resolve().parent / "EP2_Agente_Ferrandes_Colab.ipynb"


def md(texto: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": texto.splitlines(keepends=True)}


def codigo(texto: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": texto.splitlines(keepends=True),
    }


CELDAS = [
    md(
"""# 🤖 EP2 — Agente Ferrandes (Ferretería Industrial Andes)

**ISY0101 · Ingeniería de Soluciones con IA · Evaluación Parcial N°2**

Este notebook ejecuta el repositorio completo en Google Colab:

1. Copia el repositorio (GitHub) o sube el ZIP de **Ferrandes_Agente_EP2**.
2. Ejecuta las **38 pruebas unitarias** (sin instalar nada: solo librería estándar).
3. Ejecuta la **demo** que genera la evidencia (`evidencia/`).
4. (Opcional) Smoke test del agente **LangChain** con `pip install -r requirements.txt`.
5. **Guarda los resultados** en Google Drive o los descarga a tu PC.

> ⚠️ En Colab la carpeta `/content` es temporal: al cerrar la sesión se borra,
> por eso el paso 5 (guardar/descargar) es obligatorio antes de salir.
"""),
    codigo(
"""# 1) Copiar el repositorio
# Opción A — CLONAR DESDE GITHUB (reemplaza la URL por la de tu repo):

URL_REPO = "https://github.com/TU_USUARIO/TU_REPO.git"   # ← cambia esto

!git clone "$URL_REPO" ferrandes 2>&1 | tail -2
%cd ferrandes
!ls"""),
    codigo(
"""# 1b) Opción B — SUBIR EL ZIP (si no usaste Git)
# Arrastra "Proyecto_EP2_Ferrandes.zip" al panel de archivos (izquierda) y corre esta celda:

import os, zipfile, glob

zips = sorted(glob.glob("/content/*.zip"))
print("ZIPs detectados:", zips)
if os.path.exists("/content/ferrandes/README.md"):
    print("Ya hay un repo clonado en /content/ferrandes: no hace falta descomprimir.")
elif zips:
    with zipfile.ZipFile(zips[0]) as z:
        z.extractall("/content")
    carpeta = "/content/Ferrandes_Agente_EP2"
    %cd {carpeta}
    print("Descomprimido. Contenido:", len(os.listdir(".")), "elementos")
else:
    print("No se encontró ZIP. Arrastra el archivo o clona el repo en el paso 1a.")

%pwd"""),
    md(
"""## 2) Pruebas unitarias del agente

Ejecuta las 38 pruebas: herramientas, memoria de corto/largo plazo,
recuperación semántica (TF-IDF y métricas), planificación, decisiones
adaptativas y replanificación.
"""),
    codigo(
"""# 2) Pruebas unitarias
!python tests/ejecutar_tests.py
"""),
    md(
"""## 3) Demo + evidencia

`scripts/demo.py` ejecuta 11 escenarios de negocio (stock, pedidos con
reposición automática, crédito, cliente nuevo, guardrail normativo, memoria,
RAG y replanificación ante ítems inválidos) y genera:

- `evidencia/evidencia_pruebas.txt` — salida completa
- `evidencia/logs_agente.jsonl` — trazabilidad por consulta
- `datos_ferrandes.db` — memoria de largo plazo (SQLite)
"""),
    codigo(
"""# 3) Demo completa (genera la evidencia)
!python scripts/demo.py > /tmp/demo_salida.txt 2>&1
# mostramos un resumen de la salida
!tail -25 /tmp/demo_salida.txt
print("\\nArchivos de evidencia:")
!ls -la evidencia/"""),
    md(
"""## 4) (Opcional) Agente LangChain

Solo si quieres mostrar la orquestación con el **framework LangChain**
(`create_agent`) o usar Claude con tu API key. El resto del proyecto funciona
sin estos paquetes.
"""),
    codigo(
"""# 4) Instalar LangChain (opcional, ~1 min) y correr smoke test
!pip install -q -r requirements.txt
!python scripts/smoke_langchain.py
"""),
    codigo(
"""# 4b) (Opcional) Otra consulta sobre el agente local (chat rápido)
import sys; sys.path.insert(0, ".")
from src.agente import AgenteFerrandes
agente = AgenteFerrandes()
print(agente.responder("tienes stock del taladro HER-001?"))
print()
print(agente.responder("cotizar CL-001 con TOR-001:100 y EPP-001:50"))
print()
print(agente.responder("que EPP me exige la normativa para trabajo en altura?"))
"""),
    md(
"""## 4c) (Opcional) Embeddings densos y métricas del retriever (IE4)

Compara el retriever TF-IDF (por defecto) con embeddings reales sobre el mismo
conjunto etiquetado. En Colab la descarga del modelo es rápida.
"""),
    codigo(
"""# 4c) Embeddings densos + comparación de métricas
!pip install -q sentence-transformers
import sys; sys.path.insert(0, ".")
from src.datos import cargar_datos
from src.buscar_contexto import evaluar_recuperacion

datos = cargar_datos()
print("TF-IDF    :", evaluar_recuperacion(datos, modo="tfidf"))
print("Embeddings:", evaluar_recuperacion(datos, modo="embeddings"))
# Para que TODO el agente use embeddings, activa la variable de entorno:
# import os; os.environ["FERRANDES_RETRIEVER_MODE"] = "auto"
"""),
    md(
"""## 5) GUARDAR los resultados 🔒

**Antes de cerrar la sesión** descarga los artefactos a tu PC o guárdalos en
Google Drive. En Colab la carpeta `/content` se borra al terminar.
"""),
    codigo(
"""# 5a) Descargar artefactos a tu PC (se descarga cada archivo)
from google.colab import files

import os
archivos = [
    "evidencia/evidencia_pruebas.txt",
    "evidencia/logs_agente.jsonl",
    "informe/Informe_Tecnico_EP2_Ferrandes.docx",
    "presentacion/Presentacion_EP2_Ferrandes.pptx",
]
for a in archivos:
    if os.path.exists(a):
        files.download(a)
        print("Descargado:", a)
    else:
        print("No existe (se genera en pasos 3/4):", a)
"""),
    codigo(
"""# 5b) Guardar TODO en Google Drive (con copia completa de la carpeta evidencia)
from google.colab import drive
drive.mount("/content/drive")   # acepta la autorización en el navegador

import shutil, os, glob
dst = "/content/drive/MyDrive/EP2_Ferrandes/resultados"
os.makedirs(dst, exist_ok=True)

for carpeta in ["evidencia", "assets", "informe", "presentacion"]:
    if os.path.isdir(carpeta):
        shutil.copytree(carpeta, f"{dst}/{carpeta}", dirs_exist_ok=True)

if os.path.exists("datos_ferrandes.db"):
    shutil.copy("datos_ferrandes.db", f"{dst}/datos_ferrandes.db")

print("Guardado en Google Drive:")
!ls -la "$dst"
"""),
    codigo(
"""# 5c) Crear un ZIP con todo y descargarlo (método más simple)
import shutil, os
shutil.make_archive("/content/EP2_Ferrandes_resultados", "zip",
                    root_dir=".", base_dir=".")
from google.colab import files
files.download("/content/EP2_Ferrandes_resultados.zip")
print("ZIP generado y descargado ✅")
"""),
    md(
"""## 6) Cierre y recordatorios de la pauta

- Completar **nombres de integrantes** en `informe/` y `presentacion/`.
- Redactar las **reflexiones individuales SIN IA** (sección 9 del informe).
- Subir el repositorio a **GitHub/GitLab** (README, código y evidencia) y enviar
  el enlace + el informe por AVA y al correo del docente.
- Declarar el uso de IA y citar referencias APA (ya incluidas en el informe).
"""),
]


def generar():
    nb = {
        "cells": CELDAS,
        "metadata": {
            "colab": {"provenance": [], "toc_visible": True, "name": "EP2_Agente_Ferrandes_Colab"},
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3"},
        },
        "nbformat": 4,
        "nbformat_minor": 0,
    }
    SALIDA.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Notebook generado:", SALIDA)


if __name__ == "__main__":
    generar()