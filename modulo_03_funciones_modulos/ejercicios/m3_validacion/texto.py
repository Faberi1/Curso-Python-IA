"""Validación y normalización de textos."""

LETRAS_DNI = "TRWAGMYFPDXBNJZSQVHLCKE"


def esta_vacio(texto: str | None) -> bool:
    """Indica si el texto es ``None``, está vacío o solo contiene espacios.

    >>> esta_vacio("   ")
    True
    >>> esta_vacio(" a ")
    False
    """
    if texto is None:
        return True
    return texto.strip() == ""


def normalizar_nombre(nombre: str) -> str:
    """Quita los espacios sobrantes y pone en mayúscula la inicial de cada palabra.

    >>> normalizar_nombre("  ada   LOVELACE ")
    'Ada Lovelace'
    """
    palabras=nombre.strip().split()
    return " ".join(palabra.capitalize() for palabra in palabras)


def es_email(texto: str) -> bool:
    """Comprueba de forma sencilla que el texto tiene forma de correo.

    Reglas: no contiene espacios, tiene exactamente una arroba, hay texto
    antes de la arroba, y el dominio contiene al menos un punto que no está
    ni al principio ni al final.

    >>> es_email("ada@ejemplo.com")
    True
    >>> es_email("ada@ejemplo")
    False
    """
    if not texto or any(caracter.isspace() for caracter in texto):
        return False

    if texto.count("@") != 1:
        return False

    usuario, dominio = texto.split("@")
    if not usuario or not dominio:
        return False

    if "." not in dominio:
        return False

    if dominio.startswith(".") or dominio.endswith("."):
        return False

    return True


def es_dni(texto: str) -> bool:
    """Comprueba que el texto es un DNI válido: ocho dígitos y la letra correcta.

    La letra se obtiene tomando el resto de dividir el número entre 23 y
    usándolo como posición en ``LETRAS_DNI``. Admite la letra en minúscula y
    espacios alrededor.

    >>> es_dni("12345678Z")
    True
    >>> es_dni("12345678A")
    False
    """
    limpio = texto.strip().upper()
    if len(limpio) != 9:
        return False
    numero, letra = limpio[:8], limpio[8]
    if not numero.isdigit():
        return False
    indice = int(numero) % 23
    letra_correcta = LETRAS_DNI[indice]
    return letra == letra_correcta
