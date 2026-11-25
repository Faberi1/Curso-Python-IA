"""Módulo 5 - Ejercicio 6: dataclasses y composición.

En este ejercicio las clases se escriben enteras: no hay plantilla. El
enunciado está en ejercicios/README.md.
"""

from dataclasses import dataclass, field
import math

# TODO: escribe aquí las dataclasses Punto, LineaPedido y Pedido
@dataclass(frozen=True)
class Punto:
    """Punto en un plano 2D inmutable."""

    x: float = 0.0
    y: float = 0.0

    def distancia(self, otro: "Punto") -> float:
        """Distancia euclídea entre este punto y ``otro``, redondeada a dos decimales."""
        dx = self.x - otro.x
        dy = self.y - otro.y
        return round(math.hypot(dx, dy), 2)


@dataclass
class LineaPedido:
    """Línea de un pedido con validación de unidades positivas."""

    producto: str
    unidades: int
    precio: float

    def __post_init__(self) -> None:
        if self.unidades <= 0:
            raise ValueError("Las unidades deben ser un entero positivo.")

    @property
    def importe(self) -> float:
        """Importe de la línea: unidades por precio, redondeado a dos decimales."""
        return round(self.unidades * self.precio, 2)


@dataclass
class Pedido:
    """Pedido compuesto por varias líneas de pedido."""

    numero: int
    cliente: str
    lineas: list[LineaPedido] = field(default_factory=list)

    def anadir(self, producto: str, unidades: int, precio: float) -> LineaPedido:
        """Crea una línea de pedido, la añade al pedido y la devuelve."""
        linea = LineaPedido(producto=producto, unidades=unidades, precio=precio)
        self.lineas.append(linea)
        return linea

    @property
    def total(self) -> float:
        """Suma de los importes de todas las líneas, redondeada a dos decimales."""
        return round(sum(linea.importe for linea in self.lineas), 2)

    def __len__(self) -> int:
        """Devuelve el número de líneas del pedido."""
        return len(self.lineas)

    def productos(self) -> list[str]:
        """Devuelve los nombres de los productos sin repetir y en orden alfabético."""
        return sorted({linea.producto for linea in self.lineas})