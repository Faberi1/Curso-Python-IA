"""Operaciones sobre el conjunto de alertas de seguridad."""

from datetime import date

from .excepciones import DatosNoValidos, IncidenciaNoEncontrada
from .modelos import PRIORIDADES, Alerta


class GestorIncidencias:
    """Contiene las alertas y ofrece las operaciones del dominio.

    Usa composición: guarda las alertas en un diccionario interno por
    identificador. No lee ni escribe ficheros y no usa ``print`` ni ``input``.
    """

    def __init__(self, incidencias: list[Alerta] | None = None) -> None:
        """Crea el gestor, vacío o con las alertas recibidas."""
        self._alertas: dict[int, Alerta] = {}
        if incidencias:
            for alerta in incidencias:
                if not isinstance(alerta, Alerta):
                    raise DatosNoValidos("Todos los elementos deben ser instancias de Alerta")
                if alerta.id in self._alertas:
                    raise DatosNoValidos(f"Identificador duplicado: {alerta.id}")
                self._alertas[alerta.id] = alerta

    def __len__(self) -> int:
        """Devuelve el número de alertas gestionadas."""
        return len(self._alertas)

    def __iter__(self):
        """Recorre las alertas ordenadas por identificador."""
        for alerta_id in sorted(self._alertas):
            yield self._alertas[alerta_id]

    def crear(
        self,
        titulo: str,
        solicitante: str,
        prioridad: str = "media",
        hoy: date | None = None,
    ) -> Alerta:
        """Da de alta una alerta y la devuelve.

        ``solicitante`` corresponde al campo ``origen`` de la alerta.
        El identificador es el mayor existente más uno, o 1 si no hay ninguna.
        """
        fecha_deteccion = hoy if hoy is not None else date.today()
        siguiente_id = max(self._alertas, default=0) + 1

        nueva = Alerta(
            id=siguiente_id,
            titulo=titulo,
            origen=solicitante,
            fecha_deteccion=fecha_deteccion,
            prioridad=prioridad,
        )
        self._alertas[nueva.id] = nueva
        return nueva

    def obtener(self, identificador: int) -> Alerta:
        """Devuelve la alerta con ese identificador o lanza ``IncidenciaNoEncontrada``."""
        if identificador not in self._alertas:
            raise IncidenciaNoEncontrada(identificador)
        return self._alertas[identificador]

    def cambiar_estado(
        self,
        identificador: int,
        nuevo: str,
        hoy: date | None = None,
    ) -> Alerta:
        """Cambia el estado de una alerta delegando en ``Alerta.cambiar_estado``."""
        alerta = self.obtener(identificador)
        fecha_referencia = hoy if hoy is not None else date.today()
        alerta.cambiar_estado(nuevo, fecha_referencia)
        return alerta

    def asignar(self, identificador: int, tecnico: str) -> Alerta:
        """Asigna la alerta a un analista y la devuelve.

        Limpia espacios alrededor del nombre. Si estaba ``abierta``, pasa a
        ``en_curso`` usando la fecha actual si no se pasa otra.
        """
        alerta = self.obtener(identificador)
        nombre_limpio = tecnico.strip()
        if not nombre_limpio:
            raise DatosNoValidos("El nombre del técnico es obligatorio")

        alerta.asignada_a = nombre_limpio
        if alerta.estado == "abierta":
            alerta.cambiar_estado("en_curso", date.today())
        return alerta

    def filtrar(
        self,
        *,
        estado: str | None = None,
        prioridad: str | None = None,
        asignada_a: str | None = None,
        texto: str | None = None,
    ) -> list[Alerta]:
        """Devuelve las alertas que cumplen todos los criterios indicados."""
        resultado: list[Alerta] = []
        texto_buscado = texto.strip().lower() if texto is not None else None
        tecnico_buscado = asignada_a.strip().lower() if asignada_a is not None else None

        for alerta in self:
            if estado is not None and alerta.estado != estado:
                continue
            if prioridad is not None and alerta.prioridad != prioridad:
                continue
            if tecnico_buscado is not None and alerta.asignada_a.lower() != tecnico_buscado:
                continue
            if texto_buscado is not None:
                en_titulo = texto_buscado in alerta.titulo.lower()
                en_origen = texto_buscado in alerta.origen.lower()
                if not (en_titulo or en_origen):
                    continue
            resultado.append(alerta)

        return resultado

    def pendientes(self) -> list[Alerta]:
        """Devuelve las alertas pendientes ordenadas por prioridad, antigüedad e id."""
        peso_prioridad = {
            prioridad: -indice for indice, prioridad in enumerate(PRIORIDADES)
        }
        pendientes_lista = [alerta for alerta in self if alerta.pendiente]
        pendientes_lista.sort(
            key=lambda a: (
                peso_prioridad[a.prioridad],
                a.fecha_deteccion,
                a.id,
            )
        )
        return pendientes_lista

    def contar_por(self, campo: str) -> dict[str, int]:
        """Cuenta las alertas por el valor de un atributo existente."""
        conteo: dict[str, int] = {}
        for alerta in self:
            if not hasattr(alerta, campo):
                raise DatosNoValidos(f"Campo no válido para agrupar: {campo}")
            valor = getattr(alerta, campo)
            if valor == "":
                continue
            clave = str(valor)
            conteo[clave] = conteo.get(clave, 0) + 1
        return conteo