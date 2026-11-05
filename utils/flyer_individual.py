import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

import requests

from config.settings import (
    FLYERS_INDIVIDUALES_DIR,
    CUSTOM_FLYERS_DIRECTORY_FILE
)

from utils.monday import (
    obtener_items_listing_flyer
)


# ============================================================
# DIRECTORIO PERSONALIZADO OPCIONAL
# ============================================================

def obtener_directorio_personalizado():

    if not CUSTOM_FLYERS_DIRECTORY_FILE.exists():

        return None

    lineas = (
        CUSTOM_FLYERS_DIRECTORY_FILE
        .read_text(
            encoding="utf-8"
        )
        .splitlines()
    )

    for linea in lineas:

        linea = linea.strip()

        if not linea:

            continue

        if linea.startswith("#"):

            continue

        directorio = Path(
            linea
        )

        directorio.mkdir(
            parents=True,
            exist_ok=True
        )

        return directorio

    return None


# ============================================================
# LIMPIAR NOMBRE DE ARCHIVO
# ============================================================

def limpiar_nombre_archivo(
    texto
):

    texto = (
        str(
            texto
            or ""
        )
        .strip()
    )

    texto = re.sub(
        r'[\\/:*?"<>|]+',
        " - ",
        texto
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    texto = (
        texto
        .strip()
        .rstrip(".")
    )

    if not texto:

        texto = (
            "property_sin_nombre"
        )

    return texto


# ============================================================
# OBTENER EXTENSIÓN
# ============================================================

def obtener_extension_archivo(
    archivo
):

    asset = (
        archivo.get(
            "asset"
        )
        or {}
    )

    extension = (
        str(
            asset.get(
                "file_extension",
                ""
            )
            or ""
        )
        .strip()
        .lower()
        .lstrip(".")
    )

    if extension:

        return extension

    nombre = (
        str(
            archivo.get(
                "name",
                ""
            )
            or ""
        )
        .strip()
    )

    suffix = (
        Path(
            nombre
        )
        .suffix
        .lower()
        .lstrip(".")
    )

    if suffix:

        return suffix

    url = (
        str(
            asset.get(
                "public_url",
                ""
            )
            or archivo.get(
                "url",
                ""
            )
            or ""
        )
        .strip()
    )

    suffix_url = (
        Path(
            urlparse(
                url
            ).path
        )
        .suffix
        .lower()
        .lstrip(".")
    )

    return (
        suffix_url
        or "png"
    )


# ============================================================
# OBTENER PHASE
# ============================================================

def obtener_phase_item(
    item,
    phase_column_id
):

    column_values = (
        item.get(
            "column_values",
            []
        )
        or []
    )

    for valor in column_values:

        if (
            str(
                valor.get(
                    "id",
                    ""
                )
            )
            == str(
                phase_column_id
            )
        ):

            return (
                str(
                    valor.get(
                        "text",
                        ""
                    )
                    or ""
                )
                .strip()
            )

    return ""


# ============================================================
# EXTRAER ARCHIVO DE LISTING FLYER
# ============================================================

def obtener_archivo_listing_flyer(
    item,
    column_id
):

    column_values = (
        item.get(
            "column_values",
            []
        )
        or []
    )

    for valor in column_values:

        if (
            str(
                valor.get(
                    "id",
                    ""
                )
            )
            != str(
                column_id
            )
        ):

            continue

        archivos = (
            valor.get(
                "files"
            )
            or []
        )

        # ----------------------------------------------------
        # PRIMERO BUSCAR UNA IMAGEN REAL
        # ----------------------------------------------------

        for archivo in archivos:

            if (
                archivo.get(
                    "is_image"
                )
                is True
            ):

                return archivo

        # ----------------------------------------------------
        # FALLBACK
        # ----------------------------------------------------

        if archivos:

            return (
                archivos[0]
            )

    return None


# ============================================================
# URL DEL ARCHIVO
# ============================================================

def obtener_url_archivo(
    archivo
):

    asset = (
        archivo.get(
            "asset"
        )
        or {}
    )

    return (
        str(
            asset.get(
                "public_url",
                ""
            )
            or asset.get(
                "url",
                ""
            )
            or archivo.get(
                "url",
                ""
            )
            or ""
        )
        .strip()
    )


# ============================================================
# RUTA DISPONIBLE
# ============================================================

def obtener_ruta_disponible(
    directorio,
    nombre_base,
    extension
):

    ruta = (
        directorio
        /
        f"{nombre_base}.{extension}"
    )

    if not ruta.exists():

        return ruta

    numero = 2

    while True:

        ruta = (
            directorio
            /
            f"{nombre_base} ({numero}).{extension}"
        )

        if not ruta.exists():

            return ruta

        numero += 1


# ============================================================
# DESCARGAR ARCHIVO
# ============================================================

def descargar_archivo(
    url,
    ruta_destino
):

    response = requests.get(
        url,
        timeout=60
    )

    response.raise_for_status()

    ruta_destino.write_bytes(
        response.content
    )


# ============================================================
# LIMPIAR FLYERS INDIVIDUALES ANTERIORES
# ============================================================

def limpiar_flyers_individuales():

    FLYERS_INDIVIDUALES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    eliminados = 0

    for archivo in (
        FLYERS_INDIVIDUALES_DIR
        .iterdir()
    ):

        if not archivo.is_file():

            continue

        try:

            archivo.unlink()

            eliminados += 1

        except Exception as error:

            print(
                f"No se pudo eliminar "
                f"{archivo.name}: "
                f"{error}"
            )

    return eliminados


# ============================================================
# DESCARGAR FLYERS INDIVIDUALES
# ============================================================

def descargar_flyers_individuales():

    print("\n" + "=" * 100)
    print("FLYERS INDIVIDUALES")
    print("=" * 100)

    eliminados = (
        limpiar_flyers_individuales()
    )

    if eliminados > 0:

        print(
            f"\nFlyers individuales anteriores "
            f"eliminados: {eliminados}"
        )

    items, column_id, phase_column_id = (
        obtener_items_listing_flyer()
    )

    # ========================================================
    # SOLO PROPIEDADES CURRENT
    # ========================================================

    items = [
        item
        for item in items
        if (
            obtener_phase_item(
                item,
                phase_column_id
            )
            .strip()
            .lower()
            == "current"
        )
    ]

    directorio_personalizado = (
        obtener_directorio_personalizado()
    )

    directorio_personalizado_individual = None

    if directorio_personalizado is not None:

        directorio_personalizado_individual = (
            directorio_personalizado
            /
            "flyers_individuales"
        )

        directorio_personalizado_individual.mkdir(
            parents=True,
            exist_ok=True
        )

    descargados = []
    sin_flyer = []
    errores = []

    for item in items:

        property_name = (
            str(
                item.get(
                    "name",
                    ""
                )
                or ""
            )
            .strip()
        )

        archivo = (
            obtener_archivo_listing_flyer(
                item,
                column_id
            )
        )

        if archivo is None:

            sin_flyer.append(
                property_name
            )

            continue

        url = (
            obtener_url_archivo(
                archivo
            )
        )

        if not url:

            sin_flyer.append(
                property_name
            )

            continue

        extension = (
            obtener_extension_archivo(
                archivo
            )
        )

        nombre_base = (
            limpiar_nombre_archivo(
                property_name
            )
        )

        ruta_destino = (
            obtener_ruta_disponible(
                FLYERS_INDIVIDUALES_DIR,
                nombre_base,
                extension
            )
        )

        try:

            descargar_archivo(
                url,
                ruta_destino
            )

            descargados.append(
                ruta_destino
            )

            if (
                directorio_personalizado_individual
                is not None
            ):

                ruta_personalizada = (
                    directorio_personalizado_individual
                    /
                    ruta_destino.name
                )

                shutil.copy2(
                    ruta_destino,
                    ruta_personalizada
                )

        except Exception as error:

            errores.append(
                (
                    property_name,
                    str(error)
                )
            )

    # ========================================================
    # RESULTADO
    # ========================================================

    print("\n" + "=" * 100)
    print("RESULTADO FLYERS INDIVIDUALES")
    print("=" * 100)

    print(
        f"\nProperties revisadas: "
        f"{len(items)}"
    )

    print(
        f"Flyers individuales descargados: "
        f"{len(descargados)}"
    )

    print(
        f"Properties sin Listing Flyer: "
        f"{len(sin_flyer)}"
    )

    if sin_flyer:

        print(
            "\nProperties sin Listing Flyer:\n"
        )

        for property_name in sin_flyer:

            print(
                f"- {property_name}"
            )

    if errores:

        print(
            f"\nErrores de descarga: "
            f"{len(errores)}"
        )

        for property_name, error in errores:

            print(
                f"- {property_name}"
            )

            print(
                f"  Error: {error}"
            )

    print(
        f"\nCarpeta local: "
        f"{FLYERS_INDIVIDUALES_DIR}"
    )

    if (
        directorio_personalizado_individual
        is not None
    ):

        print(
            f"Carpeta personalizada: "
            f"{directorio_personalizado_individual}"
        )

    return descargados
