"""Recuperacion de contexto semantico (IL2.2, IL2.4 / IE4).

Implementa el recuperador de contexto del agente RAG. Evoluciona el retriever de
palabras clave de la EP1 a un esquema de **similitud semantica** con dos modos:

- ``tfidf`` (por defecto): similitud coseno sobre vectores **TF-IDF**. Pondera los
  terminos discriminantes (por frecuencia inversa de documento) y normaliza por
  longitud del documento, lo que corrige los sesgos del conteo simple de
  coincidencias de la EP1.
- ``embeddings`` (opcional): si ``sentence-transformers`` esta instalado, usa
  **embeddings densos** y similitud coseno real. Se activa con ``modo="auto"``
  cuando la libreria esta disponible, sin cambiar nada del resto del sistema.

El contrato publico se mantiene: ``tokenizar`` (usado por ``consulta.py``),
``construir_corpus`` y ``recuperar_contexto`` siguen devolviendo documentos
``{"id", "tipo", "texto"}`` (ahora con un campo extra ``score``), por lo que el
agente local, el agente LangChain y las herramientas no requieren cambios.

Ademas se incluye ``evaluar_recuperacion`` para medir la calidad del retriever
(hit-rate@k y MRR) sobre un conjunto etiquetado de consultas, requisito de
trazabilidad del indicador IE4.
"""
import math
import os
import re
from collections import Counter

from .config import STOPWORDS


# Largo de la raiz por prefijo usada para emparejar variantes morfologicas
# (plurales, genero, conjugaciones): "ubicados"/"ubicacion" -> "ubica".
LARGO_RAIZ = 5


def _raiz(palabra: str) -> str:
    """Normalizacion morfologica ligera: conserva el prefijo significativo."""
    return palabra[:LARGO_RAIZ] if len(palabra) >= LARGO_RAIZ else palabra


def tokenizar(texto: str) -> set:
    """Normaliza y tokeniza el texto (minusculas, sin stopwords, con raiz)."""
    palabras = re.findall(r"[a-z0-9]+", texto.lower())
    return {_raiz(p) for p in palabras if p not in STOPWORDS and len(p) > 2}


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


# --------------------------------------------------------------------- TF-IDF
def _idf(documentos: list[dict]) -> dict:
    """Frecuencia inversa de documento (suavizada) para cada termino."""
    df = Counter()
    for doc in documentos:
        for termino in tokenizar(doc["texto"]):
            df[termino] += 1
    n = len(documentos) or 1
    return {t: math.log((n + 1) / (frec + 1)) + 1 for t, frec in df.items()}


def _vector_tfidf(texto: str, idf: dict) -> dict:
    """Vector TF-IDF normalizado de un texto."""
    conteo = Counter(tokenizar(texto))
    if not conteo:
        return {}
    total = sum(conteo.values())
    return {t: (frec / total) * idf.get(t, 0.0) for t, frec in conteo.items()}


def _coseno(v1: dict, v2: dict) -> float:
    """Similitud coseno entre dos vectores dispersos (dict termino -> peso)."""
    if not v1 or not v2:
        return 0.0
    comunes = set(v1) & set(v2)
    numerador = sum(v1[t] * v2[t] for t in comunes)
    n1 = math.sqrt(sum(x * x for x in v1.values()))
    n2 = math.sqrt(sum(x * x for x in v2.values()))
    if not n1 or not n2:
        return 0.0
    return numerador / (n1 * n2)


def _recuperar_tfidf(documentos, consulta, top_k):
    idf = _idf(documentos)
    v_consulta = _vector_tfidf(consulta, idf)
    if not v_consulta:
        return []
    puntuados = []
    for doc in documentos:
        score = _coseno(v_consulta, _vector_tfidf(doc["texto"], idf))
        if score > 0:
            puntuados.append((score, doc))
    puntuados.sort(key=lambda x: x[0], reverse=True)
    return [{**doc, "score": round(score, 4)} for score, doc in puntuados[:top_k]]


# ------------------------------------------------------- embeddings (opcional)
_MODELO_EMBEDDINGS = None
MODELO_EMBEDDINGS_DEFECTO = "paraphrase-multilingual-MiniLM-L12-v2"


def _modelo_embeddings():
    """Carga (una sola vez) el modelo de embeddings si esta disponible."""
    global _MODELO_EMBEDDINGS
    if _MODELO_EMBEDDINGS is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            _MODELO_EMBEDDINGS = False
        else:
            _MODELO_EMBEDDINGS = SentenceTransformer(
                os.environ.get("FERRANDES_EMBEDDINGS_MODEL", MODELO_EMBEDDINGS_DEFECTO)
            )
    return _MODELO_EMBEDDINGS or None


def _recuperar_embeddings(documentos, consulta, top_k):
    modelo = _modelo_embeddings()
    if modelo is None:
        return None
    vectores = modelo.encode([d["texto"] for d in documentos], normalize_embeddings=True)
    v_consulta = modelo.encode([consulta], normalize_embeddings=True)[0]
    similitudes = vectores @ v_consulta
    orden = similitudes.argsort()[::-1][:top_k]
    return [{**documentos[i], "score": round(float(similitudes[i]), 4)}
            for i in orden if similitudes[i] > 0]


# ------------------------------------------------------------------ API publica
def recuperar_contexto(datos: dict, consulta: str, top_k: int = 3,
                       modo: str | None = None) -> list[dict]:
    """Retorna los documentos mas relevantes para la consulta.

    modo: "tfidf" (por defecto, sin dependencias), "embeddings" (requiere
    sentence-transformers) o "auto" (usa embeddings si estan disponibles y, si
    no, cae a tfidf). Si se omite, se toma de la variable de entorno
    FERRANDES_RETRIEVER_MODE (util para activar embeddings sin editar codigo,
    por ejemplo en Google Colab); su valor por defecto es "tfidf".
    """
    modo = modo or os.environ.get("FERRANDES_RETRIEVER_MODE", "tfidf")
    documentos = construir_corpus(datos)
    if not documentos:
        return []
    if modo in ("auto", "embeddings"):
        resultado = _recuperar_embeddings(documentos, consulta, top_k)
        if resultado is not None:
            return resultado
        if modo == "embeddings":
            raise RuntimeError(
                "modo='embeddings' requiere sentence-transformers (pip install "
                "sentence-transformers) o usar modo='tfidf'."
            )
    return _recuperar_tfidf(documentos, consulta, top_k)


# Conjunto etiquetado de consultas para medir la calidad del retriever (IE4).
CASOS_EVALUACION = [
    ("stock de tornillo inoxidable", "TOR-001"),
    ("cuantas horas demora el despacho en concepcion", "faq_despacho"),
    ("horario de atencion", "pol_horario"),
    ("como devuelvo un producto", "faq_devolucion"),
    ("donde estan ubicados", "pol_ubicacion"),
    ("que EPP entregan", "faq_epp"),
    ("necesito un taladro percutor", "HER-001"),
    ("puedo pagar con credito", "faq_credito"),
]


def evaluar_recuperacion(datos: dict, casos: list | None = None, top_k: int = 3,
                         modo: str | None = None) -> dict:
    """Mide la calidad del retriever: hit-rate@k y MRR (rango reciproco medio).

    `casos` es una lista de tuplas (consulta, id_esperado). Si se omite, usa
    `CASOS_EVALUACION`. `modo` sigue la misma regla que `recuperar_contexto`.
    """
    casos = casos or CASOS_EVALUACION
    modo = modo or os.environ.get("FERRANDES_RETRIEVER_MODE", "tfidf")
    aciertos = 0
    suma_rr = 0.0
    detalle = []
    for consulta, esperado in casos:
        resultados = recuperar_contexto(datos, consulta, top_k=top_k, modo=modo)
        ids = [d["id"] for d in resultados]
        posicion = ids.index(esperado) + 1 if esperado in ids else 0
        aciertos += 1 if posicion else 0
        suma_rr += (1.0 / posicion) if posicion else 0.0
        detalle.append({"consulta": consulta, "esperado": esperado,
                        "obtenido": ids, "hit": bool(posicion)})
    n = len(casos) or 1
    return {
        "n_casos": len(casos),
        "top_k": top_k,
        "modo": modo,
        "hit_rate": round(aciertos / n, 3),
        "mrr": round(suma_rr / n, 3),
        "detalle": detalle,
    }
