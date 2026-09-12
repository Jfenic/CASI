#!/usr/bin/env bash
# Activa el entorno de desarrollo y actualiza el ejecutable `casi`.
#
# Uso (recomendado — activa la shell actual):
#   source scripts/dev.sh
#
# Uso (ejecutable — sincroniza y abre una shell con el venv activo):
#   ./scripts/dev.sh
#
# Solo sincronizar, sin abrir shell:
#   ./scripts/dev.sh --sync

set -euo pipefail

_on_error() {
  echo "error: el script falló (línea ${1:-?})" >&2
  if [[ -t 0 && -t 1 ]]; then
    read -r -p "Pulsa Enter para cerrar..." _
  fi
}
trap '_on_error $LINENO' ERR

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"

if ! command -v uv >/dev/null 2>&1; then
  echo "error: se necesita 'uv' (https://docs.astral.sh/uv/)" >&2
  return 1 2>/dev/null || exit 1
fi

cd "$ROOT"

echo "Sincronizando dependencias e instalando casi..."
uv sync --locked --group dev

_activate() {
  if [[ ! -f "$VENV/bin/activate" ]]; then
    echo "error: no se encontró $VENV/bin/activate" >&2
    return 1 2>/dev/null || exit 1
  fi
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
  hash -r 2>/dev/null || true
  echo "Entorno activado: $VENV"
  echo "casi -> $(command -v casi)"
}

if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
  _activate
else
  case "${1:-}" in
    --sync)
      echo "Listo. Activa el entorno con: source scripts/dev.sh"
      ;;
    -h | --help)
      sed -n '2,11p' "$0" | sed 's/^# \?//'
      ;;
    *)
      if [[ -t 0 && -t 1 ]]; then
        _activate
        exec "${SHELL:-/bin/bash}" -i
      else
        echo ""
        echo "Dependencias sincronizadas."
        echo "Abre una terminal en el proyecto y activa el entorno con:"
        echo "  source scripts/dev.sh"
        echo ""
        echo "(Si ejecutaste el script con doble clic o sin TTY, la shell no puede"
        echo " quedarse abierta; usa 'source' en una terminal ya abierta.)"
      fi
      ;;
  esac
fi
