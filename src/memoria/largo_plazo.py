"""Memoria de largo plazo persistente (IL2.2, IL2.4).

Almacena en SQLite (libreria estandar) la memoria episodica y semantica del
agente: perfiles de clientes, cotizaciones, pedidos con historial de etapas,
tickets de escalamiento, ordenes de reposicion e interacciones. Ademas indexes
las fuentes documentales de la empresa para la recuperacion semantica de
contexto en flujos prolongados.

El esquema relacional es el "registro de orquestacion" que permite que una tarea
iniciada en una sesion (ej. cotizacion) sea retomada en otra sesion (ej.
confirmacion del pedido) sin perder estado. (Vease diagrama de arquitectura.)
"""
import json
import sqlite3
from datetime import datetime


class MemoriaLargoPlazo:
    def __init__(self, db_path):
        self.db_path = str(db_path)

    def _con(self):
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    # ------------------------------------------------------------------ DDL
    def inicializar(self):
        with self._con() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS clientes (
                    cliente_id TEXT PRIMARY KEY,
                    nombre TEXT, ciudad TEXT, credito INTEGER,
                    cupo_credito REAL, saldo_usado REAL,
                    metodo_pago_favorito TEXT, preferencias TEXT,
                    etiquetas TEXT, ultima_interaccion TEXT
                );
                CREATE TABLE IF NOT EXISTS interacciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT, cliente_id TEXT, sesion_id TEXT,
                    tipo TEXT, detalle TEXT
                );
                CREATE TABLE IF NOT EXISTS cotizaciones (
                    nro TEXT PRIMARY KEY, cliente_id TEXT, items TEXT,
                    subtotal REAL, descuento REAL, porcentaje_descuento INTEGER,
                    iva REAL, total REAL, estado TEXT, creado_en TEXT
                );
                CREATE TABLE IF NOT EXISTS pedidos (
                    nro TEXT PRIMARY KEY, nro_cotizacion TEXT, cliente_id TEXT,
                    items TEXT, etapa TEXT, historial_etapas TEXT, creado_en TEXT
                );
                CREATE TABLE IF NOT EXISTS tickets (
                    nro TEXT PRIMARY KEY, cliente_id TEXT, motivo TEXT,
                    estado TEXT, creado_en TEXT
                );
                CREATE TABLE IF NOT EXISTS ordenes_reposicion (
                    nro_oc TEXT PRIMARY KEY, producto_id TEXT, cantidad INTEGER,
                    proveedor TEXT, estado TEXT, creado_en TEXT
                );
                """
            )

    # ------------------------------------------------------------- utilidades
    def _ts(self) -> str:
        return datetime.now().isoformat(timespec="seconds")

    def ts(self) -> str:
        return self._ts()

    def _proximo_numero(self, tabla: str, prefijo: str, columna: str = "nro") -> str:
        with self._con() as con:
            filas = con.execute(f"SELECT {columna} FROM {tabla}").fetchall()
        max_n = 0
        for fila in filas:
            val = fila[0]
            if val and str(val).startswith(prefijo):
                try:
                    max_n = max(max_n, int(str(val).split("-")[-1]))
                except ValueError:
                    continue
        return f"{prefijo}-{max_n + 1:06d}"

    # --------------------------------------------------------------- clientes
    def upsert_cliente(self, cliente: dict):
        with self._con() as con:
            con.execute(
                """INSERT INTO clientes (cliente_id, nombre, ciudad, credito,
                     cupo_credito, saldo_usado, metodo_pago_favorito,
                     preferencias, etiquetas, ultima_interaccion)
                   VALUES (:id, :nombre, :ciudad, :credito, :cupo, :saldo,
                     :metodo, :preferencias, :etiquetas, :ultima)
                   ON CONFLICT(cliente_id) DO UPDATE SET
                     saldo_usado = excluded.saldo_usado,
                     preferencias = excluded.preferencias,
                     etiquetas = excluded.etiquetas,
                     ultima_interaccion = excluded.ultima_interaccion""",
                {
                    "id": cliente["id"],
                    "nombre": cliente["nombre"],
                    "ciudad": cliente["ciudad"],
                    "credito": int(cliente.get("credito", False)),
                    "cupo": cliente.get("cupo_credito", 0),
                    "saldo": cliente.get("saldo_usado", 0),
                    "metodo": cliente.get("metodo_pago_favorito", ""),
                    "preferencias": json.dumps(cliente.get("preferencias", [])),
                    "etiquetas": json.dumps(cliente.get("etiquetas", [])),
                    "ultima": cliente.get("ultima_interaccion") or self._ts(),
                },
            )

    def get_cliente(self, cliente_id: str) -> dict | None:
        with self._con() as con:
            fila = con.execute(
                "SELECT * FROM clientes WHERE cliente_id = ?", (cliente_id,)
            ).fetchone()
        if not fila:
            return None
        return {
            "id": fila["cliente_id"],
            "nombre": fila["nombre"],
            "preferencias": json.loads(fila["preferencias"] or "[]"),
            "etiquetas": json.loads(fila["etiquetas"] or "[]"),
            "saldo_usado": fila["saldo_usado"],
            "cupo_credito": fila["cupo_credito"],
            "credito": bool(fila["credito"]),
            "ultima_interaccion": fila["ultima_interaccion"],
        }

    # --------------------------------------------------------- interacciones
    def registrar_interaccion(self, cliente_id: str, sesion_id: str, tipo: str, detalle: str):
        with self._con() as con:
            con.execute(
                "INSERT INTO interacciones (ts, cliente_id, sesion_id, tipo, detalle)"
                " VALUES (?, ?, ?, ?, ?)",
                (self._ts(), cliente_id, sesion_id or "", tipo, detalle),
            )

    # ------------------------------------------------------------ cotizaciones
    def nueva_cotizacion(self) -> str:
        return self._proximo_numero("cotizaciones", "COT")

    def guardar_cotizacion(self, nro, cliente_id, items, subtotal, descuento,
                           porcentaje, iva, total, estado="PENDIENTE_CONFIRMACION"):
        with self._con() as con:
            con.execute(
                """INSERT INTO cotizaciones (nro, cliente_id, items, subtotal,
                     descuento, porcentaje_descuento, iva, total, estado, creado_en)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (nro, cliente_id, json.dumps(items, ensure_ascii=False), subtotal,
                 descuento, porcentaje, iva, total, estado, self._ts()),
            )

    def get_cotizacion(self, nro: str) -> dict | None:
        with self._con() as con:
            fila = con.execute("SELECT * FROM cotizaciones WHERE nro = ?", (nro,)).fetchone()
        if not fila:
            return None
        return {
            "nro": fila["nro"], "cliente_id": fila["cliente_id"],
            "items": json.loads(fila["items"]),
            "subtotal": fila["subtotal"], "descuento": fila["descuento"],
            "porcentaje_descuento": fila["porcentaje_descuento"],
            "iva": fila["iva"], "total": fila["total"], "estado": fila["estado"],
        }

    # ----------------------------------------------------------------- pedidos
    def nuevo_pedido(self) -> str:
        return self._proximo_numero("pedidos", "PAT")

    def guardar_pedido(self, nro, nro_cotizacion, cliente_id, items, etapa, historial_etapas):
        with self._con() as con:
            con.execute(
                """INSERT INTO pedidos (nro, nro_cotizacion, cliente_id, items,
                     etapa, historial_etapas, creado_en) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (nro, nro_cotizacion, cliente_id, json.dumps(items, ensure_ascii=False),
                 etapa, json.dumps(historial_etapas, ensure_ascii=False), self._ts()),
            )

    def avanzar_pedido(self, nro: str, nueva_etapa: str):
        with self._con() as con:
            fila = con.execute("SELECT * FROM pedidos WHERE nro = ?", (nro,)).fetchone()
            if not fila:
                return
            historial = json.loads(fila["historial_etapas"] or "[]")
            historial.append({"etapa": nueva_etapa, "ts": self._ts()})
            con.execute(
                "UPDATE pedidos SET etapa = ?, historial_etapas = ? WHERE nro = ?",
                (nueva_etapa, json.dumps(historial, ensure_ascii=False), nro),
            )

    def get_pedido(self, nro: str) -> dict | None:
        with self._con() as con:
            fila = con.execute("SELECT * FROM pedidos WHERE nro = ?", (nro,)).fetchone()
        if not fila:
            return None
        return {
            "nro": fila["nro"], "nro_cotizacion": fila["nro_cotizacion"],
            "cliente_id": fila["cliente_id"], "items": json.loads(fila["items"]),
            "etapa": fila["etapa"],
            "historial_etapas": json.loads(fila["historial_etapas"] or "[]"),
        }

    # ----------------------------------------------------------------- tickets
    def nuevo_ticket(self) -> str:
        return self._proximo_numero("tickets", "TKT")

    def crear_ticket(self, cliente_id: str, motivo: str) -> str:
        nro = self.nuevo_ticket()
        with self._con() as con:
            con.execute(
                "INSERT INTO tickets (nro, cliente_id, motivo, estado, creado_en)"
                " VALUES (?, ?, ?, ?, ?)",
                (nro, cliente_id, motivo, "ABIERTO", self._ts()),
            )
        return nro

    # ------------------------------------------------------ ordenes de compra
    def nueva_oc(self) -> str:
        return self._proximo_numero("ordenes_reposicion", "OC", columna="nro_oc")

    def registrar_oc(self, producto_id: str, cantidad: int, proveedor: str) -> str:
        nro = self.nueva_oc()
        with self._con() as con:
            con.execute(
                """INSERT INTO ordenes_reposicion (nro_oc, producto_id, cantidad,
                     proveedor, estado, creado_en) VALUES (?, ?, ?, ?, ?, ?)""",
                (nro, producto_id, cantidad, proveedor, "EMITIDA", self._ts()),
            )
        return nro