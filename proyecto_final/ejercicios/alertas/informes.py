"""Textos para mostrar por pantalla sobre las alertas de seguridad.

Las funciones de este módulo devuelven cadenas y no usan ``print``.
"""

from datetime import date

from .gestor import GestorIncidencias
from .modelos import ESTADOS, PRIORIDADES, Alerta

ANCHO = 78


def linea(incidencia: Alerta) -> str:
    """Devuelve una alerta en una línea de columnas alineadas."""
    asignada = incidencia.asignada_a if incidencia.asignada_a else "-"
    return (
        f"{incidencia.id:>4}  "
        f"{incidencia.prioridad:<10}"
        f"{incidencia.estado:<10}"
        f"{asignada:<12}"
        f"{incidencia.titulo}"
    )


def listado(incidencias: list[Alerta]) -> str:
    """Devuelve una tabla con cabecera, línea separadora y una línea por alerta."""
    if not incidencias:
        return "No hay incidencias."

    cabecera = (
        f"{'ID':>4}  "
        f"{'PRIORIDAD':<10}"
        f"{'ESTADO':<10}"
        f"{'ASIGNADA A':<12}"
        f"{'TÍTULO'}"
    )
    separador = "-" * ANCHO
    filas = [linea(alerta) for alerta in incidencias]
    return "\n".join([cabecera, separador, *filas])


def resumen(gestor: GestorIncidencias, hoy: date) -> str:
    """Devuelve el informe de situación con el formato establecido."""
    todas = list(gestor)
    total = len(todas)

    conteo_estados: dict[str, int] = {estado: 0 for estado in ESTADOS}
    for alerta in todas:
        conteo_estados[alerta.estado] += 1

    pendientes_lista = [alerta for alerta in todas if alerta.pendiente]
    prioridades_desc = tuple(reversed(PRIORIDADES))
    pendientes_prio: dict[str, int] = {prio: 0 for prio in prioridades_desc}
    for alerta in pendientes_lista:
        pendientes_prio[alerta.prioridad] += 1

    if pendientes_lista:
        mas_antigua = min(
            pendientes_lista,
            key=lambda a: (-a.dias_abierta(hoy), a.id),
        )
        dias_antigua = mas_antigua.dias_abierta(hoy)
        linea_antigua = f"Pendiente más antigua: n.º {mas_antigua.id}, {dias_antigua} días"
    else:
        linea_antigua = "Pendiente más antigua: ninguna"

    borde = "=" * ANCHO
    titulo_centrado = "INFORME DE INCIDENCIAS".center(ANCHO)

    lineas_estado = [
        f"  {estado:<12}{conteo_estados[estado]:>4}" for estado in ESTADOS
    ]
    lineas_pendientes = [
        f"  {prio:<12}{pendientes_prio[prio]:>4}" for prio in prioridades_desc
    ]

    partes = [
        borde,
        titulo_centrado,
        borde,
        f"Fecha del informe: {hoy.isoformat()}",
        f"Total de incidencias: {total}",
        "",
        "Por estado",
        *lineas_estado,
        "",
        "Pendientes por prioridad",
        *lineas_pendientes,
        "",
        linea_antigua,
        borde,
    ]
    return "\n".join(partes)