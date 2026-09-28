import re
import unicodedata

import pandas as pd

from config.settings import (
    PROPERTIES_PER_FLYER
)


# ============================================================
# NORMALIZAR TEXTO
# ============================================================

def normalizar_texto(texto):

    if texto is None:
        return ""

    texto = (
        str(texto)
        .strip()
        .lower()
    )

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )

    texto = re.sub(
        r"[^a-z0-9]+",
        " ",
        texto
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


# ============================================================
# LOCATION VISUAL
# ============================================================

def obtener_display_location(
    location,
    details
):

    location_original = (
        str(location or "")
        .strip()
    )

    location_norm = (
        normalizar_texto(
            location_original
        )
    )

    details_norm = (
        normalizar_texto(
            details
        )
    )

    # ========================================================
    # CASO ESPECIAL MONROE
    # ========================================================

    if location_norm == "monroe":

        if (
            "center monroe"
            in details_norm
        ):

            return "Center Monroe"

        return "Monroe"

    # ========================================================
    # RESTO DE LOCATIONS
    # ========================================================

    return location_original


# ============================================================
# FORMATEAR PRECIO
# ============================================================

def formatear_precio(valor):

    if valor is None:
        return ""

    texto = (
        str(valor)
        .replace("$", "")
        .replace(",", "")
        .strip()
    )

    if not texto:
        return ""

    try:

        numero = float(texto)

        numero = int(
            round(numero)
        )

        return (
            f"${numero:,}/month"
        )

    except ValueError:

        return (
            f"${texto}/month"
        )


# ============================================================
# FORMATEAR BEDROOM
# ============================================================

def formatear_bedroom(valor):

    texto = (
        str(valor or "")
        .strip()
    )

    normalizado = (
        normalizar_texto(
            texto
        )
    )

    # --------------------------------------------------------
    # STUDIO
    # --------------------------------------------------------

    if "studio" in normalizado:

        return "Studio"

    # --------------------------------------------------------
    # BED
    # --------------------------------------------------------

    match = re.search(
        r"(\d+(?:\.\d+)?)",
        texto
    )

    if not match:

        return texto

    numero = (
        match.group(1)
    )

    return (
        f"{numero} Bed"
    )


# ============================================================
# FORMATEAR BATH
# ============================================================

def formatear_bath(valor):

    texto = (
        str(valor or "")
        .strip()
    )

    match = re.search(
        r"(\d+(?:\.\d+)?)",
        texto
    )

    if not match:

        return texto

    numero = (
        match.group(1)
    )

    return (
        f"{numero} Bath"
    )


# ============================================================
# PREPARAR DATASET PARA FLYER
# ============================================================

def preparar_dataset_flyer(
    df,
    listing_type
):

    # ========================================================
    # EVITAR PROBLEMAS CON DATAFRAME VACÍO
    # ========================================================

    if df is None or df.empty:

        return pd.DataFrame(
            columns=[
                "property",
                "Location",
                "Details",
                "Price",
                "Bedroom",
                "Bath",
                "image_drive_url",
                "display_location",
                "price_text",
                "bedroom_text",
                "bath_text",
                "listing_type"
            ]
        )

    df = df.copy()

    # ========================================================
    # LOCATION VISUAL
    # ========================================================

    df[
        "display_location"
    ] = df.apply(
        lambda fila:
        obtener_display_location(
            fila.get(
                "Location",
                ""
            ),
            fila.get(
                "Details",
                ""
            )
        ),
        axis=1
    )

    # ========================================================
    # PRECIO VISUAL
    # ========================================================

    df[
        "price_text"
    ] = (
        df["Price"]
        .apply(
            formatear_precio
        )
    )

    # ========================================================
    # BEDROOM VISUAL
    # ========================================================

    df[
        "bedroom_text"
    ] = (
        df["Bedroom"]
        .apply(
            formatear_bedroom
        )
    )

    # ========================================================
    # BATH VISUAL
    # ========================================================

    df[
        "bath_text"
    ] = (
        df["Bath"]
        .apply(
            formatear_bath
        )
    )

    # ========================================================
    # CURRENT / ARCHIVED
    # ========================================================

    df[
        "listing_type"
    ] = listing_type

    return df


# ============================================================
# ORDENAR MONROE / CENTER MONROE
# SIN ALTERAR EL ORDEN GENERAL DE LOCATIONS
# ============================================================

def ordenar_monroe_center(
    df
):

    if df.empty:
        return df

    df = df.copy()

    # ========================================================
    # GUARDAR ORDEN ORIGINAL DE LAS LOCATIONS
    #
    # inventory.py ya ordenó las locations por cantidad.
    # Aquí respetamos ese orden.
    # ========================================================

    location_order = {}

    siguiente_orden = 0

    for location in df["Location"]:

        location_norm = (
            normalizar_texto(
                location
            )
        )

        if (
            location_norm
            not in location_order
        ):

            location_order[
                location_norm
            ] = siguiente_orden

            siguiente_orden += 1

    # ========================================================
    # PRIORIDAD GENERAL DE LOCATION
    # ========================================================

    df[
        "_location_order"
    ] = (
        df["Location"]
        .apply(
            normalizar_texto
        )
        .map(
            location_order
        )
    )

    # ========================================================
    # PRIORIDAD DENTRO DE MONROE
    #
    # Monroe        -> 0
    # Center Monroe -> 1
    # Resto         -> 0
    # ========================================================

    def prioridad_monroe(fila):

        location_norm = (
            normalizar_texto(
                fila["Location"]
            )
        )

        if location_norm != "monroe":
            return 0

        if (
            fila["display_location"]
            == "Center Monroe"
        ):
            return 1

        return 0

    df[
        "_monroe_priority"
    ] = df.apply(
        prioridad_monroe,
        axis=1
    )

    # ========================================================
    # ORDENAR
    # ========================================================

    df = df.sort_values(
        by=[
            "_location_order",
            "_monroe_priority"
        ],
        ascending=[
            True,
            True
        ],
        kind="stable"
    )

    # ========================================================
    # LIMPIAR
    # ========================================================

    df = df.drop(
        columns=[
            "_location_order",
            "_monroe_priority"
        ]
    )

    return df.reset_index(
        drop=True
    )


# ============================================================
# CREAR GRUPOS PARA LOS FLYERS
# ============================================================

def crear_grupos_flyers(
    current,
    archived
):

    # ========================================================
    # PREPARAR CURRENT
    # ========================================================

    current = (
        preparar_dataset_flyer(
            current,
            "current"
        )
    )

    # ========================================================
    # PREPARAR ARCHIVED
    # ========================================================

    archived = (
        preparar_dataset_flyer(
            archived,
            "archived"
        )
    )

    # ========================================================
    # MONROE / CENTER MONROE
    # ========================================================

    current = (
        ordenar_monroe_center(
            current
        )
    )

    archived = (
        ordenar_monroe_center(
            archived
        )
    )

    grupos = []

    total_current = (
        len(current)
    )

    # ========================================================
    # CUÁNTOS FLYERS COMPLETOS CURRENT TENEMOS
    # ========================================================

    grupos_completos = (
        total_current
        // PROPERTIES_PER_FLYER
    )

    # ========================================================
    # CREAR FLYERS DE 10 CURRENT
    # ========================================================

    for numero in range(
        grupos_completos
    ):

        inicio = (
            numero
            * PROPERTIES_PER_FLYER
        )

        fin = (
            inicio
            + PROPERTIES_PER_FLYER
        )

        grupo = (
            current.iloc[
                inicio:fin
            ]
            .copy()
        )

        grupos.append(
            grupo
        )

    # ========================================================
    # CURRENT RESTANTES
    # ========================================================

    resto_inicio = (
        grupos_completos
        * PROPERTIES_PER_FLYER
    )

    restantes = (
        current.iloc[
            resto_inicio:
        ]
        .copy()
    )

    # ========================================================
    # SI ES MÚLTIPLO EXACTO DE 10
    # ========================================================

    if restantes.empty:

        return grupos

    # ========================================================
    # CUÁNTAS ARCHIVED HACEN FALTA
    # ========================================================

    faltantes = (
        PROPERTIES_PER_FLYER
        - len(restantes)
    )

    # Archived ya viene previamente
    # seleccionado en Fase 2.

    archived_necesarios = (
        archived.head(
            faltantes
        )
        .copy()
    )

    # ========================================================
    # ÚLTIMO FLYER
    # ========================================================

    ultimo = pd.concat(
        [
            restantes,
            archived_necesarios
        ],
        ignore_index=True
    )

    # ========================================================
    # VALIDACIÓN
    # ========================================================

    if (
        len(ultimo)
        < PROPERTIES_PER_FLYER
    ):

        faltan = (
            PROPERTIES_PER_FLYER
            - len(ultimo)
        )

        print("\n" + "!" * 100)

        print(
            "WARNING:"
        )

        print(
            "El último flyer no puede "
            "completarse con 10 propiedades."
        )

        print(
            f"Propiedades disponibles: "
            f"{len(ultimo)}"
        )

        print(
            f"Propiedades faltantes: "
            f"{faltan}"
        )

        print(
            "Se generará el grupo con "
            "las propiedades disponibles."
        )

        print(
            "!" * 100
        )

    grupos.append(
        ultimo
    )

    return grupos