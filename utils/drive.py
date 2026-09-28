import re
import unicodedata

from googleapiclient.discovery import build

from config.settings import (
    GOOGLE_API_KEY,
    DRIVE_ROOT_FOLDER_ID
)


FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"


# ============================================================
# NORMALIZAR TEXTO
# ============================================================

def normalizar_texto(texto):

    if texto is None:
        return ""

    texto = str(texto).strip().lower()

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
        r"[^a-z0-9]",
        "",
        texto
    )

    return texto


# ============================================================
# CONECTAR DRIVE MEDIANTE API KEY
# ============================================================

def conectar_drive():

    return build(
        "drive",
        "v3",
        developerKey=GOOGLE_API_KEY
    )


# ============================================================
# LISTAR CONTENIDO DE UNA CARPETA
# ============================================================

def listar_carpeta(
    service,
    folder_id
):

    elementos = []

    page_token = None

    while True:

        respuesta = (
            service.files()
            .list(
                q=(
                    f"'{folder_id}' in parents "
                    "and trashed = false"
                ),
                fields=(
                    "nextPageToken,"
                    "files("
                    "id,"
                    "name,"
                    "mimeType"
                    ")"
                ),
                pageSize=1000,
                pageToken=page_token
            )
            .execute()
        )

        elementos.extend(
            respuesta.get(
                "files",
                []
            )
        )

        page_token = (
            respuesta.get(
                "nextPageToken"
            )
        )

        if not page_token:
            break

    return elementos


# ============================================================
# OBTENER CARPETAS LOCATION
# ============================================================

def obtener_carpetas_location(
    service
):

    elementos = listar_carpeta(
        service,
        DRIVE_ROOT_FOLDER_ID
    )

    return [
        elemento
        for elemento in elementos
        if elemento["mimeType"] == FOLDER_MIME_TYPE
    ]


# ============================================================
# OBTENER PRIMERA IMAGEN DE UNA PROPERTY
# ============================================================

def obtener_primera_imagen(
    service,
    property_folder_id
):

    elementos = listar_carpeta(
        service,
        property_folder_id
    )

    imagenes = [
        elemento
        for elemento in elementos
        if elemento
        .get("mimeType", "")
        .startswith("image/")
    ]

    if not imagenes:
        return None

    # Orden predecible
    imagenes.sort(
        key=lambda x: x["name"].lower()
    )

    return imagenes[0]