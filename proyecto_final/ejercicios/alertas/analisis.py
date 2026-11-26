"""Análisis de las alertas de seguridad con pandas.

Opera sobre tablas construidas a partir de las alertas sin modificar los
objetos ni el gestor, y sin usar ``print``.
"""

from datetime import date

import pandas as pd

from .modelos import CAMPOS, ESTADOS, PRIORIDADES

PENDIENTES = ("abierta", "en_curso")


def a_tabla(incidencias) -> pd.DataFrame:
    """Convierte un iterable de alertas en un ``DataFrame`` tipado."""
    filas = [alerta.a_fila() for alerta in incidencias]
    if not filas:
        vacio = pd.DataFrame(columns=CAMPOS)
        vacio["id"] = vacio["id"].astype("int64")
        vacio["fecha_deteccion"] = pd.to_datetime(vacio["fecha_deteccion"])
        vacio["fecha_cierre"] = pd.to_datetime(vacio["fecha_cierre"])
        return vacio

    tabla = pd.DataFrame(filas)[CAMPOS]
    tabla["id"] = tabla["id"].astype("int64")
    tabla["fecha_deteccion"] = pd.to_datetime(tabla["fecha_deteccion"])
    tabla["fecha_cierre"] = pd.to_datetime(tabla["fecha_cierre"])
    return tabla


def dias_de_resolucion(tabla: pd.DataFrame) -> pd.Series:
    """Devuelve los días transcurridos hasta el cierre para alertas cerradas."""
    if tabla.empty:
        return pd.Series(dtype="int64", index=pd.Index([], name="id"))

    cerradas = tabla[tabla["fecha_cierre"].notna()].copy()
    if cerradas.empty:
        return pd.Series(dtype="int64", index=pd.Index([], name="id"))

    dias = (cerradas["fecha_cierre"] - cerradas["fecha_deteccion"]).dt.days.astype("int64")
    resultado = pd.Series(dias.values, index=pd.Index(cerradas["id"].values, name="id"))
    return resultado


def tabla_estado_prioridad(tabla: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una tabla cruzada de conteos por estado y prioridad."""
    prioridades_desc = list(reversed(PRIORIDADES))
    if tabla.empty:
        return pd.DataFrame(0, index=list(ESTADOS), columns=prioridades_desc, dtype="int64")

    cruzada = pd.crosstab(
        tabla["estado"],
        tabla["prioridad"],
        rownames=["estado"],
        colnames=["prioridad"],
    )
    return cruzada.reindex(
        index=list(ESTADOS),
        columns=prioridades_desc,
        fill_value=0,
    ).astype("int64")


def resumen_por_tecnico(tabla: pd.DataFrame) -> pd.DataFrame:
    """Devuelve asignadas, pendientes y cerradas por analista/técnico."""
    columnas = ["asignadas", "pendientes", "cerradas"]
    if tabla.empty:
        return pd.DataFrame(columns=columnas, index=pd.Index([], name="asignada_a"), dtype="int64")

    df = tabla.copy()
    tecnico_limpio = df["asignada_a"].fillna("").astype(str).str.strip()
    df["tecnico"] = tecnico_limpio.where(tecnico_limpio != "", "Sin asignar")
    df["es_pendiente"] = df["estado"].isin(PENDIENTES).astype("int64")
    df["es_cerrada"] = (df["estado"] == "cerrada").astype("int64")

    agrupado = df.groupby("tecnico", as_index=True).agg(
        asignadas=("id", "count"),
        pendientes=("es_pendiente", "sum"),
        cerradas=("es_cerrada", "sum"),
    )
    agrupado.index.name = "asignada_a"
    agrupado = agrupado.astype("int64")

    # Ordena por asignadas descendente y luego alfabéticamente por nombre
    agrupado = agrupado.reset_index().sort_values(
        by=["asignadas", "asignada_a"],
        ascending=[False, True],
    ).set_index("asignada_a")
    return agrupado[columnas]


def indicadores(tabla: pd.DataFrame, hoy: date | None = None) -> dict:
    """Devuelve los indicadores principales del servicio con tipos nativos de Python."""
    fecha_ref = pd.Timestamp(hoy if hoy is not None else date.today())
    total = int(len(tabla))

    if total == 0:
        return {
            "total": 0,
            "pendientes": 0,
            "porcentaje_pendientes": 0.0,
            "sin_asignar": 0,
            "dias_medios_resolucion": None,
            "antiguedad_maxima": 0,
        }

    mascara_pendientes = tabla["estado"].isin(PENDIENTES)
    pendientes_count = int(mascara_pendientes.sum())
    porcentaje_pendientes = float(round((pendientes_count / total) * 100, 1))

    tecnico_limpio = tabla["asignada_a"].fillna("").astype(str).str.strip()
    sin_asignar = int((mascara_pendientes & (tecnico_limpio == "")).sum())

    resolucion = dias_de_resolucion(tabla)
    if resolucion.empty:
        dias_medios: float | None = None
    else:
        dias_medios = float(round(float(resolucion.mean()), 1))

    if pendientes_count == 0:
        antiguedad_maxima = 0
    else:
        pendientes_df = tabla[mascara_pendientes]
        antiguedades = (fecha_ref - pendientes_df["fecha_deteccion"]).dt.days.clip(lower=0)
        antiguedad_maxima = int(antiguedades.max())

    return {
        "total": total,
        "pendientes": pendientes_count,
        "porcentaje_pendientes": porcentaje_pendientes,
        "sin_asignar": sin_asignar,
        "dias_medios_resolucion": dias_medios,
        "antiguedad_maxima": antiguedad_maxima,
    }
def alertas_sin_asignar(tabla: pd.DataFrame) -> pd.DataFrame:
    """Devuelve las alertas que no tienen analista asignado."""
    columnas_visibles = ["id", "titulo", "origen", "prioridad", "estado", "fecha_deteccion"]
    if tabla.empty:
        return pd.DataFrame(columns=columnas_visibles)

    tecnico_limpio = tabla["asignada_a"].fillna("").astype(str).str.strip()
    sin_asignar_df = tabla[tecnico_limpio == ""].copy()
    if sin_asignar_df.empty:
        return pd.DataFrame(columns=columnas_visibles)

    sin_asignar_df["fecha_deteccion"] = sin_asignar_df["fecha_deteccion"].dt.strftime("%Y-%m-%d")
    return sin_asignar_df[columnas_visibles].reset_index(drop=True)