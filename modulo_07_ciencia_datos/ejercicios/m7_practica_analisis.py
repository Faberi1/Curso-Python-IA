"""Módulo 7 - Práctica 7: análisis de las ventas del año.

Un pequeño proceso de análisis completo: cargar, limpiar, calcular indicadores,
generar gráficos y exportar los resultados.

Uso:

    python m7_practica_analisis.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATOS = Path(__file__).resolve().parent.parent / "datos"
SALIDA = Path(__file__).resolve().parent / "salida_practica_7"
COLUMNAS_TEXTO = ["vendedor", "region", "producto", "categoria"]


def cargar(ruta: str | Path) -> pd.DataFrame:
    """Lee el CSV de ventas con todas las columnas como texto."""
    return pd.read_csv(Path(ruta), dtype=str, keep_default_na=True, encoding="utf-8")


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve las ventas limpias y con las columnas calculadas.

    1. Texto sin espacios sobrantes y con la inicial en mayúscula.
    2. Sin filas duplicadas.
    3. ``fecha`` como fecha (formato "AAAA-MM-DD"), ``unidades`` y ``precio``
       como números. ``precio`` admite coma decimal.
    4. Las regiones ausentes pasan a ser "Sin región".
    5. Se descartan las filas sin fecha, vendedor, unidades o precio válidos, y
       las que tienen unidades o precio menores o iguales que cero.
    6. ``unidades`` queda como entero.
    7. Columnas nuevas: ``importe`` (unidades por precio) y ``mes`` ("AAAA-MM").
    8. Filas ordenadas por fecha, con el índice renumerado desde 0. A igual
       fecha se conserva el orden original.

    No modifica el DataFrame recibido.
    """
    limpio = df.copy()

    for col in COLUMNAS_TEXTO:
        if col in limpio.columns:
            limpio[col] = limpio[col].str.strip().str.capitalize()

    limpio = limpio.drop_duplicates(keep="first").copy()

    limpio["fecha"] = pd.to_datetime(
        limpio["fecha"].str.strip(),
        format="%Y-%m-%d",
        errors="coerce",
    )
    limpio["unidades"] = pd.to_numeric(limpio["unidades"].str.strip(), errors="coerce")
    precio_texto = limpio["precio"].str.strip().str.replace(",", ".", regex=False)
    limpio["precio"] = pd.to_numeric(precio_texto, errors="coerce")

    limpio["region"] = limpio["region"].fillna("Sin región")

    limpio = limpio.dropna(subset=["fecha", "vendedor", "unidades", "precio"])
    limpio = limpio[(limpio["unidades"] > 0) & (limpio["precio"] > 0)].copy()

    limpio["unidades"] = limpio["unidades"].astype(int)
    limpio["importe"] = limpio["unidades"] * limpio["precio"]
    limpio["mes"] = limpio["fecha"].dt.strftime("%Y-%m")

    limpio = limpio.sort_values("fecha", kind="mergesort").reset_index(drop=True)
    return limpio


def indicadores(df: pd.DataFrame) -> dict:
    """Devuelve los indicadores principales de unas ventas preparadas.

    Claves:

    - "ventas": número de ventas (int).
    - "importe_total": float con dos decimales.
    - "ticket_medio": importe medio por venta, float con dos decimales.
    - "mejor_vendedor": el de mayor importe total.
    - "mejor_mes": el mes "AAAA-MM" de mayor importe total.
    - "producto_mas_vendido": el de más unidades.
    """
    num_ventas = int(len(df))
    importe_total = round(float(df["importe"].sum()), 2) if num_ventas > 0 else 0.0
    ticket_medio = round(float(df["importe"].mean()), 2) if num_ventas > 0 else 0.0

    por_vendedor = df.groupby("vendedor")["importe"].sum()
    por_mes = df.groupby("mes")["importe"].sum()
    por_producto = df.groupby("producto")["unidades"].sum()

    return {
        "ventas": num_ventas,
        "importe_total": importe_total,
        "ticket_medio": ticket_medio,
        "mejor_vendedor": str(por_vendedor.idxmax()),
        "mejor_mes": str(por_mes.idxmax()),
        "producto_mas_vendido": str(por_producto.idxmax()),
    }


def ranking_vendedores(df: pd.DataFrame, objetivos: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una fila por vendedor, de mayor a menor importe.

    Columnas, en este orden: vendedor, ventas, importe, objetivo, cumplimiento
    y cumplido. ``importe`` va redondeado a dos decimales, ``cumplimiento`` es
    el porcentaje del objetivo alcanzado con un decimal y ``cumplido`` indica
    si el importe llega al objetivo. El índice va de 0 en adelante.

    ``objetivos`` tiene las columnas vendedor y objetivo.
    """
    agrupado = (
        df.groupby("vendedor", as_index=False)
        .agg(
            ventas=("importe", "count"),
            importe_raw=("importe", "sum"),
        )
    )
    combinado = agrupado.merge(objetivos[["vendedor", "objetivo"]], on="vendedor", how="left")
    combinado["importe"] = combinado["importe_raw"].round(2)
    combinado["cumplimiento"] = ((combinado["importe_raw"] / combinado["objetivo"]) * 100).round(1)
    combinado["cumplido"] = combinado["importe_raw"] >= combinado["objetivo"]
    combinado = combinado.sort_values("importe_raw", ascending=False, kind="mergesort")

    columnas = ["vendedor", "ventas", "importe", "objetivo", "cumplimiento", "cumplido"]
    return combinado[columnas].reset_index(drop=True)


def evolucion_mensual(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una fila por mes, en orden, con las columnas mes, importe y variacion.

    ``importe`` va redondeado a dos decimales. ``variacion`` es el cambio en
    porcentaje respecto al mes anterior, con un decimal; en el primer mes es
    un valor ausente. El índice va de 0 en adelante.
    """
    mensual = (
        df.groupby("mes", as_index=False)["importe"]
        .sum()
        .sort_values("mes", ascending=True, kind="mergesort")
        .reset_index(drop=True)
    )
    mensual["variacion"] = (mensual["importe"].pct_change() * 100).round(1)
    mensual["importe"] = mensual["importe"].round(2)
    return mensual[["mes", "importe", "variacion"]]


def generar_graficos(df: pd.DataFrame, carpeta: str | Path) -> list[Path]:
    """Guarda dos gráficos en ``carpeta`` y devuelve sus rutas, en este orden.

    1. ``importe_por_vendedor.png``: barras, de mayor a menor importe.
    2. ``evolucion_mensual.png``: líneas con el importe de cada mes.

    Crea la carpeta si no existe. Cada gráfico lleva título y etiqueta en el
    eje Y. Las figuras se cierran después de guardarlas.
    """
    destino = Path(carpeta)
    destino.mkdir(parents=True, exist_ok=True)

    por_vendedor = df.groupby("vendedor")["importe"].sum().sort_values(ascending=False)
    fig_barras, ax_barras = plt.subplots(figsize=(8, 4))
    ax_barras.bar(por_vendedor.index.astype(str), por_vendedor.values)
    ax_barras.set_title("Importe por vendedor")
    ax_barras.set_ylabel("Importe (€)")
    ax_barras.set_xlabel("Vendedor")
    ruta_barras = destino / "importe_por_vendedor.png"
    fig_barras.savefig(ruta_barras, dpi=150)
    plt.close(fig_barras)

    por_mes = df.groupby("mes")["importe"].sum().sort_index()
    fig_lineas, ax_lineas = plt.subplots(figsize=(8, 4))
    ax_lineas.plot(por_mes.index.astype(str), por_mes.values, marker="o")
    ax_lineas.set_title("Evolución mensual de ventas")
    ax_lineas.set_ylabel("Importe (€)")
    ax_lineas.set_xlabel("Mes")
    ax_lineas.grid(True)
    ruta_lineas = destino / "evolucion_mensual.png"
    fig_lineas.savefig(ruta_lineas, dpi=150)
    plt.close(fig_lineas)

    return [ruta_barras, ruta_lineas]


def exportar(tabla: pd.DataFrame, ruta: str | Path) -> None:
    """Escribe la tabla en un CSV en UTF-8, sin la columna del índice.

    Crea la carpeta de destino si no existe.
    """
    objetivo = Path(ruta)
    objetivo.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(objetivo, index=False, encoding="utf-8")


def main() -> None:
    """Ejecuta el análisis completo con los datos del módulo."""
    ventas = preparar(cargar(DATOS / "ventas_2026.csv"))
    objetivos = pd.read_csv(DATOS / "objetivos.csv")

    print("INDICADORES")
    for nombre, valor in indicadores(ventas).items():
        print(f"  {nombre:<22}{valor}")
    print()
    print("RANKING DE VENDEDORES")
    ranking = ranking_vendedores(ventas, objetivos)
    print(ranking.to_string(index=False))
    print()
    print("EVOLUCIÓN MENSUAL")
    print(evolucion_mensual(ventas).to_string(index=False))

    exportar(ranking, SALIDA / "ranking_vendedores.csv")
    exportar(evolucion_mensual(ventas), SALIDA / "evolucion_mensual.csv")
    for ruta in generar_graficos(ventas, SALIDA):
        print(f"Gráfico guardado en {ruta}")


if __name__ == "__main__":
    main()
