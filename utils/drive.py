import re
import unicodedata

import pandas as pd

from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.discovery import build

from config.settings import (
    DRIVE_ROOT_FOLDER_ID,
    GOOGLE_DRIVE_SCOPES,
    GOOGLE_SERVICE_ACCOUNT_FILE,
    CURRENT_DRIVE_FILE,
    ARCHIVED_DRIVE_FILE,
    MAX_ARCHIVED_IMAGES,
    MAX_ARCHIVED_SEARCH_ATTEMPTS
)


FOLDER_MIME_TYPE = (
    "application/vnd.google-apps.folder"
)


# ============================================================
# NORMALIZACIÓN
# ============================================================

def normalizar_texto(texto):

    if texto is None:
        return ""

    texto = (
        str(texto)
        .strip()
        .lower()
    )

    # Quitar tildes

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        c
        for c in texto
        if not unicodedata.combining(c)
    )

    # Unificar símbolos

    texto = texto.replace(
        "&",
        "and"
    )

    # Eliminar espacios, comas, guiones,
    # puntos y caracteres especiales

    texto = re.sub(
        r"[^a-z0-9]",
        "",
        texto
    )

    return texto


# ============================================================
# CONECTAR GOOGLE DRIVE
# ============================================================

def conectar_drive():

    credentials = (
        Credentials.from_service_account_file(
            str(GOOGLE_SERVICE_ACCOUNT_FILE),
            scopes=GOOGLE_DRIVE_SCOPES
        )
    )

    drive = build(
        "drive",
        "v3",
        credentials=credentials
    )

    return drive


# ============================================================
# LISTAR CONTENIDO DE CARPETA
# ============================================================

def listar_carpeta(
    service,
    folder_id
):

    elementos = []

    page_token = None

    while True:

        resultado = (
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
                pageToken=page_token,
                pageSize=1000
            )
            .execute()
        )

        elementos.extend(
            resultado.get(
                "files",
                []
            )
        )

        page_token = (
            resultado.get(
                "nextPageToken"
            )
        )

        if not page_token:
            break

    return elementos


# ============================================================
# BUSCAR CARPETA EXACTA NORMALIZADA
# ============================================================

def buscar_carpeta(
    elementos,
    nombre
):

    nombre_normalizado = (
        normalizar_texto(
            nombre
        )
    )

    for elemento in elementos:

        if (
            elemento["mimeType"]
            != FOLDER_MIME_TYPE
        ):
            continue

        if (
            normalizar_texto(
                elemento["name"]
            )
            == nombre_normalizado
        ):

            return elemento

    return None


# ============================================================
# BUSCAR PRIMERA IMAGEN
# ============================================================

def buscar_primera_imagen(
    elementos
):

    imagenes = [

        elemento

        for elemento in elementos

        if (
            elemento
            .get(
                "mimeType",
                ""
            )
            .startswith(
                "image/"
            )
        )
    ]

    if not imagenes:

        return None

    # Orden estable por nombre

    imagenes.sort(
        key=lambda x:
        x["name"].lower()
    )

    return imagenes[0]


# ============================================================
# OBTENER INFORMACIÓN DRIVE DE UNA PROPIEDAD
# ============================================================

def obtener_info_propiedad(
    service,
    carpetas_location,
    location,
    property_name
):

    vacio = {
        "drive_property_folder_id": "",
        "image_drive_url": "",
        "image_name": ""
    }

    # --------------------------------------------------------
    # Buscar carpeta de Location
    # --------------------------------------------------------

    carpeta_location = (
        buscar_carpeta(
            carpetas_location,
            location
        )
    )

    if not carpeta_location:

        return vacio

    # --------------------------------------------------------
    # Listar propiedades dentro de Location
    # --------------------------------------------------------

    propiedades_drive = (
        listar_carpeta(
            service,
            carpeta_location["id"]
        )
    )

    # --------------------------------------------------------
    # Buscar property
    # --------------------------------------------------------

    carpeta_property = (
        buscar_carpeta(
            propiedades_drive,
            property_name
        )
    )

    if not carpeta_property:

        return vacio

    # --------------------------------------------------------
    # Buscar imágenes
    # --------------------------------------------------------

    contenido_property = (
        listar_carpeta(
            service,
            carpeta_property["id"]
        )
    )

    imagen = (
        buscar_primera_imagen(
            contenido_property
        )
    )

    if not imagen:

        return vacio

    # --------------------------------------------------------
    # Crear URL estable
    # --------------------------------------------------------

    image_drive_url = (
        "https://drive.google.com/file/d/"
        f'{imagen["id"]}'
        "/view"
    )

    return {

        "drive_property_folder_id":
            carpeta_property["id"],

        "image_drive_url":
            image_drive_url,

        "image_name":
            imagen["name"]
    }


# ============================================================
# CURRENT INVENTORY + DRIVE
# ============================================================

def procesar_current_drive(
    service,
    current
):

    print("\n" + "=" * 100)
    print("BUSCANDO IMÁGENES - CURRENT")
    print("=" * 100)

    carpetas_location = (
        listar_carpeta(
            service,
            DRIVE_ROOT_FOLDER_ID
        )
    )

    resultados = []

    total = len(current)

    for posicion, (_, fila) in enumerate(
        current.iterrows(),
        start=1
    ):

        property_name = (
            fila["property"]
        )

        location = (
            fila["Location"]
        )

        print(
            f"[{posicion}/{total}] "
            f"{location} -> "
            f"{property_name}"
        )

        info = (
            obtener_info_propiedad(
                service,
                carpetas_location,
                location,
                property_name
            )
        )

        if info["image_drive_url"]:

            print(
                "   ✓ Imagen encontrada"
            )

        else:

            print(
                "   - Sin imagen"
            )

        resultados.append(
            info
        )

    df_drive = pd.DataFrame(
        resultados
    )

    resultado = pd.concat(
        [
            current.reset_index(
                drop=True
            ),
            df_drive
        ],
        axis=1
    )

    # ========================================================
    # SOLO PROPIEDADES CON IMAGEN ENCONTRADA
    # ========================================================

    resultado = resultado[
        resultado["image_drive_url"]
        .fillna("")
        .ne("")
    ].copy()

    resultado.reset_index(
        drop=True,
        inplace=True
    )

    return resultado


# ============================================================
# ARCHIVED - SOLO 9 MÁS RECIENTES CON IMAGEN
# ============================================================

def procesar_archived_drive(
    service,
    archived
):

    print("\n" + "=" * 100)
    print("BUSCANDO PROPIEDADES RENTADAS RECIENTES CON IMAGEN")
    print("=" * 100)

    print(
        f"\nObjetivo de imágenes: "
        f"{MAX_ARCHIVED_IMAGES}"
    )

    print(
        f"Máximo de propiedades a revisar: "
        f"{MAX_ARCHIVED_SEARCH_ATTEMPTS}"
    )

    # ========================================================
    # LISTAR CARPETAS LOCATION
    # ========================================================

    carpetas_location = (
        listar_carpeta(
            service,
            DRIVE_ROOT_FOLDER_ID
        )
    )

    filas_encontradas = []

    intentos = 0

    # ========================================================
    # RECORRER ARCHIVED
    # ========================================================

    # archived ya debe venir ordenado por
    # Rented Date más reciente primero

    for _, fila in archived.iterrows():

        # ----------------------------------------------------
        # Ya conseguimos todas las imágenes necesarias
        # ----------------------------------------------------

        if (
            len(filas_encontradas)
            >= MAX_ARCHIVED_IMAGES
        ):
            break

        # ----------------------------------------------------
        # Ya alcanzamos el máximo de intentos
        # ----------------------------------------------------

        if (
            intentos
            >= MAX_ARCHIVED_SEARCH_ATTEMPTS
        ):
            break

        intentos += 1

        property_name = (
            fila["property"]
        )

        location = (
            fila["Location"]
        )

        rented_date = (
            fila["Rented Date"]
        )

        print(
            f"\nIntento "
            f"{intentos}/"
            f"{MAX_ARCHIVED_SEARCH_ATTEMPTS}"
        )

        print(
            f"Encontradas: "
            f"{len(filas_encontradas)}/"
            f"{MAX_ARCHIVED_IMAGES}"
        )

        print(
            f"{rented_date} | "
            f"{location} -> "
            f"{property_name}"
        )

        # ====================================================
        # BUSCAR EN DRIVE
        # ====================================================

        info = (
            obtener_info_propiedad(
                service,
                carpetas_location,
                location,
                property_name
            )
        )

        # ----------------------------------------------------
        # No hay imagen
        # ----------------------------------------------------

        if not info[
            "image_drive_url"
        ]:

            print(
                "   - No se encontró imagen"
            )

            continue

        # ----------------------------------------------------
        # Imagen encontrada
        # ----------------------------------------------------

        print(
            "   ✓ Imagen encontrada"
        )

        fila_final = (
            fila.to_dict()
        )

        fila_final.update(
            info
        )

        filas_encontradas.append(
            fila_final
        )

    # ========================================================
    # CREAR DATAFRAME
    # ========================================================

    resultado = pd.DataFrame(
        filas_encontradas
    )

    # ========================================================
    # RESUMEN
    # ========================================================

    print("\n" + "=" * 100)
    print("RESULTADO ARCHIVED")
    print("=" * 100)

    print(
        f"\nPropiedades revisadas: "
        f"{intentos}"
    )

    print(
        f"Imágenes encontradas: "
        f"{len(filas_encontradas)}"
    )

    print(
        f"Imágenes requeridas: "
        f"{MAX_ARCHIVED_IMAGES}"
    )

    # ========================================================
    # ADVERTENCIA
    # ========================================================

    if (
        len(filas_encontradas)
        < MAX_ARCHIVED_IMAGES
    ):

        faltantes = (
            MAX_ARCHIVED_IMAGES
            - len(filas_encontradas)
        )

        print("\n" + "!" * 100)

        print(
            "ADVERTENCIA:"
        )

        print(
            "No hay suficientes imágenes "
            "de propiedades rentadas en Google Drive."
        )

        print(
            f"Se encontraron "
            f"{len(filas_encontradas)} de "
            f"{MAX_ARCHIVED_IMAGES}."
        )

        print(
            f"Faltan {faltantes} imágenes."
        )

        print(
            "El usuario debe actualizar "
            "las carpetas o imágenes de Google Drive."
        )

        print(
            "!" * 100
        )

    else:

        print(
            "\n✓ Se encontraron suficientes "
            "imágenes Archived."
        )

    return resultado


# ============================================================
# GUARDAR
# ============================================================

def guardar_drive_datasets(
    current_drive,
    archived_drive
):

    current_drive.to_csv(
        CURRENT_DRIVE_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    archived_drive.to_csv(
        ARCHIVED_DRIVE_FILE,
        index=False,
        encoding="utf-8-sig"
    )