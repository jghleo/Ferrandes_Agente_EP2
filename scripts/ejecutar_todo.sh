#!/usr/bin/env bash
# Ejecuta pruebas, demo y smoke test del agente Ferrandes (EP2).
# Uso: bash scripts/ejecutar_todo.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== 1) Pruebas unitarias (sin dependencias) =="
python3 tests/ejecutar_tests.py

echo
echo "== 2) Demo + evidencia de pruebas =="
python3 scripts/demo.py >/dev/null && echo "OK -> evidencia/evidencia_pruebas.txt, evidencia/logs_agente.jsonl"

echo
echo "== 3) Smoke test del agente LangChain (requiere langchain) =="
if python3 -c "import langchain" 2>/dev/null; then
  python3 scripts/smoke_langchain.py >/dev/null && echo "OK -> evidencia/evidencia_langchain.txt"
else
  echo "SALTADO (langchain no instalado): pip install -r requirements.txt"
fi

echo
echo "== 4) Verificación de artefactos =="
ls -1 evidencia/ assets/*.png informe/*.docx presentacion/*.pptx
echo "Todo listo."