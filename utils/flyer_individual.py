import hashlib
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

import requests

from config.settings import (
    FLYERS_INDIVIDUALES_DIR,
    CUSTOM_FLYERS_DIRECTORY_FILE,
    CACHE_FLYERS_INDIVIDUALES_DIR,
    CACHE_FLYERS_INDIVIDUALES_MANIFEST_FILE
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
# IDENTIDAD ESTABLE DEL ARCHIVO DE MONDAY
# ============================================================
#
# public_url puede cambiar / expirar.
# Por eso el cache se valida principalmente con asset_id.
#
# ============================================================

def obtener_asset_key(
    archivo
):

    asset = (
        archivo.get(
            "asset"
        )
        or {}
    )

    candidatos = [
        archivo.get(
            "asset_id"
        ),
        asset.get(
            "id"
        ),
        archivo.get(
            "file_id"
        )
    ]

    for candidato in candidatos:

        valor = (
            str(
                candidato
                or ""
            )
            .strip()
        )

        if valor:

            return valor

    # Fallback estable si Monday no devuelve ID.
    texto = (
        str(
            archivo.get(
                "name",
                ""
            )
            or ""
        )
        + "|"
        + str(
            asset.get(
                "file_size",
                ""
            )
            or ""
        )
    )

    return (
        hashlib.sha256(
            texto.encode(
                "utf-8"
            )
        )
        .hexdigest()
    )


# ============================================================
# CONSOLIDACIÓN PORT EWEN / BROADWAY
# ============================================================
#
# Regla acordada:
#
# 186 Broadway + 188 Broadway -> un solo flyer:
#     186 Broadway-Unit, Port Ewen, NY 12466
#
# 190 Broadway -> un solo flyer:
#     190 Broadway-Unit, Port Ewen, NY 12466
#
# Por lo tanto, aunque existan 12 unidades Current,
# se generan como máximo 2 flyers individuales.
#
# ============================================================

def obtener_clave_y_nombre_consolidado(
    property_name,
    item_id=""
):

    texto = (
        str(
            property_name
            or ""
        )
        .strip()
    )

    texto_normalizado = (
        texto.lower()
    )

    es_port_ewen = (
        "port ewen"
        in texto_normalizado
    )

    if es_port_ewen:

        match = re.search(
            r"\b(186|188|190)\s+broadway\b",
            texto_normalizado,
            flags=re.IGNORECASE
        )

        if match:

            numero = (
                match.group(
                    1
                )
            )

            if numero in {
                "186",
                "188"
            }:

                return (
                    "port_ewen_broadway_186_188",
                    "186 Broadway-Unit, Port Ewen, NY 12466"
                )

            if numero == "190":

                return (
                    "port_ewen_broadway_190",
                    "190 Broadway-Unit, Port Ewen, NY 12466"
                )

    # --------------------------------------------------------
    # RESTO DE PROPIEDADES:
    # una propiedad Current = un flyer individual
    # --------------------------------------------------------

    clave_base = (
        texto.lower()
    )

    clave_base = re.sub(
        r"\s+",
        " ",
        clave_base
    ).strip()

    if not clave_base:

        clave_base = (
            f"item_{item_id}"
        )

    return (
        f"property::{clave_base}",
        texto
    )


# ============================================================
# CONSOLIDAR ITEMS CURRENT
# ============================================================

def consolidar_items_current(
    items,
    listing_flyer_column_id
):

    grupos = {}

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

        item_id = (
            str(
                item.get(
                    "id",
                    ""
                )
                or ""
            )
            .strip()
        )

        clave, nombre_salida = (
            obtener_clave_y_nombre_consolidado(
                property_name,
                item_id
            )
        )

        archivo = (
            obtener_archivo_listing_flyer(
                item,
                listing_flyer_column_id
            )
        )

        if clave not in grupos:

            grupos[
                clave
            ] = {
                "key":
                    clave,
                "output_property":
                    nombre_salida,
                "source_properties":
                    [],
                "archivo":
                    None,
                "source_property":
                    None
            }

        grupos[
            clave
        ][
            "source_properties"
        ].append(
            property_name
        )

        # ----------------------------------------------------
        # Para un grupo consolidado basta con que al menos
        # una de sus unidades tenga Listing Flyer.
        # ----------------------------------------------------

        if (
            grupos[
                clave
            ][
                "archivo"
            ]
            is None
            and archivo
            is not None
        ):

            grupos[
                clave
            ][
                "archivo"
            ] = archivo

            grupos[
                clave
            ][
                "source_property"
            ] = property_name

    return list(
        grupos.values()
    )


# ============================================================
# CACHE MANIFEST
# ============================================================

def cargar_manifest_cache():

    if not (
        CACHE_FLYERS_INDIVIDUALES_MANIFEST_FILE
        .exists()
    ):

        return {}

    try:

        with (
            CACHE_FLYERS_INDIVIDUALES_MANIFEST_FILE
            .open(
                "r",
                encoding="utf-8"
            )
        ) as archivo:

            datos = (
                json.load(
                    archivo
                )
            )

        if isinstance(
            datos,
            dict
        ):

            return datos

    except Exception:

        pass

    return {}


def guardar_manifest_cache(
    manifest
):

    CACHE_FLYERS_INDIVIDUALES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    CACHE_FLYERS_INDIVIDUALES_MANIFEST_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with (
        CACHE_FLYERS_INDIVIDUALES_MANIFEST_FILE
        .open(
            "w",
            encoding="utf-8"
        )
    ) as archivo:

        json.dump(
            manifest,
            archivo,
            indent=4,
            ensure_ascii=False
        )


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
# LIMPIAR CARPETA DE SALIDA
# ============================================================

def limpiar_directorio_archivos(
    directorio
):

    directorio.mkdir(
        parents=True,
        exist_ok=True
    )

    eliminados = 0

    for archivo in (
        directorio.iterdir()
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
# RUTA DE CACHE
# ============================================================

def obtener_ruta_cache(
    asset_key,
    extension
):

    nombre_seguro = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        str(
            asset_key
        )
    )

    return (
        CACHE_FLYERS_INDIVIDUALES_DIR
        /
        f"{nombre_seguro}.{extension}"
    )

# def validar_flyers_requeridos(
#     registros
# ):

#     faltantes = []

#     for registro in registros:

#         archivo = (
#             registro.get(
#                 "archivo"
#             )
#         )

#         if archivo is None:

#             faltantes.append(
#                 registro[
#                     "output_property"
#                 ]
#             )

#             continue

#         url = (
#             obtener_url_archivo(
#                 archivo
#             )
#         )

#         if not url:

#             faltantes.append(
#                 registro[
#                     "output_property"
#                 ]
#             )

#     if not faltantes:

#         return

#     print("\n" + "=" * 100)
#     print("ERROR - FALTAN FLYERS INDIVIDUALES")
#     print("=" * 100)

#     print(
#         f"\nFaltan {len(faltantes)} "
#         f"flyer(s) individual(es) "
#         f"para propiedades Current."
#     )

#     print(
#         "\nActualice la columna "
#         "'Listing Flyer' en Monday "
#         "antes de continuar:\n"
#     )

#     for property_name in faltantes:

#         print(
#             f"- {property_name}"
#         )

#     print(
#         "\n[MODO PRUEBA] "
#         "El programa continuará."
#     )

#     return

#     # raise SystemExit(
#     #     1
#     # )


# ============================================================
# VALIDAR QUE TODOS LOS CURRENT TENGAN FLYER
# ============================================================

def validar_flyers_requeridos(
    registros
):

    faltantes = []

    for registro in registros:

        archivo = (
            registro.get(
                "archivo"
            )
        )

        if archivo is None:

            faltantes.append(
                registro[
                    "output_property"
                ]
            )

            continue

        url = (
            obtener_url_archivo(
                archivo
            )
        )

        if not url:

            faltantes.append(
                registro[
                    "output_property"
                ]
            )

    if not faltantes:

        return

    print("\n" + "=" * 100)
    print("ERROR - FALTAN FLYERS INDIVIDUALES")
    print("=" * 100)

    print(
        f"\nFaltan {len(faltantes)} "
        f"flyer(s) individual(es) "
        f"para propiedades Current."
    )

    print(
        "\nActualice la columna "
        "'Listing Flyer' en Monday "
        "antes de continuar:\n"
    )

    for property_name in faltantes:

        print(
            f"- {property_name}"
        )

    print(
        "\n[ERROR] El programa se detuvo. "
        "No se modificaron las carpetas de salida."
    )

    raise SystemExit(
        1
    )


# ============================================================
# SINCRONIZAR CACHE
# ============================================================

def preparar_cache_current(
    registros
):

    CACHE_FLYERS_INDIVIDUALES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    manifest_anterior = (
        cargar_manifest_cache()
    )

    manifest_nuevo = {}

    cache_reutilizado = 0
    descargados = 0
    actualizados = 0

    for registro in registros:

        clave = (
            registro[
                "key"
            ]
        )

        archivo = (
            registro[
                "archivo"
            ]
        )

        extension = (
            obtener_extension_archivo(
                archivo
            )
        )

        asset_key = (
            obtener_asset_key(
                archivo
            )
        )

        url = (
            obtener_url_archivo(
                archivo
            )
        )

        ruta_cache = (
            obtener_ruta_cache(
                asset_key,
                extension
            )
        )

        anterior = (
            manifest_anterior.get(
                clave
            )
            or {}
        )

        mismo_asset = (
            str(
                anterior.get(
                    "asset_key",
                    ""
                )
            )
            == str(
                asset_key
            )
        )

        archivo_cache_anterior = (
            anterior.get(
                "cache_file"
            )
        )

        ruta_cache_anterior = None

        if archivo_cache_anterior:

            ruta_cache_anterior = (
                CACHE_FLYERS_INDIVIDUALES_DIR
                /
                archivo_cache_anterior
            )

        # ----------------------------------------------------
        # REUTILIZAR CACHE
        # ----------------------------------------------------

        if (
            mismo_asset
            and ruta_cache_anterior
            is not None
            and ruta_cache_anterior.exists()
        ):

            ruta_cache = (
                ruta_cache_anterior
            )

            cache_reutilizado += 1

        else:

            # ------------------------------------------------
            # DESCARGAR NUEVO / ACTUALIZADO
            # ------------------------------------------------

            descargar_archivo(
                url,
                ruta_cache
            )

            if anterior:

                actualizados += 1

            else:

                descargados += 1

        registro[
            "cache_path"
        ] = ruta_cache

        registro[
            "extension"
        ] = extension

        manifest_nuevo[
            clave
        ] = {
            "output_property":
                registro[
                    "output_property"
                ],
            "source_property":
                registro[
                    "source_property"
                ],
            "asset_key":
                str(
                    asset_key
                ),
            "cache_file":
                ruta_cache.name
        }

    # ========================================================
    # ELIMINAR DEL CACHE LO QUE YA NO ES CURRENT
    # ========================================================

    archivos_validos = {
        dato[
            "cache_file"
        ]
        for dato
        in manifest_nuevo.values()
    }

    for archivo in (
        CACHE_FLYERS_INDIVIDUALES_DIR
        .iterdir()
    ):

        if not archivo.is_file():

            continue

        if (
            archivo.name
            in archivos_validos
        ):

            continue

        try:

            archivo.unlink()

        except Exception:

            pass

    guardar_manifest_cache(
        manifest_nuevo
    )

    return {
        "cache":
            cache_reutilizado,
        "new":
            descargados,
        "updated":
            actualizados
    }


# ============================================================
# CREAR SALIDA SOLO CON CURRENT
# ============================================================

def crear_salida_current(
    registros,
    directorio_personalizado_individual
):

    limpiar_directorio_archivos(
        FLYERS_INDIVIDUALES_DIR
    )

    if (
        directorio_personalizado_individual
        is not None
    ):

        limpiar_directorio_archivos(
            directorio_personalizado_individual
        )

    archivos_salida = []

    nombres_usados = {}

    for registro in registros:

        nombre_base = (
            limpiar_nombre_archivo(
                registro[
                    "output_property"
                ]
            )
        )

        extension = (
            registro[
                "extension"
            ]
        )

        contador = (
            nombres_usados.get(
                (
                    nombre_base.lower(),
                    extension.lower()
                ),
                0
            )
            + 1
        )

        nombres_usados[
            (
                nombre_base.lower(),
                extension.lower()
            )
        ] = contador

        if contador > 1:

            nombre_archivo = (
                f"{nombre_base} "
                f"({contador})."
                f"{extension}"
            )

        else:

            nombre_archivo = (
                f"{nombre_base}."
                f"{extension}"
            )

        ruta_salida = (
            FLYERS_INDIVIDUALES_DIR
            /
            nombre_archivo
        )

        shutil.copy2(
            registro[
                "cache_path"
            ],
            ruta_salida
        )

        archivos_salida.append(
            ruta_salida
        )

        if (
            directorio_personalizado_individual
            is not None
        ):

            shutil.copy2(
                ruta_salida,
                directorio_personalizado_individual
                /
                nombre_archivo
            )

    return archivos_salida


# ============================================================
# DESCARGAR / SINCRONIZAR FLYERS INDIVIDUALES
# ============================================================

def descargar_flyers_individuales():

    print("\n" + "=" * 100)
    print("FLYERS INDIVIDUALES - CURRENT")
    print("=" * 100)

    items, column_id, phase_column_id = (
        obtener_items_listing_flyer()
    )

    # ========================================================
    # SOLO CURRENT
    # ========================================================

    items_current = [
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

    # ========================================================
    # CONSOLIDAR ANTES DE VALIDAR / DESCARGAR
    # ========================================================

    registros = (
        consolidar_items_current(
            items_current,
            column_id
        )
    )

    port_ewen_origen = [
        item
        for item in items_current
        if (
            "port ewen"
            in str(
                item.get(
                    "name",
                    ""
                )
                or ""
            ).lower()
            and re.search(
                r"\b(186|188|190)\s+broadway\b",
                str(
                    item.get(
                        "name",
                        ""
                    )
                    or ""
                ),
                flags=re.IGNORECASE
            )
        )
    ]

    port_ewen_final = [
        registro
        for registro in registros
        if registro[
            "key"
        ] in {
            "port_ewen_broadway_186_188",
            "port_ewen_broadway_190"
        }
    ]

    print(
        f"\nCurrent encontrados en Monday: "
        f"{len(items_current)}"
    )

    if port_ewen_origen:

        print(
            f"Consolidación Port Ewen / Broadway: "
            f"{len(port_ewen_origen)} unidad(es) "
            f"→ {len(port_ewen_final)} flyer(s) individual(es)"
        )

    print(
        f"Flyers individuales requeridos "
        f"después de consolidar: "
        f"{len(registros)}"
    )

    # ========================================================
    # VALIDAR TODO ANTES DE MODIFICAR SALIDAS
    # ========================================================

    validar_flyers_requeridos(
        registros
    )

    # ========================================================
    # MODO PRUEBA - CONTINUAR SOLO CON LOS QUE TIENEN FLYER
    # ========================================================

    registros = [
        registro
        for registro in registros
        if (
            registro.get(
                "archivo"
            )
            is not None
        )
    ]

    # ========================================================
    # DIRECTORIO PERSONALIZADO
    # ========================================================

    directorio_personalizado = (
        obtener_directorio_personalizado()
    )

    directorio_personalizado_individual = None

    if (
        directorio_personalizado
        is not None
    ):

        directorio_personalizado_individual = (
            directorio_personalizado
            /
            "flyers_individuales"
        )

        directorio_personalizado_individual.mkdir(
            parents=True,
            exist_ok=True
        )

    # ========================================================
    # PREPARAR CACHE
    # ========================================================

    print(
        "\nSincronizando cache de "
        "flyers individuales..."
    )

    stats = (
        preparar_cache_current(
            registros
        )
    )

    # ========================================================
    # RECREAR SALIDA SOLO CON CURRENT
    # ========================================================

    archivos = (
        crear_salida_current(
            registros,
            directorio_personalizado_individual
        )
    )

    # ========================================================
    # RESULTADO
    # ========================================================

    print("\n" + "=" * 100)
    print("RESULTADO FLYERS INDIVIDUALES")
    print("=" * 100)

    print(
        f"\nCurrent en Monday: "
        f"{len(items_current)}"
    )

    print(
        f"Flyers finales después "
        f"de consolidación: "
        f"{len(registros)}"
    )

    print(
        f"Reutilizados desde cache: "
        f"{stats['cache']}"
    )

    print(
        f"Nuevos descargados: "
        f"{stats['new']}"
    )

    print(
        f"Actualizados desde Monday: "
        f"{stats['updated']}"
    )

    print(
        f"Flyers guardados en salida: "
        f"{len(archivos)}"
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

    return archivos
