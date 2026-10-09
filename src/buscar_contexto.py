"""Recuperacion de contexto semantico (IL2.2, IL2.4).

Implementa un retriever por similitud de palabras clave sobre los documentos
textuales de la empresa (fichas de catalogo, politicas y preguntas frecuentes).
Es el equivalente del "mock de embeddings" usado en el prototipo de la EP1
(asistente_rag.py), documentado como etapa 3 del pipeline RAG. En produccion
se reemplaza por un indice vectorial real (Chroma/FAISS + embeddings), tal como
se explica en el informe tecnico (seccion 3).
"""
import re

from .config import STOPWORDS


def tokenizar(texto: str) -> set:
    palabras = re.findall(r"[a-z0-9]+", texto.lower())
    return {p for p in palabras if p not in STOPWORDS and len(p) > 2}


def construir_corpus(datos: dict) -> list[dict]:
    """Convierte catalogo + politicas + faqs en documentos indexables."""
    documentos = []
    for p in datos["productos"]:
        texto = (
            f"{p['nombre']}. {p['descripcion']}. Categoria {p['categoria']}. "
            f"Proveedor {p['proveedor']}. " + " ".join(p["tags"])
        )
        documentos.append({"id": p["id"], "tipo": "producto", "texto": texto})
    pol = datos["politicas"]
    for clave in ("horario", "ubicacion", "despacho", "credito", "devoluciones"):
        valor = pol.get(clave)
        if isinstance(valor, dict):
            valor = " ".join(f"{k}: {v}" for k, v in valor.items())
        if valor:
            documentos.append({"id": f"pol_{clave}", "tipo": "politica",
                               "texto": f"{clave}: {valor}"})
    for f in datos["faqs"]:
        documentos.append({"id": f["id"], "tipo": "faq", "texto": f["texto"]})
    return documentos


def recuperar_contexto(datos: dict, consulta: str, top_k: int = 3) -> list[dict]:
    """Retorna los documentos mas relevantes para la consulta (retriever).
    Simula la busqueda semantica con puntaje por coincidencia de palabras clave.
    """
    palabras_consulta = tokenizar(consulta)
    if not palabras_consulta:
        return []
    puntuados = []
    for doc in construir_corpus(datos):
        palabras_doc = tokenizar(doc["texto"])
        score = len(palabras_consulta & palabras_doc)
        if score > 0:
            puntuados.append((score, doc))
    puntuados.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in puntuados[:top_k]]