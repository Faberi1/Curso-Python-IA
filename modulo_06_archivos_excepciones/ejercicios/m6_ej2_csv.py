"""Módulo 6 - Ejercicio 2: CSV.

Todos los ficheros se abren con ``encoding="utf-8"`` y ``newline=""``.
"""

import csv
from pathlib import Path


def leer_csv(ruta, delimitador: str = ",") -> list[dict]:
    """Devuelve las filas del CSV como lista de diccionarios.

    Las claves son los nombres de la cabecera y todos los valores son cadenas.
    """
    with open(Path(ruta), "r", encoding="utf-8", newline="") as fichero:
        lector = csv.DictReader(fichero, delimiter=delimitador)
        return list(lector)


def cabecera(ruta) -> list[str]:
    """Devuelve la lista de nombres de columna. Con el fichero vacío, lista vacía."""
    with open(Path(ruta), "r", encoding="utf-8", newline="") as fichero:
        lector = csv.reader(fichero)
        return next(lector, [])


def escribir_csv(ruta, registros: list[dict], campos: list[str]) -> None:
    """Escribe los registros en un CSV con la cabecera indicada en ``campos``.

    Las claves de los registros que no estén en ``campos`` se ignoran.
    """
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", encoding="utf-8", newline="") as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=campos, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(registros)


def leer_ventas(ruta) -> list[dict]:
    """Lee un CSV de ventas y convierte ``unidades`` a ``int`` y ``precio`` a ``float``.

    El resto de los campos se dejan como cadenas.
    """
    filas = leer_csv(ruta)
    ventas: list[dict] = []
    for fila in filas:
        registro = dict(fila)
        if "unidades" in registro and registro["unidades"] != "":
            registro["unidades"] = int(registro["unidades"])
        if "precio" in registro and registro["precio"] != "":
            registro["precio"] = float(registro["precio"])
        ventas.append(registro)
    return ventas


def total_columna(ruta, columna: str) -> float:
    """Devuelve la suma de los valores de una columna numérica, con dos decimales."""
    filas = leer_csv(ruta)
    total = sum(float(fila[columna]) for fila in filas if fila.get(columna, "") != "")
    return round(total, 2)


def filtrar_csv(origen, destino, columna: str, valor: str) -> int:
    """Copia en ``destino`` las filas de ``origen`` en las que ``columna`` vale ``valor``.

    El fichero de destino conserva la cabecera y el orden de las columnas.
    Devuelve el número de filas copiadas.
    """
    campos = cabecera(origen)
    if not campos:
        escribir_csv(destino, [], [])
        return 0
    filas = leer_csv(origen)
    filtradas = [fila for fila in filas if fila.get(columna) == valor]
    escribir_csv(destino, filtradas, campos)
    return len(filtradas)


def convertir_delimitador(origen, destino, de: str = ";", a: str = ",") -> None:
    """Reescribe un CSV cambiando el delimitador.

    Tiene que funcionar aunque algún campo contenga cualquiera de los dos
    delimitadores: usa ``csv.reader`` y ``csv.writer``, no ``replace``.
    """
    ruta_destino = Path(destino)
    ruta_destino.parent.mkdir(parents=True, exist_ok=True)
    with open(Path(origen), "r", encoding="utf-8", newline="") as f_origen, open(ruta_destino, "w", encoding="utf-8", newline="") as f_destino:
        lector = csv.reader(f_origen, delimiter=de)
        escritor = csv.writer(f_destino, delimiter=a)
        escritor.writerows(lector)
