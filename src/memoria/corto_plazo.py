"""Memoria de corto plazo (ILI 2.2): buffer conversacional por sesion.

Mantiene los ultimos N turnos de la conversacion activa para que el agente sea
coherente dentro de una tarea prolongada (por ejemplo, una cotizacion seguida de
la confirmacion del pedido en el mismo dialogo). Cuando el buffer se acerca a su
capacidad, se entrega un resumen comprimido de los turnos mas recientes.
"""
from collections import deque
from datetime import datetime


class MemoriaCortoPlazo:
    def __init__(self, max_turnos: int = 30):
        self._turnos: deque = deque(maxlen=max_turnos)
        self._limite = max_turnos

    def agregar(self, rol: str, contenido: str):
        self._turnos.append(
            {"rol": rol, "contenido": contenido, "ts": datetime.now().isoformat()}
        )

    def obtener(self) -> list[dict]:
        return list(self._turnos)

    def resumir(self, ultimas: int = 6) -> str:
        turnos = list(self._turnos)[-ultimas:]
        if not turnos:
            return "(sin historial en esta sesion)"
        return "\n".join(f"[{t['rol']}] {t['contenido']}" for t in turnos)

    def esta_saturada(self) -> bool:
        return len(self._turnos) >= self._limite

    def __len__(self):
        return len(self._turnos)