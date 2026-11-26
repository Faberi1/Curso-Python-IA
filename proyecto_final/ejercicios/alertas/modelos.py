"""Modelo de dominio: la alerta de seguridad y sus reglas."""

from dataclasses import dataclass
from datetime import date

from .excepciones import DatosNoValidos, TransicionNoValida

ESTADOS = ("abierta", "en_curso", "resuelta", "cerrada")
PRIORIDADES = ("baja", "media", "alta", "critica")

# Desde cada estado, a cuáles se puede pasar
TRANSICIONES: dict[str, tuple[str, ...]] = {
    "abierta": ("en_curso", "cerrada"),
    "en_curso": ("abierta", "resuelta"),
    "resuelta": ("en_curso", "cerrada"),
    "cerrada": (),
}

CAMPOS = [
    "id",
    "titulo",
    "origen",
    "fecha_deteccion",
    "prioridad",
    "estado",
    "asignada_a",
    "fecha_cierre",
]


@dataclass
class Alerta:
    """Una alerta o incidente detectado en el entorno de seguridad.

    Campos en orden:
    - id: identificador entero positivo
    - titulo: descripción breve de la alerta (obligatorio)
    - origen: IP, host, sensor o usuario afectado/origen (obligatorio)
    - fecha_deteccion: fecha en que se registró la alerta
    - prioridad: 'baja', 'media', 'alta' o 'critica' (por defecto 'media')
    - estado: 'abierta', 'en_curso', 'resuelta' o 'cerrada' (por defecto 'abierta')
    - asignada_a: analista responsable o cadena vacía
    - fecha_cierre: fecha de cierre si está cerrada, o None en caso contrario
    """

    id: int
    titulo: str
    origen: str
    fecha_deteccion: date
    prioridad: str = "media"
    estado: str = "abierta"
    asignada_a: str = ""
    fecha_cierre: date | None = None

    def __post_init__(self) -> None:
        """Limpia espacios y valida que todos los datos sean correctos."""
        if not isinstance(self.id, int) or isinstance(self.id, bool) or self.id < 1:
            raise DatosNoValidos("El identificador debe ser un entero positivo")

        self.titulo = self.titulo.strip()
        self.origen = self.origen.strip()
        self.asignada_a = self.asignada_a.strip()

        if not self.titulo:
            raise DatosNoValidos("El título es obligatorio")
        if not self.origen:
            raise DatosNoValidos("El origen es obligatorio")
        if self.prioridad not in PRIORIDADES:
            raise DatosNoValidos(f"Prioridad no válida: {self.prioridad}")
        if self.estado not in ESTADOS:
            raise DatosNoValidos(f"Estado no válido: {self.estado}")

        if not isinstance(self.fecha_deteccion, date):
            raise DatosNoValidos("La fecha de detección debe ser una fecha válida")

        if self.fecha_cierre is not None and not isinstance(self.fecha_cierre, date):
            raise DatosNoValidos("La fecha de cierre debe ser una fecha válida o None")

        if self.fecha_cierre is not None and self.fecha_cierre < self.fecha_deteccion:
            raise DatosNoValidos("La fecha de cierre no puede ser anterior a la detección")

    @property
    def pendiente(self) -> bool:
        """Indica si la alerta está abierta o en curso."""
        return self.estado in ("abierta", "en_curso")

    def cambiar_estado(self, nuevo: str, hoy: date) -> None:
        """Cambia al estado ``nuevo`` respetando ``TRANSICIONES``."""
        if nuevo not in ESTADOS:
            raise DatosNoValidos(f"Estado no válido: {nuevo}")

        permitidos = TRANSICIONES[self.estado]
        if nuevo not in permitidos:
            raise TransicionNoValida(self.estado, nuevo)

        self.estado = nuevo
        if nuevo == "cerrada":
            self.fecha_cierre = hoy

    def dias_abierta(self, hoy: date) -> int:
        """Días transcurridos desde la detección hasta el cierre o hasta ``hoy``."""
        fecha_fin = self.fecha_cierre if self.fecha_cierre is not None else hoy
        dias = (fecha_fin - self.fecha_deteccion).days
        return max(0, dias)

    def a_fila(self) -> dict[str, str]:
        """Convierte la alerta en un diccionario de cadenas con las claves de ``CAMPOS``."""
        return {
            "id": str(self.id),
            "titulo": self.titulo,
            "origen": self.origen,
            "fecha_deteccion": self.fecha_deteccion.isoformat(),
            "prioridad": self.prioridad,
            "estado": self.estado,
            "asignada_a": self.asignada_a,
            "fecha_cierre": self.fecha_cierre.isoformat() if self.fecha_cierre else "",
        }

    @classmethod
    def desde_fila(cls, fila: dict[str, str]) -> "Alerta":
        """Reconstruye una ``Alerta`` desde un diccionario de cadenas (como ``csv.DictReader``)."""
        faltantes = [campo for campo in CAMPOS if campo not in fila]
        if faltantes:
            raise DatosNoValidos(f"Faltan campos obligatorios: {', '.join(faltantes)}")

        try:
            id_valor = int(fila["id"].strip())
        except (ValueError, AttributeError) as exc:
            raise DatosNoValidos(f"Identificador no válido: {fila.get('id')!r}") from exc

        try:
            fecha_deteccion = date.fromisoformat(fila["fecha_deteccion"].strip())
        except (ValueError, AttributeError) as exc:
            raise DatosNoValidos(
                f"Fecha de detección no válida: {fila.get('fecha_deteccion')!r}"
            ) from exc

        fecha_cierre_raw = (fila["fecha_cierre"] or "").strip()
        fecha_cierre: date | None = None
        if fecha_cierre_raw:
            try:
                fecha_cierre = date.fromisoformat(fecha_cierre_raw)
            except ValueError as exc:
                raise DatosNoValidos(
                    f"Fecha de cierre no válida: {fecha_cierre_raw!r}"
                ) from exc

        return cls(
            id=id_valor,
            titulo=fila["titulo"] or "",
            origen=fila["origen"] or "",
            fecha_deteccion=fecha_deteccion,
            prioridad=(fila["prioridad"] or "").strip(),
            estado=(fila["estado"] or "").strip(),
            asignada_a=fila["asignada_a"] or "",
            fecha_cierre=fecha_cierre,
        )