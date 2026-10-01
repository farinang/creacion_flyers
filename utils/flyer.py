from io import BytesIO
from pathlib import Path
import re
import time

import requests

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageOps
)

from config.settings import (

    # ========================================================
    # ARCHIVOS / SALIDA
    # ========================================================

    FLYERS_DIR,
    FLYER_FILE_PREFIX,
    FLYER_FORMAT,
    FLYER_TEMPLATE_FILE,

    BED_ICON_FILE,
    BATH_ICON_FILE,

    # ========================================================
    # FUENTES
    # ========================================================

    FONT_GARET_BOLD,
    FONT_GARET_REGULAR,
    FONT_COMFORTAA_BOLD,
    FONT_LEAGUE_SPARTAN_BOLD,

    # ========================================================
    # TAMAÑOS DE FUENTE
    # ========================================================

    FONT_SIZE_LOCATION,
    FONT_SIZE_LOCATION_MIN,
    FONT_SIZE_PRICE,
    FONT_SIZE_BADGE,
    BADGE_TEXT_STROKE_WIDTH,
    FONT_SIZE_BED_BATH_VALUE,
    FONT_SIZE_BED_BATH_LABEL,
    FONT_SIZE_RENTED,

    # ========================================================
    # TAMAÑO FLYER
    # ========================================================

    FLYER_WIDTH,
    FLYER_HEIGHT,

    # ========================================================
    # GRID
    # ========================================================

    GRID_TOP,
    GRID_LEFT_X,
    GRID_RIGHT_X,
    GRID_ROW_HEIGHT,
    GRID_ROW_GAP,

    # ========================================================
    # IMÁGENES
    # ========================================================

    PROPERTY_IMAGE_WIDTH,
    PROPERTY_IMAGE_HEIGHT,

    # ========================================================
    # CARD / MIRROR
    # ========================================================

    PROPERTY_CARD_WIDTH,
    PROPERTY_CARD_HEIGHT,

    # ========================================================
    # IMAGEN IZQUIERDA - LAYOUT MAESTRO
    # ========================================================

    LEFT_IMAGE_X_OFFSET,
    LEFT_IMAGE_Y_OFFSET,

    # ========================================================
    # CONTENEDOR IZQUIERDA - LAYOUT MAESTRO
    # ========================================================

    LEFT_INFO_GROUP_X_OFFSET,
    LEFT_INFO_GROUP_Y_OFFSET,

    LEFT_INFO_GROUP_WIDTH,
    LEFT_INFO_GROUP_HEIGHT,

    LEFT_LOCATION_REL_X,
    LEFT_LOCATION_REL_Y,

    LEFT_BADGE_REL_X,
    LEFT_BADGE_REL_Y,

    LEFT_PRICE_REL_X,
    LEFT_PRICE_REL_Y,

    LEFT_FEATURE_FAR_REL_X,
    LEFT_FEATURE_NEAR_REL_X,
    LEFT_FEATURE_Y,

    FEATURE_SLOT_WIDTH,

    # ========================================================
    # RIGHT DETAILS
    # ========================================================
    RIGHT_DETAILS_OFFSET_X,
    RIGHT_DETAILS_OFFSET_Y,

    # ========================================================
    # BADGE FOR RENT
    # ========================================================

    FOR_RENT_TEXT,
    FOR_RENT_BADGE_WIDTH,
    FOR_RENT_BADGE_HEIGHT,
    FOR_RENT_BADGE_RADIUS,
    FOR_RENT_BG_COLOR,
    FOR_RENT_TEXT_COLOR,

    # ========================================================
    # RENTED
    # ========================================================

    RENTED_TEXT,
    RENTED_TEXT_COLOR,
    RENTED_ANGLE,

    # ========================================================
    # PRICE
    # ========================================================

    PRICE_BOX_WIDTH,
    PRICE_BOX_HEIGHT,
    PRICE_BOX_RADIUS,
    PRICE_BOX_FILL,
    PRICE_BOX_OUTLINE,
    PRICE_TEXT_COLOR,

    # ========================================================
    # BED / BATH
    # ========================================================

    BED_BATH_ICON_SIZE,
    BED_BATH_GAP,
    BED_BATH_TEXT_COLOR,
    FEATURE_ICON_VALUE_GAP,
    FEATURE_VALUE_LABEL_GAP,
    FEATURE_ICON_Y_OFFSET,

    # ========================================================
    # LOCATION
    # ========================================================

    LOCATION_TEXT_COLOR,
    LOCATION_MAX_WIDTH_LEFT,
    LOCATION_MAX_WIDTH_RIGHT,
    LOCATION_MAX_LINES,
    LOCATION_MULTILINE_EXTRA_UP,

    # ========================================================
    # Caché
    # ========================================================

    CACHE_IMAGES_DIR
)


# ============================================================
# CACHE
# ============================================================

_FONT_CACHE = {}
_ICON_CACHE = {}
_IMAGE_CACHE_MEMORY = {}

_IMAGE_PREPARATION_STATS = {
    "cache": 0,
    "drive": 0,
    "failed": []
}


# ============================================================
# COLORES
# ============================================================

def hex_to_rgb(hex_color):

    color = (
        hex_color
        .strip()
        .lstrip("#")
    )

    if len(color) != 6:

        raise ValueError(
            f"Color inválido: "
            f"{hex_color}"
        )

    return tuple(
        int(
            color[i:i + 2],
            16
        )
        for i in (
            0,
            2,
            4
        )
    )


# ============================================================
# VALIDAR ARCHIVO
# ============================================================

def asegurar_archivo(
    path_obj
):

    if not Path(
        path_obj
    ).exists():

        raise FileNotFoundError(
            f"No existe:\n"
            f"{path_obj}"
        )


# ============================================================
# FUENTES
# ============================================================

def cargar_fuente(
    path_obj,
    size
):

    key = (
        str(path_obj),
        size
    )

    if key in _FONT_CACHE:

        return (
            _FONT_CACHE[
                key
            ]
        )

    asegurar_archivo(
        path_obj
    )

    fuente = (
        ImageFont.truetype(
            str(path_obj),
            size=size
        )
    )

    _FONT_CACHE[
        key
    ] = fuente

    return fuente


# ============================================================
# TEMPLATE
# ============================================================

def abrir_template():

    asegurar_archivo(
        FLYER_TEMPLATE_FILE
    )

    imagen = (
        Image.open(
            FLYER_TEMPLATE_FILE
        )
        .convert(
            "RGBA"
        )
    )

    if imagen.size != (
        FLYER_WIDTH,
        FLYER_HEIGHT
    ):

        imagen = (
            imagen.resize(
                (
                    FLYER_WIDTH,
                    FLYER_HEIGHT
                ),
                Image.Resampling.LANCZOS
            )
        )

    return imagen


# ============================================================
# ICONOS
# ============================================================

def cargar_icono_png(
    path_obj,
    size
):

    key = (
        str(path_obj),
        size
    )

    if key in _ICON_CACHE:

        return (
            _ICON_CACHE[
                key
            ]
        )

    asegurar_archivo(
        path_obj
    )

    icon = (
        Image.open(
            path_obj
        )
        .convert(
            "RGBA"
        )
    )

    icon = (
        icon.resize(
            (
                size,
                size
            ),
            Image.Resampling.LANCZOS
        )
    )

    _ICON_CACHE[
        key
    ] = icon

    return icon


# ============================================================
# MEDIR TEXTO
# ============================================================

def medir_texto(
    draw,
    text,
    font
):

    bbox = (
        draw.textbbox(
            (
                0,
                0
            ),
            str(text),
            font=font
        )
    )

    width = (
        bbox[2]
        - bbox[0]
    )

    height = (
        bbox[3]
        - bbox[1]
    )

    return (
        width,
        height
    )


# ============================================================
# PARTIR TEXTO LOCATION
# ============================================================

def partir_texto_en_lineas(
    draw,
    texto,
    font,
    max_width,
    max_lines=2
):

    texto = (
        str(
            texto
            or ""
        )
        .strip()
    )

    if not texto:

        return [
            ""
        ]

    palabras = (
        texto.split()
    )

    if len(
        palabras
    ) == 1:

        palabra = (
            palabras[0]
        )

        width, _ = (
            medir_texto(
                draw,
                palabra,
                font
            )
        )

        if (
            width
            <= max_width
        ):

            return [
                palabra
            ]

    lineas = []
    actual = ""

    for palabra in palabras:

        prueba = (
            palabra
            if not actual
            else
            f"{actual} "
            f"{palabra}"
        )

        width, _ = (
            medir_texto(
                draw,
                prueba,
                font
            )
        )

        if (
            width
            <= max_width
        ):

            actual = prueba

        else:

            if actual:

                lineas.append(
                    actual
                )

            actual = palabra

    if actual:

        lineas.append(
            actual
        )

    if (
        len(lineas)
        <= max_lines
    ):

        return lineas

    lineas = (
        lineas[
            :max_lines
        ]
    )

    ultima = (
        lineas[-1]
    )

    while ultima:

        prueba = (
            ultima
            + "..."
        )

        width, _ = (
            medir_texto(
                draw,
                prueba,
                font
            )
        )

        if (
            width
            <= max_width
        ):

            break

        ultima = (
            ultima[
                :-1
            ]
            .rstrip()
        )

    lineas[-1] = (
        ultima + "..."
        if ultima
        else "..."
    )

    return lineas


# ============================================================
# ALTURA DE LINEA
# ============================================================

def obtener_line_height(
    draw,
    font
):

    _, height = (
        medir_texto(
            draw,
            "Ag",
            font
        )
    )

    return (
        height
        + 2
    )


# ============================================================
# EXTRAER FILE ID DE DRIVE
# ============================================================

def extraer_drive_file_id(
    url
):

    url = (
        str(
            url
            or ""
        )
        .strip()
    )

    if not url:

        return None

    patrones = [

        r"/d/([a-zA-Z0-9_-]+)",

        r"id=([a-zA-Z0-9_-]+)",

        r"/file/d/([a-zA-Z0-9_-]+)"
    ]

    for patron in patrones:

        match = (
            re.search(
                patron,
                url
            )
        )

        if match:

            return (
                match.group(
                    1
                )
            )

    return None


# ============================================================
# URL DE DESCARGA DRIVE
# ============================================================

def construir_url_descarga(
    url
):

    url = (
        str(
            url
            or ""
        )
        .strip()
    )

    if not url:

        return ""

    if (
        "drive.google.com"
        in url
    ):

        file_id = (
            extraer_drive_file_id(
                url
            )
        )

        if file_id:

            return (
                "https://drive.google.com/uc"
                f"?export=view&id="
                f"{file_id}"
            )

    return url

# ============================================================
# RUTA DE IMAGEN EN CACHE
# ============================================================

def obtener_ruta_cache_imagen(
    url
):

    file_id = (
        extraer_drive_file_id(
            url
        )
    )

    if not file_id:

        return None

    return (
        CACHE_IMAGES_DIR /
        f"{file_id}.jpg"
    )


# ============================================================
# CARGAR IMAGEN DESDE CACHE
# ============================================================

def cargar_imagen_desde_cache(
    url
):

    ruta_cache = (
        obtener_ruta_cache_imagen(
            url
        )
    )

    if ruta_cache is None:

        return None

    if not ruta_cache.exists():

        return None

    try:

        imagen = (
            Image.open(
                ruta_cache
            )
            .convert(
                "RGB"
            )
        )

        return imagen

    except Exception:

        return None


# ============================================================
# GUARDAR IMAGEN EN CACHE
# ============================================================

def guardar_imagen_en_cache(
    imagen,
    url
):

    ruta_cache = (
        obtener_ruta_cache_imagen(
            url
        )
    )

    if ruta_cache is None:

        return

    CACHE_IMAGES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    imagen.save(
        ruta_cache,
        format="JPEG",
        quality=95
    )

# ============================================================
# DESCARGAR IMAGEN
# ============================================================

def descargar_imagen_desde_url(
    url,
    max_intentos=3
):

    url_descarga = (
        construir_url_descarga(
            url
        )
    )

    if not url_descarga:

        raise ValueError(
            "URL de imagen vacía."
        )

    headers = {

        "User-Agent":
        (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/131.0 Safari/537.36"
        )
    }

    ultimo_error = None

    for intento in range(
        1,
        max_intentos + 1
    ):

        try:

            response = (
                requests.get(
                    url_descarga,
                    headers=headers,
                    timeout=30
                )
            )

            response.raise_for_status()

            content_type = (
                response.headers
                .get(
                    "Content-Type",
                    ""
                )
                .lower()
            )

            if (
                "image"
                not in content_type
            ):

                raise ValueError(
                    "Google Drive no devolvió "
                    "una imagen. "
                    f"Content-Type: "
                    f"{content_type}"
                )

            imagen = (
                Image.open(
                    BytesIO(
                        response.content
                    )
                )
                .convert(
                    "RGB"
                )
            )

            return imagen

        except Exception as error:

            ultimo_error = error

            if intento < max_intentos:

                time.sleep(
                    intento * 2
                )

    raise RuntimeError(
        f"No se pudo descargar la imagen "
        f"después de {max_intentos} intentos. "
        f"Último error: {ultimo_error}"
    )

# ============================================================
# PREPARAR IMÁGENES
# ============================================================
#
# Si existe cache:
#
#     utiliza las imágenes disponibles
#     y descarga solamente las faltantes.
#
# Si NO existe cache:
#
#     crea la carpeta
#     y descarga todas las imágenes desde Drive.
#
# ============================================================

def preparar_imagenes_flyers(
    grupos
):

    global _IMAGE_CACHE_MEMORY
    global _IMAGE_PREPARATION_STATS

    _IMAGE_CACHE_MEMORY = {}

    _IMAGE_PREPARATION_STATS = {
        "cache": 0,
        "drive": 0,
        "failed": []
    }

    # ========================================================
    # DETECTAR SI CACHE EXISTÍA
    # ========================================================

    cache_existia = (
        CACHE_IMAGES_DIR.exists()
    )

    print(
        "\n" + "=" * 100
    )

    print(
        "PREPARANDO IMÁGENES"
    )

    print(
        "=" * 100
    )

    if cache_existia:

        print(
            "Cache encontrada."
        )

        print(
            "Se utilizarán imágenes locales "
            "y solo se descargarán las faltantes."
        )

    else:

        print(
            "Cache no encontrada."
        )

        print(
            "Todas las imágenes serán "
            "descargadas desde Google Drive."
        )

        CACHE_IMAGES_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

    # ========================================================
    # OBTENER PROPIEDADES ÚNICAS
    # ========================================================

    registros = []

    urls_vistas = set()

    for grupo in grupos:

        for _, fila in grupo.iterrows():

            url = str(
                fila.get(
                    "image_drive_url",
                    ""
                )
                or ""
            ).strip()

            if not url:

                continue

            if url in urls_vistas:

                continue

            urls_vistas.add(
                url
            )

            property_name = str(
                fila.get(
                    "property",
                    ""
                )
                or ""
            ).strip()

            registros.append(
                {
                    "property":
                        property_name,

                    "url":
                        url
                }
            )

    total = len(
        registros
    )

    exitosas = 0

    # ========================================================
    # PROGRESO
    # ========================================================

    print(
        f"\nPreparando imágenes: "
        f"0/{total}",
        end="",
        flush=True
    )

    for registro in registros:

        property_name = (
            registro[
                "property"
            ]
        )

        url = (
            registro[
                "url"
            ]
        )

        imagen = None

        # ====================================================
        # MEMORIA
        # ====================================================

        if url in _IMAGE_CACHE_MEMORY:

            imagen = (
                _IMAGE_CACHE_MEMORY[
                    url
                ]
            )

        # ====================================================
        # CACHE LOCAL
        # ====================================================

        if (
            imagen is None
            and cache_existia
        ):

            imagen = (
                cargar_imagen_desde_cache(
                    url
                )
            )

            if imagen is not None:

                _IMAGE_PREPARATION_STATS[
                    "cache"
                ] += 1

        # ====================================================
        # GOOGLE DRIVE
        # ====================================================

        if imagen is None:

            try:

                imagen = (
                    descargar_imagen_desde_url(
                        url
                    )
                )

                guardar_imagen_en_cache(
                    imagen,
                    url
                )

                _IMAGE_PREPARATION_STATS[
                    "drive"
                ] += 1

            except Exception:

                _IMAGE_PREPARATION_STATS[
                    "failed"
                ].append(
                    {
                        "property":
                            property_name,

                        "url":
                            url
                    }
                )

        # ====================================================
        # GUARDAR EN MEMORIA
        # ====================================================

        if imagen is not None:

            _IMAGE_CACHE_MEMORY[
                url
            ] = imagen

            exitosas += 1

        # ====================================================
        # ACTUALIZAR MISMA LÍNEA
        # ====================================================

        print(
            f"\rPreparando imágenes: "
            f"{exitosas}/{total}",
            end="",
            flush=True
        )

    # ========================================================
    # RESULTADO
    # ========================================================

    failed = (
        _IMAGE_PREPARATION_STATS[
            "failed"
        ]
    )

    if not failed:

        print(
            f"\rPreparando imágenes: "
            f"{total}/{total} - Todo OK"
        )

    else:

        print(
            f"\rPreparando imágenes: "
            f"{exitosas}/{total}"
        )

        print(
            "\nNo se pudo descargar:"
        )

        for error in failed:

            print(
                f'- {error["property"]} / '
                f'{error["url"]}'
            )

    # ========================================================
    # RESUMEN DEL ORIGEN
    # ========================================================

    usadas_cache = (
        _IMAGE_PREPARATION_STATS[
            "cache"
        ]
    )

    descargadas = (
        _IMAGE_PREPARATION_STATS[
            "drive"
        ]
    )

    print()

    if not cache_existia:

        print(
            "Modo imágenes: "
            "Google Drive → Cache local"
        )

        print(
            f"Descargadas desde Drive: "
            f"{descargadas}"
        )

    elif (
        usadas_cache > 0
        and descargadas > 0
    ):

        print(
            "Modo imágenes: "
            "Cache local + Google Drive"
        )

        print(
            f"Desde cache: "
            f"{usadas_cache}"
        )

        print(
            f"Descargadas nuevas: "
            f"{descargadas}"
        )

    elif (
        usadas_cache > 0
        and descargadas == 0
    ):

        print(
            "Modo imágenes: "
            "Solo cache local"
        )

        print(
            f"Desde cache: "
            f"{usadas_cache}"
        )

    else:

        print(
            "Modo imágenes: "
            "Google Drive"
        )

# ============================================================
# PLACEHOLDER
# ============================================================

def crear_placeholder_imagen():

    img = (
        Image.new(
            "RGB",
            (
                PROPERTY_IMAGE_WIDTH,
                PROPERTY_IMAGE_HEIGHT
            ),
            (
                210,
                210,
                210
            )
        )
    )

    draw = (
        ImageDraw.Draw(
            img
        )
    )

    draw.rectangle(
        (
            0,
            0,
            PROPERTY_IMAGE_WIDTH - 1,
            PROPERTY_IMAGE_HEIGHT - 1
        ),
        outline=(
            170,
            170,
            170
        ),
        width=2
    )

    draw.line(
        (
            0,
            0,
            PROPERTY_IMAGE_WIDTH,
            PROPERTY_IMAGE_HEIGHT
        ),
        fill=(
            170,
            170,
            170
        ),
        width=2
    )

    draw.line(
        (
            PROPERTY_IMAGE_WIDTH,
            0,
            0,
            PROPERTY_IMAGE_HEIGHT
        ),
        fill=(
            170,
            170,
            170
        ),
        width=2
    )

    return img


# ============================================================
# PREPARAR FOTO
# ============================================================

def preparar_imagen_propiedad(
    url
):

    imagen = (
        _IMAGE_CACHE_MEMORY.get(
            url
        )
    )

    # ========================================================
    # FALLBACK
    # ========================================================
    #
    # En condiciones normales la imagen ya fue preparada
    # anteriormente.
    #
    # Si no existe, utilizamos placeholder.
    #
    # ========================================================

    if imagen is None:

        imagen = (
            crear_placeholder_imagen()
        )

    imagen = (
        ImageOps.fit(
            imagen,
            (
                PROPERTY_IMAGE_WIDTH,
                PROPERTY_IMAGE_HEIGHT
            ),
            method=
                Image.Resampling.LANCZOS,
            centering=(
                0.5,
                0.5
            )
        )
    )

    return (
        imagen.convert(
            "RGBA"
        )
    )


# ============================================================
# LOCATION
# ============================================================

def dibujar_location(
    draw,
    text,
    x,
    y,
    max_width,
    align
):

    texto = (
        str(
            text
            or ""
        )
        .strip()
    )

    # ========================================================
    # FUENTE BASE
    # ========================================================

    font_size = (
        FONT_SIZE_LOCATION
    )

    font = cargar_fuente(
        FONT_GARET_BOLD,
        font_size
    )

    # ========================================================
    # ALTURA DE REFERENCIA
    # ========================================================
    #
    # Guardamos la altura que tendría Location con
    # FONT_SIZE_LOCATION original.
    #
    # Si posteriormente reducimos la fuente,
    # compensaremos verticalmente para mantener
    # el mismo centro visual.
    #
    # ========================================================

    font_referencia = cargar_fuente(
        FONT_GARET_BOLD,
        FONT_SIZE_LOCATION
    )

    _, altura_referencia = (
        medir_texto(
            draw,
            "Ag",
            font_referencia
        )
    )

    ajuste_fuente_y = 0

    # ========================================================
    # PALABRA ÚNICA MUY LARGA
    # ========================================================
    #
    # Ejemplo:
    #
    # Washingtonville
    #
    # Como no existe un espacio donde hacer salto de línea,
    # reducimos automáticamente el tamaño de fuente
    # hasta que entre dentro de max_width.
    #
    # ========================================================

    palabras = (
        texto.split()
    )

    if len(palabras) == 1:

        width, _ = (
            medir_texto(
                draw,
                texto,
                font
            )
        )

        while (
            width > max_width
            and font_size
            > FONT_SIZE_LOCATION_MIN
        ):

            font_size -= 1

            font = cargar_fuente(
                FONT_GARET_BOLD,
                font_size
            )

            width, _ = (
                medir_texto(
                    draw,
                    texto,
                    font
                )
            )

        # ========================================================
        # COMPENSACIÓN VERTICAL POR CAMBIO DE FUENTE
        # ========================================================
        #
        # Solo aplicamos compensación si realmente
        # FONT_SIZE_LOCATION fue reducido.
        #
        # Si la fuente mantiene su tamaño original,
        # ajuste_fuente_y permanece en 0.
        #
        # ========================================================

        if font_size < FONT_SIZE_LOCATION:

            bbox_referencia = draw.textbbox(
                (
                    0,
                    0
                ),
                texto,
                font=font_referencia
            )

            bbox_actual = draw.textbbox(
                (
                    0,
                    0
                ),
                texto,
                font=font
            )

            ajuste_fuente_y = (
                bbox_referencia[3]
                - bbox_actual[3]
                - 2
            )

    # ========================================================
    # PARTIR TEXTO EN LINEAS
    # ========================================================

    lineas = partir_texto_en_lineas(
        draw=draw,
        texto=texto,
        font=font,
        max_width=max_width,
        max_lines=LOCATION_MAX_LINES
    )

    line_height = obtener_line_height(
        draw,
        font
    )

    # ========================================================
    # AJUSTE VERTICAL
    # ========================================================
    #
    # Si hay 1 línea:
    #     empieza exactamente en y
    #
    # Si hay 2 líneas:
    #     subimos media altura de línea
    #
    # De esta forma:
    #
    #       Center
    #       Monroe
    #
    # queda centrado verticalmente respecto
    # a donde estaría "Monroe" en una sola línea.
    # ========================================================

    cantidad_lineas = len(
        lineas
    )

    offset_vertical = (
        (
            cantidad_lineas - 1
        )
        * line_height
        / 2
    )

    extra_up = 0

    if cantidad_lineas > 1:

        extra_up = (
            LOCATION_MULTILINE_EXTRA_UP
        )

    start_y = (
        y
        - offset_vertical
        - extra_up
        + ajuste_fuente_y
    )

    # ========================================================
    # DIBUJAR LINEAS
    # ========================================================

    for indice, linea in enumerate(
        lineas
    ):

        line_y = (
            start_y
            + indice
            * line_height
        )

        line_w, _ = medir_texto(
            draw,
            linea,
            font
        )

        if align == "right":

            line_x = (
                x
                + max_width
                - line_w
            )

        else:

            line_x = x

        draw.text(
            (
                line_x,
                line_y
            ),
            linea,
            font=font,
            fill=hex_to_rgb(
                LOCATION_TEXT_COLOR
            )
        )


# ============================================================
# FOR RENT
# ============================================================

def dibujar_badge_for_rent(
    canvas,
    draw,
    x,
    y
):

    # ========================================================
    # BADGE
    # ========================================================

    rect = (
        x,
        y,
        x
        + FOR_RENT_BADGE_WIDTH,
        y
        + FOR_RENT_BADGE_HEIGHT
    )

    draw.rounded_rectangle(
        rect,
        radius=
            FOR_RENT_BADGE_RADIUS,
        fill=hex_to_rgb(
            FOR_RENT_BG_COLOR
        )
    )

    # ========================================================
    # TEXTO - SUPERSAMPLING
    # ========================================================
    #
    # En lugar de renderizar Comfortaa Bold directamente
    # a FONT_SIZE_BADGE (muy pequeño), lo dibujamos
    # varias veces más grande y después lo reducimos.
    #
    # Esto conserva mejor la forma y el grosor
    # original de la fuente.
    #
    # ========================================================

    SCALE = 5

    font = cargar_fuente(
        FONT_COMFORTAA_BOLD,
        FONT_SIZE_BADGE * SCALE
    )

    # ========================================================
    # MEDIR TEXTO
    # ========================================================

    temp_draw = ImageDraw.Draw(
        Image.new(
            "RGBA",
            (
                FOR_RENT_BADGE_WIDTH * SCALE,
                FOR_RENT_BADGE_HEIGHT * SCALE
            ),
            (
                0,
                0,
                0,
                0
            )
        )
    )

    bbox = temp_draw.textbbox(
        (
            0,
            0
        ),
        FOR_RENT_TEXT,
        font=font
    )

    text_w = (
        bbox[2]
        - bbox[0]
    )

    text_h = (
        bbox[3]
        - bbox[1]
    )

    # ========================================================
    # CAPA TEMPORAL
    # ========================================================

    texto_layer = Image.new(
        "RGBA",
        (
            FOR_RENT_BADGE_WIDTH * SCALE,
            FOR_RENT_BADGE_HEIGHT * SCALE
        ),
        (
            0,
            0,
            0,
            0
        )
    )

    texto_draw = ImageDraw.Draw(
        texto_layer
    )

    text_x = (
        (
            FOR_RENT_BADGE_WIDTH
            * SCALE
            - text_w
        )
        / 2
        - bbox[0]
    )

    text_y = (
        (
            FOR_RENT_BADGE_HEIGHT
            * SCALE
            - text_h/2
        )
        / 2
        - bbox[1]
        - SCALE
    )

    texto_draw.text(
        (
            text_x,
            text_y
        ),
        FOR_RENT_TEXT,
        font=font,
        fill=hex_to_rgb(
            FOR_RENT_TEXT_COLOR
        )
        + (255,)
    )

    # ========================================================
    # REDUCIR A TAMAÑO REAL
    # ========================================================

    texto_layer = texto_layer.resize(
        (
            FOR_RENT_BADGE_WIDTH,
            FOR_RENT_BADGE_HEIGHT
        ),
        Image.Resampling.LANCZOS
    )

    # ========================================================
    # PEGAR SOBRE EL FLYER
    # ========================================================

    draw._image.alpha_composite(
        texto_layer,
        (
            int(x),
            int(y)
        )
    )

    canvas.alpha_composite(
        texto_layer,
        (
            int(x),
            int(y)
        )
    )


# ============================================================
# PRICE
# ============================================================

def dibujar_price_box(
    draw,
    text,
    x,
    y
):

    rect = (
        x,
        y,
        x
        + PRICE_BOX_WIDTH,
        y
        + PRICE_BOX_HEIGHT
    )

    draw.rounded_rectangle(
        rect,
        radius=
            PRICE_BOX_RADIUS,
        fill=hex_to_rgb(
            PRICE_BOX_FILL
        ),
        outline=hex_to_rgb(
            PRICE_BOX_OUTLINE
        ),
        width=2
    )

    font = (
        cargar_fuente(
            FONT_GARET_REGULAR,
            FONT_SIZE_PRICE
        )
    )

    text_w, text_h = (
        medir_texto(
            draw,
            text,
            font
        )
    )

    text_x = (
        x
        + (
            PRICE_BOX_WIDTH
            - text_w
        )
        / 2
    )

    text_y = (
        y
        + (
            PRICE_BOX_HEIGHT
            - text_h
        )
        / 2
        - 3
    )

    draw.text(
        (
            text_x,
            text_y
        ),
        text,
        font=font,
        fill=hex_to_rgb(
            PRICE_TEXT_COLOR
        )
    )


# ============================================================
# SEPARAR ATRIBUTO
# ============================================================

def separar_atributo(
    texto
):

    texto = (
        str(
            texto
            or ""
        )
        .strip()
    )

    if not texto:

        return (
            "",
            ""
        )

    partes = (
        texto.split(
            maxsplit=1
        )
    )

    if (
        len(partes)
        == 1
    ):

        return (
            "",
            partes[0]
        )

    return (
        partes[0],
        partes[1]
    )


# ============================================================
# FEATURE BED / BATH
# ============================================================

def dibujar_feature(
    canvas,
    draw,
    icon,
    x,
    y,
    value_text,
    label_text
):

    font_valor = cargar_fuente(
        FONT_GARET_BOLD, # debe ser "Garet-Heavy.ttf"
        FONT_SIZE_BED_BATH_VALUE
    )

    font_label = cargar_fuente(
        FONT_GARET_BOLD,
        FONT_SIZE_BED_BATH_LABEL
    )

    fill = hex_to_rgb(
        BED_BATH_TEXT_COLOR
    )

    # ========================================================
    # ICONO
    # ========================================================

    icon_x = x

    icon_y = (
        y
        + FEATURE_ICON_Y_OFFSET
    )

    canvas.alpha_composite(
        icon,
        (
            int(icon_x),
            int(icon_y)
        )
    )

    # ========================================================
    # VALOR
    # ========================================================

    value_x = (
        x
        + BED_BATH_ICON_SIZE
        + FEATURE_ICON_VALUE_GAP
    )

    value_y = y + 1 # Editado por mí

    draw.text(
        (
            value_x,
            value_y
        ),
        str(value_text),
        font=font_valor,
        fill=fill
    )

    # ========================================================
    # LABEL
    # ========================================================

    value_bbox = draw.textbbox(
        (
            value_x,
            value_y
        ),
        str(value_text),
        font=font_valor
    )

    value_height = (
        value_bbox[3]
        - value_bbox[1]
    )

    # ========================================================
    # CASO ESPECIAL - STUDIO
    # ========================================================
    #
    # Cuando Bedroom = Studio:
    #
    # separar_atributo() devuelve:
    #
    # value_text = ""
    # label_text = "Studio"
    #
    # En este caso hacemos que Studio empiece
    # desde debajo del icono de cama y no
    # desde la posición normal del texto.
    #
    # ========================================================

    es_studio = (
        not str(
            value_text
        ).strip()
        and str(
            label_text
        ).strip().lower()
        == "studio"
    )

    if es_studio:

        label_x = x

        label_y = (
            y 
            - 3 # Editado por mí
            + BED_BATH_ICON_SIZE
            + FEATURE_VALUE_LABEL_GAP
        )

    else:

        label_x = value_x

        label_y = (
            value_y
            + value_height
            + FEATURE_VALUE_LABEL_GAP
        )

    draw.text(
        (
            label_x,
            label_y
        ),
        str(label_text),
        font=font_label,
        fill=fill
    )


# ============================================================
# BED / BATH
# ============================================================
#
# IZQUIERDA:
#
# BED | BATH | FOTO
#
# Bath queda junto a la foto.
#
#
# DERECHA:
#
# FOTO | BED | BATH
#
# Bed queda junto a la foto.
#
# ============================================================

def dibujar_bed_bath(
    canvas,
    draw,
    bedroom_text,
    bath_text,
    near_x,
    far_x,
    y,
    side
):

    # ========================================================
    # ICONOS
    # ========================================================

    bed_icon = (
        cargar_icono_png(
            BED_ICON_FILE,
            BED_BATH_ICON_SIZE
        )
    )

    bath_icon = (
        cargar_icono_png(
            BATH_ICON_FILE,
            BED_BATH_ICON_SIZE
        )
    )

    # ========================================================
    # DATOS
    # ========================================================

    bed_valor, bed_label = (
        separar_atributo(
            bedroom_text
        )
    )

    bath_valor, bath_label = (
        separar_atributo(
            bath_text
        )
    )

    # ========================================================
    # IZQUIERDA
    # ========================================================
    #
    # BED | BATH | FOTO
    #
    # far  = BED
    # near = BATH
    #
    # ========================================================

    if side == "left":

        # BED - lejos de la foto

        dibujar_feature(
            canvas=canvas,
            draw=draw,
            icon=bed_icon,
            x=far_x,
            y=y,
            value_text=bed_valor,
            label_text=bed_label
        )

        # BATH - cerca de la foto

        dibujar_feature(
            canvas=canvas,
            draw=draw,
            icon=bath_icon,
            x=near_x,
            y=y,
            value_text=bath_valor,
            label_text=bath_label
        )

        return

    # ========================================================
    # DERECHA
    # ========================================================
    #
    # FOTO | BED | BATH
    #
    # near = BED
    # far  = BATH
    #
    # ========================================================

    dibujar_feature(
        canvas=canvas,
        draw=draw,
        icon=bed_icon,
        x=near_x,
        y=y,
        value_text=bed_valor,
        label_text=bed_label
    )

    dibujar_feature(
        canvas=canvas,
        draw=draw,
        icon=bath_icon,
        x=far_x,
        y=y,
        value_text=bath_valor,
        label_text=bath_label
    )


# ============================================================
# RENTED
# ============================================================

def dibujar_rented_overlay(
    canvas,
    image_x,
    image_y
):

    overlay = (
        Image.new(
            "RGBA",
            (
                PROPERTY_IMAGE_WIDTH,
                PROPERTY_IMAGE_HEIGHT
            ),
            (
                0,
                0,
                0,
                0
            )
        )
    )

    draw = (
        ImageDraw.Draw(
            overlay
        )
    )

    font = (
        cargar_fuente(
            FONT_LEAGUE_SPARTAN_BOLD,
            FONT_SIZE_RENTED
        )
    )

    text_w, text_h = (
        medir_texto(
            draw,
            RENTED_TEXT,
            font
        )
    )

    text_x = (
        (
            PROPERTY_IMAGE_WIDTH
            - text_w
        )
        / 2
    )

    text_y = (
        (
            PROPERTY_IMAGE_HEIGHT
            - text_h
        )
        / 2
        - 4
    )

    draw.text(
        (
            text_x,
            text_y
        ),
        RENTED_TEXT,
        font=font,
        fill=hex_to_rgb(
            RENTED_TEXT_COLOR
        )
    )

    overlay = (
        overlay.rotate(
            RENTED_ANGLE,
            resample=
                Image.Resampling.BICUBIC,
            expand=False
        )
    )

    canvas.alpha_composite(
        overlay,
        (
            int(
                image_x
            ),
            int(
                image_y
            )
        )
    )


# ============================================================
# SLOT
# ============================================================

def obtener_slot(
    indice
):

    fila = (
        indice // 2
    )

    lado = (
        "left"
        if (
            indice % 2
            == 0
        )
        else "right"
    )

    base_y = (
        GRID_TOP
        + fila
        * (
            GRID_ROW_HEIGHT
            + GRID_ROW_GAP
        )
    )

    if (
        lado
        == "left"
    ):

        return {

            "side":
                "left",

            "base_x":
                GRID_LEFT_X,

            "base_y":
                base_y
        }

    return {

        "side":
            "right",

        "base_x":
            GRID_RIGHT_X,

        "base_y":
            base_y
    }

# ============================================================
# MIRROR HORIZONTAL
# ============================================================
#
# La IZQUIERDA es el diseño maestro.
#
# Esta función calcula automáticamente
# la posición equivalente del lado derecho.
#
# ============================================================

def mirror_x(
    x,
    element_width
):

    return (
        PROPERTY_CARD_WIDTH
        - x
        - element_width
    )


# ============================================================
# LAYOUT DEL CONTENEDOR
# ============================================================
#
# IMPORTANTE:
#
# La DERECHA es el layout maestro.
#
# La IZQUIERDA se calcula automáticamente
# haciendo MIRROR del layout derecho.
#
# Si mañana modificamos la derecha,
# la izquierda cambia automáticamente.
#
# ============================================================

# ============================================================
# LAYOUT DEL CONTENEDOR
# ============================================================
#
# IMPORTANTE:
#
# La IZQUIERDA es el layout MAESTRO.
#
# La DERECHA se calcula automáticamente
# haciendo MIRROR horizontal.
#
# Cualquier modificación en LEFT_...
# afectará automáticamente ambos lados.
#
# ============================================================

def obtener_layout_propiedad(
    side,
    base_x,
    base_y
):

    # ========================================================
    # LAYOUT MAESTRO - IZQUIERDA
    # ========================================================

    # --------------------------------------------------------
    # IMAGEN
    # --------------------------------------------------------

    left_image_x = (
        LEFT_IMAGE_X_OFFSET
    )

    left_image_y = (
        LEFT_IMAGE_Y_OFFSET
    )

    # --------------------------------------------------------
    # CONTENEDOR INFO
    # --------------------------------------------------------

    left_info_x = (
        LEFT_INFO_GROUP_X_OFFSET
    )

    left_info_y = (
        LEFT_INFO_GROUP_Y_OFFSET
    )

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    left_location_x = (
        left_info_x
        + LEFT_LOCATION_REL_X
    )

    left_location_y = (
        left_info_y
        + LEFT_LOCATION_REL_Y
    )

    # --------------------------------------------------------
    # FOR RENT
    # --------------------------------------------------------

    left_badge_x = (
        left_info_x
        + LEFT_BADGE_REL_X
    )

    left_badge_y = (
        left_info_y
        + LEFT_BADGE_REL_Y
    )

    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    left_price_x = (
        left_info_x
        + LEFT_PRICE_REL_X
    )

    left_price_y = (
        left_info_y
        + LEFT_PRICE_REL_Y
    )

    # --------------------------------------------------------
    # BED / BATH
    # --------------------------------------------------------
    #
    # IZQUIERDA:
    #
    # BED | BATH | FOTO
    #
    # far  = BED
    # near = BATH
    #
    # --------------------------------------------------------

    left_feature_far_x = (
        left_info_x
        + LEFT_FEATURE_FAR_REL_X
    )

    left_feature_near_x = (
        left_info_x
        + LEFT_FEATURE_NEAR_REL_X
    )

    left_feature_y = (
        left_info_y
        + LEFT_FEATURE_Y
    )

    # ========================================================
    # IZQUIERDA
    # ========================================================

    if side == "left":

        return {

            "image_x":
                base_x
                + left_image_x,

            "image_y":
                base_y
                + left_image_y,

            "location_x":
                base_x
                + left_location_x,

            "location_y":
                base_y
                + left_location_y,

            "location_max_width":
                LOCATION_MAX_WIDTH_LEFT,

            "location_align":
                "right",

            "badge_x":
                base_x
                + left_badge_x,

            "badge_y":
                base_y
                + left_badge_y,

            "price_x":
                base_x
                + left_price_x,

            "price_y":
                base_y
                + left_price_y,

            "feature_near_x":
                base_x
                + left_feature_near_x,

            "feature_far_x":
                base_x
                + left_feature_far_x,

            "feature_y":
                base_y
                + left_feature_y
        }

    # ========================================================
    # DERECHA - MIRROR AUTOMÁTICO
    # ========================================================

    # --------------------------------------------------------
    # IMAGEN
    # --------------------------------------------------------

    right_image_x = (
        mirror_x(
            left_image_x,
            PROPERTY_IMAGE_WIDTH
        )
    )

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    right_location_x = (
        mirror_x(
            left_location_x,
            LOCATION_MAX_WIDTH_LEFT
        )
    )

    # --------------------------------------------------------
    # FOR RENT
    # --------------------------------------------------------

    right_badge_x = (
        mirror_x(
            left_badge_x,
            FOR_RENT_BADGE_WIDTH
        )
    )

    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    right_price_x = (
        mirror_x(
            left_price_x,
            PRICE_BOX_WIDTH
        )
    )

    # --------------------------------------------------------
    # BED / BATH
    # --------------------------------------------------------
    #
    # IZQUIERDA:
    #
    # BED | BATH | FOTO
    #
    # se convierte automáticamente en:
    #
    # FOTO | BED | BATH
    #
    # --------------------------------------------------------

    right_feature_near_x = (
        mirror_x(
            left_feature_near_x,
            FEATURE_SLOT_WIDTH
        )
    )

    right_feature_far_x = (
        mirror_x(
            left_feature_far_x,
            FEATURE_SLOT_WIDTH
        )
    )

    # ========================================================
    # RETORNAR DERECHA
    # ========================================================

    return {

        "image_x":
            base_x
            + right_image_x,

        "image_y":
            base_y
            + left_image_y,

        "location_x":
            base_x
            + right_location_x,

        "location_y":
            base_y
            + left_location_y,

        "location_max_width":
            LOCATION_MAX_WIDTH_RIGHT,

        "location_align":
            "left",

        "badge_x":
            base_x
            + right_badge_x,

        "badge_y":
            base_y
            + left_badge_y,

        "price_x":
            base_x
            + right_price_x,

        "price_y":
            base_y
            + left_price_y,

        "feature_near_x":
        base_x
        + right_feature_near_x
        + RIGHT_DETAILS_OFFSET_X,

        "feature_far_x":
            base_x
            + right_feature_far_x
            + RIGHT_DETAILS_OFFSET_X,

        "feature_y":
            base_y
            + left_feature_y
            + RIGHT_DETAILS_OFFSET_Y
    }


# ============================================================
# DIBUJAR PROPIEDAD
# ============================================================

def dibujar_propiedad(
    canvas,
    fila,
    indice
):

    draw = (
        ImageDraw.Draw(
            canvas
        )
    )

    # ========================================================
    # SLOT
    # ========================================================

    slot = (
        obtener_slot(
            indice
        )
    )

    side = (
        slot[
            "side"
        ]
    )

    base_x = (
        slot[
            "base_x"
        ]
    )

    base_y = (
        slot[
            "base_y"
        ]
    )

    # ========================================================
    # LAYOUT
    # ========================================================

    layout = (
        obtener_layout_propiedad(
            side=side,
            base_x=base_x,
            base_y=base_y
        )
    )

    # ========================================================
    # DATOS
    # ========================================================

    display_location = (
        fila.get(
            "display_location",
            ""
        )
    )

    price_text = (
        fila.get(
            "price_text",
            ""
        )
    )

    bedroom_text = (
        fila.get(
            "bedroom_text",
            ""
        )
    )

    bath_text = (
        fila.get(
            "bath_text",
            ""
        )
    )

    image_url = (
        fila.get(
            "image_drive_url",
            ""
        )
    )

    listing_type = (
        str(
            fila.get(
                "listing_type",
                "current"
            )
        )
        .strip()
        .lower()
    )

    # ========================================================
    # IMAGEN
    # ========================================================

    imagen = (
        preparar_imagen_propiedad(
            image_url
        )
    )

    canvas.alpha_composite(
        imagen,
        (
            int(
                layout[
                    "image_x"
                ]
            ),
            int(
                layout[
                    "image_y"
                ]
            )
        )
    )

    # ========================================================
    # LOCATION
    # ========================================================

    dibujar_location(

        draw=draw,

        text=
            display_location,

        x=
            layout[
                "location_x"
            ],

        y=
            layout[
                "location_y"
            ],

        max_width=
            layout[
                "location_max_width"
            ],

        align=
            layout[
                "location_align"
            ]
    )

    # ========================================================
    # FOR RENT
    # ========================================================

    dibujar_badge_for_rent(
        canvas,
        draw,
        layout["badge_x"],
        layout["badge_y"]
    )

    # ========================================================
    # PRECIO
    # ========================================================

    dibujar_price_box(

        draw,

        price_text,

        layout[
            "price_x"
        ],

        layout[
            "price_y"
        ]
    )

    # ========================================================
    # BED / BATH
    # ========================================================

    dibujar_bed_bath(

        canvas=canvas,

        draw=draw,

        bedroom_text=
            bedroom_text,

        bath_text=
            bath_text,

        near_x=
            layout[
                "feature_near_x"
            ],

        far_x=
            layout[
                "feature_far_x"
            ],

        y=
            layout[
                "feature_y"
            ],

        side=
            side
    )

    # ========================================================
    # RENTED
    # ========================================================

    if (
        listing_type
        == "archived"
    ):

        dibujar_rented_overlay(

            canvas,

            layout[
                "image_x"
            ],

            layout[
                "image_y"
            ]
        )


# ============================================================
# GENERAR 1 FLYER
# ============================================================

def generar_flyer(
    grupo,
    numero
):

    flyer = (
        abrir_template()
    )

    grupo = (
        grupo.reset_index(
            drop=True
        )
    )

    for indice, (_, fila) in enumerate(
        grupo.iterrows()
    ):

        if (
            indice
            >= 10
        ):

            break

        dibujar_propiedad(
            canvas=flyer,
            fila=fila,
            indice=indice
        )

    archivo = (
        FLYERS_DIR
        /
        f"{FLYER_FILE_PREFIX}_"
        f"{numero:02d}.png"
    )

    flyer = (
        flyer.convert(
            "RGB"
        )
    )

    flyer.save(
        archivo,
        format=FLYER_FORMAT,
        quality=100
    )

    return archivo


# ============================================================
# LIMPIAR FLYERS ANTERIORES
# ============================================================
#
# Antes de generar una nueva tanda de flyers,
# eliminamos únicamente los PNG creados automáticamente
# por este proyecto.
#
# De esta forma, si anteriormente existían 3 flyers
# y ahora solo se necesitan 2, el flyer 03 anterior
# no quedará guardado por error.
#
# ============================================================

def limpiar_flyers_anteriores():

    archivos = (
        FLYERS_DIR.glob(
            f"{FLYER_FILE_PREFIX}_*.png"
        )
    )

    eliminados = 0

    for archivo in archivos:

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
# GENERAR TODOS
# ============================================================

def generar_flyers(
    grupos
):

    archivos = []

    # ========================================================
    # LIMPIAR FLYERS ANTERIORES
    # ========================================================

    eliminados = (
        limpiar_flyers_anteriores()
    )

    if eliminados > 0:

        print(
            f"\nFlyers anteriores eliminados: "
            f"{eliminados}"
        )

    # ========================================================
    # PREPARAR IMÁGENES
    # ========================================================

    preparar_imagenes_flyers(
        grupos
    )

    # ========================================================
    # GENERAR FLYERS
    # ========================================================

    for numero, grupo in enumerate(
        grupos,
        start=1
    ):

        archivo = (
            generar_flyer(
                grupo=grupo,
                numero=numero
            )
        )

        archivos.append(
            archivo
        )

    return archivos