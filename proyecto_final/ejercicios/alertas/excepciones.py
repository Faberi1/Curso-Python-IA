"""Excepciones del gestor de alertas de seguridad.

Jerarquía definida:

    ErrorDeIncidencias (Exception)      base de todos los errores de la aplicación
    ├── DatosNoValidos                  un dato de una alerta no es válido
    ├── IncidenciaNoEncontrada          no existe una alerta con ese identificador
    ├── TransicionNoValida              el cambio de estado no está permitido
    └── ErrorDeAlmacen                  el fichero de datos no se puede leer o escribir
"""


class ErrorDeIncidencias(Exception):
    """Error base para cualquier fallo de dominio o persistencia."""


class DatosNoValidos(ErrorDeIncidencias):
    """Se lanza cuando un campo o dato de una alerta no cumple las reglas."""


class IncidenciaNoEncontrada(ErrorDeIncidencias):
    """Se lanza cuando se consulta o modifica un identificador inexistente."""

    def __init__(self, identificador: int) -> None:
        self.identificador = identificador
        super().__init__(f"No existe la alerta {identificador}")


class TransicionNoValida(ErrorDeIncidencias):
    """Se lanza cuando no se permite pasar de un estado a otro."""

    def __init__(self, actual: str, nuevo: str) -> None:
        self.actual = actual
        self.nuevo = nuevo
        super().__init__(f"No se puede pasar de {actual} a {nuevo}")


class ErrorDeAlmacen(ErrorDeIncidencias):
    """Se lanza cuando ocurre un error al leer o guardar el almacén de datos."""