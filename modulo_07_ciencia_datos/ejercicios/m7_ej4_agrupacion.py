"""Módulo 7 - Ejercicio 4: agrupar, agregar y combinar.

Todas las funciones reciben un DataFrame de ventas limpio que ya tiene la
columna ``importe``.
"""

import pandas as pd


def importe_por(df: pd.DataFrame, columna: str) -> pd.Series:
    """Devuelve el importe total por cada valor de ``columna``, de mayor a menor."""
    return df.groupby(columna)["importe"].sum().sort_values(ascending=False)


def cuota(df: pd.DataFrame, columna: str) -> pd.Series:
    """Devuelve el porcentaje del importe total que supone cada valor de ``columna``.

    De mayor a menor y redondeado a un decimal. La suma es 100, salvo redondeo.
    """
    totales = importe_por(df, columna)
    total_general = totales.sum()
    if total_general == 0:
        return (totales * 0.0).round(1)
    return ((totales / total_general) * 100).round(1)


def resumen_por_vendedor(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una fila por vendedor con las columnas ventas, unidades, importe y ticket_medio.

    - ``ventas``: número de ventas.
    - ``unidades``: unidades vendidas.
    - ``importe``: importe total.
    - ``ticket_medio``: importe medio por venta, redondeado a dos decimales.

    El índice es el vendedor y las filas van de mayor a menor importe.
    """
    agrupado = df.groupby("vendedor").agg(
        ventas=("importe", "count"),
        unidades=("unidades", "sum"),
        importe=("importe", "sum"),
        ticket_medio=("importe", "mean"),
    )
    agrupado["ticket_medio"] = agrupado["ticket_medio"].round(2)
    return agrupado.sort_values("importe", ascending=False)


def importe_mensual(df: pd.DataFrame) -> pd.Series:
    """Devuelve el importe total de cada mes. El índice es el mes como texto "AAAA-MM", en orden."""
    fechas = pd.to_datetime(df["fecha"])
    meses = fechas.dt.strftime("%Y-%m")
    return df.groupby(meses)["importe"].sum().sort_index()


def tabla_region_categoria(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una tabla con las regiones en filas, las categorías en columnas y el importe total.

    Las combinaciones sin ventas valen 0.
    """
    return pd.pivot_table(
        df,
        values="importe",
        index="region",
        columns="categoria",
        aggfunc="sum",
        fill_value=0,
    )


def producto_estrella(df: pd.DataFrame) -> pd.Series:
    """Devuelve, para cada categoría, el producto con más unidades vendidas.

    El índice es la categoría y el valor el nombre del producto.
    """
    totales_producto = (
        df.groupby(["categoria", "producto"], as_index=False)["unidades"]
        .sum()
        .sort_values("unidades", ascending=False)
    )
    estrella = totales_producto.drop_duplicates(subset=["categoria"], keep="first")
    return estrella.set_index("categoria")["producto"].sort_index()


def con_objetivos(resumen: pd.DataFrame, objetivos: pd.DataFrame) -> pd.DataFrame:
    """Añade a un resumen por vendedor su objetivo y si lo ha cumplido.

    ``resumen`` es el resultado de ``resumen_por_vendedor``. ``objetivos`` tiene
    las columnas vendedor y objetivo. El resultado conserva el orden y el índice
    de ``resumen`` y añade las columnas:

    - ``objetivo``: el objetivo del vendedor. Ausente si no tiene.
    - ``cumplimiento``: importe entre objetivo, en porcentaje con un decimal.
    - ``cumplido``: ``True`` si el importe alcanza el objetivo.
    """
    base = resumen.copy()
    indice_original = base.index.name or "vendedor"
    base_reset = base.reset_index().rename(columns={base.index.name or "index": "vendedor"})

    combinado = base_reset.merge(
        objetivos[["vendedor", "objetivo"]],
        on="vendedor",
        how="left",
    )
    combinado["cumplimiento"] = ((combinado["importe"] / combinado["objetivo"]) * 100).round(1)
    combinado["cumplido"] = combinado["importe"] >= combinado["objetivo"]

    resultado = combinado.set_index("vendedor")
    resultado.index.name = indice_original
    return resultado.reindex(base.index)
