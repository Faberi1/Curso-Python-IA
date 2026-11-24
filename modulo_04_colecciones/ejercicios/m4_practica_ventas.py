"""Módulo 4 - Práctica 4: análisis de ventas en memoria.

Cada venta es un diccionario con las claves "fecha", "vendedor", "region",
"producto", "categoria", "unidades" y "precio". Ninguna función modifica la
lista de ventas que recibe.
"""

from m4_datos_ventas import VENTAS

ANCHO = 44


def importe(venta: dict) -> float:
    """Devuelve el importe de una venta: unidades por precio, con dos decimales.

    >>> importe({"unidades": 3, "precio": 19.9})
    59.7
    """
    return round(venta.get("unidades", 0) * venta.get("precio", 0.0), 2)


def total_ventas(ventas: list[dict]) -> float:
    """Devuelve la suma de los importes de todas las ventas, con dos decimales."""
    return round(sum(importe(venta) for venta in ventas), 2)


def filtrar_ventas(ventas: list[dict], *, region: str | None = None,
                   categoria: str | None = None, vendedor: str | None = None,
                   desde: str | None = None, hasta: str | None = None) -> list[dict]:
    """Devuelve las ventas que cumplen todos los criterios indicados.

    Un criterio que vale ``None`` no se aplica. ``desde`` y ``hasta`` son
    fechas ISO y las dos están incluidas en el intervalo.
    """
    resultado: list[dict] = []
    for venta in ventas:
        if region is not None and venta.get("region") != region:
            continue
        if categoria is not None and venta.get("categoria") != categoria:
            continue
        if vendedor is not None and venta.get("vendedor") != vendedor:
            continue
        fecha = venta.get("fecha")
        if desde is not None and fecha < desde:
            continue
        if hasta is not None and fecha > hasta:
            continue
        resultado.append(venta)
    return resultado
    # Las fechas ISO se pueden comparar como texto: su orden alfabético
    # coincide con el cronológico.


def importe_por(ventas: list[dict], campo: str) -> dict[str, float]:
    """Agrupa las ventas por ``campo`` y devuelve el importe total de cada grupo.

    Los importes van redondeados a dos decimales.

    >>> importe_por([{"region": "Norte", "unidades": 2, "precio": 10.0}], "region")
    {'Norte': 20.0}
    """
    acumulado:dict[str, float] = {}
    for venta in ventas:
        clave = venta.get(campo)
        acumulado[clave] = acumulado.get(clave, 0.0) + importe(venta)
    return {clave: round(total, 2) for clave, total in acumulado.items()}


def unidades_por_producto(ventas: list[dict]) -> dict[str, int]:
    """Devuelve las unidades totales vendidas de cada producto."""
    total_unidades: dict[str, int] = {}
    for venta in ventas:
        producto = venta.get("producto")
        total_unidades[producto] = total_unidades.get(producto, 0) + venta.get("unidades", 0)
    return total_unidades



def ranking(ventas: list[dict], campo: str, cantidad: int = 3) -> list[tuple[str, float]]:
    """Devuelve los ``cantidad`` grupos con mayor importe, como tuplas (clave, importe).

    De mayor a menor importe. A igual importe, por orden alfabético de la clave.
    """
    if cantidad <= 0:
        return []
    importes = importe_por(ventas, campo)
    ordenado = sorted(importes.items(), key=lambda x: (-x[1], x[0]))
    return ordenado[:cantidad]


def producto_mas_vendido(ventas: list[dict]) -> str | None:
    """Devuelve el producto con más unidades vendidas, o ``None`` si no hay ventas.

    En caso de empate, el primero por orden alfabético.
    """
    totales=unidades_por_producto(ventas)
    if not totales:
        return None 
    return min(totales, key=lambda p: (-totales[p], p))


def ticket_medio(ventas: list[dict]) -> float:
    """Devuelve el importe medio por venta, con dos decimales. Sin ventas, 0.0."""
    return round(total_ventas(ventas) / len(ventas), 2) if ventas else 0.0


def generar_informe(ventas: list[dict]) -> str:
    """Devuelve el informe de ventas como texto, con el formato del enunciado."""
    separador_doble = "=" * ANCHO
    separador_simple = "-" * ANCHO

    num_ventas = len(ventas)
    total = total_ventas(ventas)
    medio = ticket_medio(ventas)
    top_producto = producto_mas_vendido(ventas)
    texto_producto = top_producto if top_producto is not None else "-"

    lineas = [
        separador_doble,
        f"{'INFORME DE VENTAS':^{ANCHO}}",
        separador_doble,
        f"{'Ventas registradas':<30}{num_ventas:>14}",
        f"{'Importe total':<30}{total:>14,.2f}",
        f"{'Ticket medio':<30}{medio:>14,.2f}",
        f"{'Producto más vendido':<30}{texto_producto:>14}",
    ]

    secciones = [
        ("Por región", "region"),
        ("Por categoría", "categoria"),
        ("Por vendedor", "vendedor"),
    ]

    for titulo, campo in secciones:
        lineas.append(separador_simple)
        lineas.append(titulo)
        grupos = importe_por(ventas, campo)
        # Todos los grupos ordenados de mayor a menor importe y luego alfabéticamente
        grupos_ordenados = sorted(grupos.items(), key=lambda item: (-item[1], item[0]))
        for clave, valor in grupos_ordenados:
            lineas.append(f"  {clave:<28}{valor:>14,.2f}")

    lineas.append(separador_doble)
    return "\n".join(lineas)


def main():
    print(generar_informe(VENTAS))
    print()
    print("Solo la región Sur, segunda quincena:")
    print(generar_informe(filtrar_ventas(VENTAS, region="Sur", desde="2026-10-16")))


if __name__ == "__main__":
    print(generar_informe(VENTAS))
    print()
    print("Solo la región Sur, segunda quincena:")
    print(generar_informe(filtrar_ventas(VENTAS, region="Sur", desde="2026-10-16")))
    main()
