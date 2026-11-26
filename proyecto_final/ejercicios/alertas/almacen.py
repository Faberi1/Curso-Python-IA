"""Persistencia de las alertas de seguridad en un fichero CSV."""

import csv
import logging
from pathlib import Path

from .excepciones import DatosNoValidos, ErrorDeAlmacen
from .modelos import CAMPOS, Alerta

logger = logging.getLogger(__name__)


def guardar(ruta, incidencias) -> None:
    """Escribe las alertas en un CSV con la cabecera ``CAMPOS``."""
    ruta_path = Path(ruta)
    try:
        ruta_path.parent.mkdir(parents=True, exist_ok=True)
        filas = [alerta.a_fila() for alerta in incidencias]
        with ruta_path.open("w", encoding="utf-8", newline="") as fichero:
            escritor = csv.DictWriter(fichero, fieldnames=CAMPOS)
            escritor.writeheader()
            escritor.writerows(filas)
    except OSError as exc:
        raise ErrorDeAlmacen(f"No se pudo guardar el fichero {ruta_path}: {exc}") from exc

    logger.info("Guardadas %d alertas en %s", len(filas), ruta_path)


def cargar(ruta) -> list[Alerta]:
    """Lee las alertas de un CSV y las devuelve en una lista."""
    ruta_path = Path(ruta)
    if not ruta_path.exists():
        return []

    alertas: list[Alerta] = []
    try:
        with ruta_path.open("r", encoding="utf-8", newline="") as fichero:
            lector = csv.DictReader(fichero)
            if lector.fieldnames != CAMPOS:
                raise DatosNoValidos(
                    f"Cabecera inválida en {ruta_path}: {lector.fieldnames}"
                )
            for numero_linea, fila in enumerate(lector, start=2):
                try:
                    alertas.append(Alerta.desde_fila(fila))
                except DatosNoValidos as exc:
                    raise ErrorDeAlmacen(f"Línea {numero_linea}: {exc}") from exc
    except DatosNoValidos as exc:
        raise ErrorDeAlmacen(f"Línea 1: {exc}") from exc
    except OSError as exc:
        raise ErrorDeAlmacen(f"No se pudo leer el fichero {ruta_path}: {exc}") from exc

    return alertas