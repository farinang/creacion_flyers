import pandas as pd

from config.settings import (
    PROPERTIES_PER_FLYER,
    CURRENT_DRIVE_FILE,
    ARCHIVED_DRIVE_FILE
)

from utils.drive import (
    FOLDER_MIME_TYPE,
    normalizar_texto,
    listar_carpeta,
    obtener_carpetas_location,
    obtener_primera_imagen
)

# ============================================================
# CALCULAR ARCHIVED NECESARIOS
# ============================================================

def calcular_archived_necesarios(
    cantidad_current
):

    # Si no hay Current,
    # no generamos flyer únicamente con Archived

    if cantidad_current == 0:
        return 0

    resto = (
        cantidad_current
        % PROPERTIES_PER_FLYER
    )

    # Si es múltiplo exacto de 10
    if resto == 0:
        return 0

    return (
        PROPERTIES_PER_FLYER
        - resto
    )

# ============================================================
# CONSTRUIR ÍNDICE COMPLETO DE DRIVE
# ============================================================

def construir_indice_drive(
    service
):

    print("\n" + "=" * 100)
    print("CONSTRUYENDO ÍNDICE TEMPORAL DE GOOGLE DRIVE")
    print("=" * 100)

    registros = []

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    carpetas_location = (
        obtener_carpetas_location(
            service
        )
    )

    print(
        f"\nLocations encontradas en Drive: "
        f"{len(carpetas_location)}"
    )

    for numero_location, carpeta_location in enumerate(
        carpetas_location,
        start=1
    ):

        location_name = (
            carpeta_location["name"]
        )

        print(
            f"\n[{numero_location}/"
            f"{len(carpetas_location)}] "
            f"Location: {location_name}"
        )

        # ----------------------------------------------------
        # PROPERTIES DENTRO DE LOCATION
        # ----------------------------------------------------

        elementos_location = (
            listar_carpeta(
                service,
                carpeta_location["id"]
            )
        )

        carpetas_property = [
            elemento
            for elemento in elementos_location
            if (
                elemento["mimeType"]
                == FOLDER_MIME_TYPE
            )
        ]

        print(
            f"   Properties: "
            f"{len(carpetas_property)}"
        )

        for carpeta_property in carpetas_property:

            property_name = (
                carpeta_property["name"]
            )

            # ------------------------------------------------
            # PRIMERA IMAGEN
            # ------------------------------------------------

            imagen = (
                obtener_primera_imagen(
                    service,
                    carpeta_property["id"]
                )
            )

            # Si la property no tiene imagen,
            # no nos interesa para los flyers.
            if not imagen:
                continue

            image_drive_url = (
                "https://drive.google.com/file/d/"
                f'{imagen["id"]}/view'
            )

            registros.append(
                {
                    "location_drive":
                        location_name,

                    "property_drive":
                        property_name,

                    "location_norm":
                        normalizar_texto(
                            location_name
                        ),

                    "property_norm":
                        normalizar_texto(
                            property_name
                        ),

                    "drive_property_folder_id":
                        carpeta_property["id"],

                    "image_drive_url":
                        image_drive_url,

                    "image_name":
                        imagen["name"]
                }
            )

    df_drive = pd.DataFrame(
        registros
    )

    print("\n" + "=" * 100)
    print("ÍNDICE DRIVE TERMINADO")
    print("=" * 100)

    print(
        f"Propiedades con imagen detectadas: "
        f"{len(df_drive)}"
    )

    return df_drive


# ============================================================
# PREPARAR DATAFRAME MONDAY PARA MATCH
# ============================================================

def agregar_columnas_normalizadas(
    df
):

    df = df.copy()

    df["location_norm"] = (
        df["Location"]
        .fillna("")
        .apply(
            normalizar_texto
        )
    )

    df["property_norm"] = (
        df["property"]
        .fillna("")
        .apply(
            normalizar_texto
        )
    )

    return df


# ============================================================
# MATCH CURRENT
# ============================================================

def match_current_drive(
    current,
    drive_index
):

    print("\n" + "=" * 100)
    print("MATCH CURRENT ↔ DRIVE")
    print("=" * 100)

    current_match = (
        agregar_columnas_normalizadas(
            current
        )
    )

    resultado = (
        current_match.merge(
            drive_index,
            on=[
                "location_norm",
                "property_norm"
            ],
            how="left"
        )
    )

    # --------------------------------------------------------
    # SOLO ÉXITOS
    # --------------------------------------------------------

    resultado = resultado[
        resultado[
            "image_drive_url"
        ]
        .fillna("")
        .ne("")
    ].copy()

    # --------------------------------------------------------
    # QUITAR COLUMNAS TEMPORALES
    # --------------------------------------------------------

    columnas_eliminar = [
        "location_norm",
        "property_norm",
        "location_drive",
        "property_drive"
    ]

    resultado = resultado.drop(
        columns=[
            columna
            for columna in columnas_eliminar
            if columna in resultado.columns
        ]
    )

    resultado.reset_index(
        drop=True,
        inplace=True
    )

    print(
        f"\nCurrent totales: "
        f"{len(current)}"
    )

    print(
        f"Current con imagen: "
        f"{len(resultado)}"
    )

    print(
        f"Current sin imagen: "
        f"{len(current) - len(resultado)}"
    )

    return resultado


# ============================================================
# MATCH ARCHIVED
# ============================================================

def match_archived_drive(
    archived,
    drive_index,
    cantidad_requerida
):

    print("\n" + "=" * 100)
    print("MATCH ARCHIVED ↔ DRIVE")
    print("=" * 100)

    # ========================================================
    # SI NO SE NECESITAN ARCHIVED
    # ========================================================

    if cantidad_requerida == 0:

        print(
            "\nNo se requieren propiedades Archived "
            "para completar el último flyer."
        )

        return pd.DataFrame()

    # ========================================================
    # NORMALIZAR COLUMNAS PARA HACER MATCH
    # ========================================================

    archived_match = (
        agregar_columnas_normalizadas(
            archived
        )
    )

    # ========================================================
    # MERGE CON EL ÍNDICE COMPLETO DE DRIVE
    # ========================================================

    resultado = (
        archived_match.merge(
            drive_index,
            on=[
                "location_norm",
                "property_norm"
            ],
            how="left"
        )
    )

    # ========================================================
    # SOLO PROPIEDADES QUE TIENEN IMAGEN EN DRIVE
    # ========================================================

    resultado = resultado[
        resultado[
            "image_drive_url"
        ]
        .fillna("")
        .ne("")
    ].copy()

    # ========================================================
    # SOLO PROPIEDADES REALMENTE RENTADAS
    # ========================================================

    rented_normalizado = (
        resultado["Rented"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    RENTED_VALIDOS = {
        "by us",
        "not by us"
    }

    resultado = resultado[
        rented_normalizado.isin(
            RENTED_VALIDOS
        )
    ].copy()

    # ========================================================
    # PREPARAR FECHAS PARA ORDEN
    # ========================================================

    resultado[
        "_rented_date_sort"
    ] = pd.to_datetime(
        resultado["Rented Date"],
        errors="coerce"
    )

    resultado[
        "_last_updated_sort"
    ] = pd.to_datetime(
        resultado["Last updated"],
        errors="coerce"
    )

    # Indica cuáles sí tienen Rented Date

    resultado[
        "_tiene_rented_date"
    ] = (
        resultado[
            "_rented_date_sort"
        ]
        .notna()
    )

    # ========================================================
    # ORDEN
    #
    # 1. Primero las que sí tienen Rented Date
    # 2. Rented Date más reciente
    # 3. Si no tiene Rented Date, usar Last updated
    # ========================================================

    resultado = (
        resultado.sort_values(
            by=[
                "_tiene_rented_date",
                "_rented_date_sort",
                "_last_updated_sort"
            ],
            ascending=[
                False,
                False,
                False
            ],
            kind="stable"
        )
    )

    # ========================================================
    # IDENTIFICAR CASOS SIN RENTED DATE
    # ========================================================

    sin_rented_date = resultado[
        resultado[
            "_rented_date_sort"
        ].isna()
    ].copy()

    if not sin_rented_date.empty:

        print(
            "\nPropiedades rentadas con imagen "
            "pero sin Rented Date:"
        )

        for _, fila in (
            sin_rented_date.iterrows()
        ):

            print(
                f"- {fila['property']} "
                f"| Rented: {fila['Rented']} "
                f"| Last updated: "
                f"{fila['Last updated']}"
            )

        print(
            "\nEstas propiedades no se eliminan. "
            "Last updated se utiliza únicamente "
            "como criterio auxiliar de orden."
        )

    # ========================================================
    # TOMAR SOLO LA CANTIDAD NECESARIA
    # ========================================================

    seleccionadas = (
        resultado.head(
            cantidad_requerida
        )
        .copy()
    )

    cantidad_encontrada = (
        len(seleccionadas)
    )

    # ========================================================
    # RANGO DE RENTED DATE REAL
    # ========================================================

    fechas_validas = (
        seleccionadas[
            "_rented_date_sort"
        ]
        .dropna()
    )

    if not fechas_validas.empty:

        fecha_mas_reciente = (
            fechas_validas.max()
        )

        fecha_mas_antigua = (
            fechas_validas.min()
        )

        fecha_inicio = (
            fecha_mas_antigua
            .strftime("%Y-%m-%d")
        )

        fecha_fin = (
            fecha_mas_reciente
            .strftime("%Y-%m-%d")
        )

    else:

        fecha_inicio = "-"
        fecha_fin = "-"

    # ========================================================
    # CUÁNTAS SELECCIONADAS NO TIENEN RENTED DATE
    # ========================================================

    seleccionadas_sin_fecha = (
        seleccionadas[
            "_rented_date_sort"
        ]
        .isna()
        .sum()
    )

    # ========================================================
    # LIMPIAR COLUMNAS TEMPORALES
    # ========================================================

    columnas_temporales = [
        "location_norm",
        "property_norm",
        "location_drive",
        "property_drive",
        "_rented_date_sort",
        "_last_updated_sort",
        "_tiene_rented_date"
    ]

    seleccionadas = (
        seleccionadas.drop(
            columns=[
                columna
                for columna
                in columnas_temporales
                if columna
                in seleccionadas.columns
            ]
        )
    )

    seleccionadas.reset_index(
        drop=True,
        inplace=True
    )

    # ========================================================
    # RESUMEN
    # ========================================================

    print(
        f"\nMínimo de imágenes Archived "
        f"requeridas: "
        f"{cantidad_requerida}"
    )

    print(
        f"Imágenes Archived encontradas: "
        f"{cantidad_encontrada}"
    )

    print(
        f"Rango de Rented Date válido: "
        f"{fecha_inicio} a {fecha_fin}"
    )

    if seleccionadas_sin_fecha > 0:

        print(
            f"Propiedades seleccionadas sin "
            f"Rented Date: "
            f"{seleccionadas_sin_fecha}"
        )

    # ========================================================
    # WARNING SI NO ALCANZA
    # ========================================================

    if (
        cantidad_encontrada
        < cantidad_requerida
    ):

        faltantes = (
            cantidad_requerida
            - cantidad_encontrada
        )

        print("\n" + "!" * 100)

        print(
            "WARNING: "
            "NO HAY SUFICIENTES IMÁGENES "
            "DE PROPIEDADES RENTADAS"
        )

        print(
            f"Requeridas: "
            f"{cantidad_requerida}"
        )

        print(
            f"Encontradas: "
            f"{cantidad_encontrada}"
        )

        print(
            f"Faltantes: "
            f"{faltantes}"
        )

        print(
            "El usuario debe actualizar "
            "Monday o Google Drive."
        )

        print(
            "!" * 100
        )

    else:

        print(
            "\n✓ Hay suficientes propiedades "
            "Archived con imagen para completar "
            "el último flyer."
        )

    return seleccionadas


# ============================================================
# GUARDAR RESULTADOS
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

# ============================================================
# AUDITAR PROPIEDADES DE DRIVE NO UTILIZADAS
# ============================================================

def auditar_drive_no_utilizado(
    drive_index,
    current,
    archived
):

    print("\n" + "=" * 100)
    print("AUDITORÍA DE PROPIEDADES DRIVE")
    print("=" * 100)

    # ========================================================
    # NORMALIZAR CURRENT
    # ========================================================

    current_norm = (
        agregar_columnas_normalizadas(
            current
        )
    )

    # ========================================================
    # NORMALIZAR ARCHIVED
    # ========================================================

    archived_norm = (
        agregar_columnas_normalizadas(
            archived
        )
    )

    # ========================================================
    # KEYS CURRENT
    # ========================================================

    current_keys = set(
        zip(
            current_norm["location_norm"],
            current_norm["property_norm"]
        )
    )

    # ========================================================
    # KEYS ARCHIVED
    # ========================================================

    archived_keys = set(
        zip(
            archived_norm["location_norm"],
            archived_norm["property_norm"]
        )
    )

    # ========================================================
    # RECORRER TODO DRIVE
    # ========================================================

    resultados = []

    for _, fila_drive in drive_index.iterrows():

        key = (
            fila_drive["location_norm"],
            fila_drive["property_norm"]
        )

        # ----------------------------------------------------
        # MATCH CURRENT
        # ----------------------------------------------------

        if key in current_keys:

            estado = "CURRENT"

            resultados.append(
                {
                    "location_drive":
                        fila_drive["location_drive"],

                    "property_drive":
                        fila_drive["property_drive"],

                    "estado":
                        estado,

                    "detalle":
                        "Coincide con Current"
                }
            )

            continue

        # ----------------------------------------------------
        # MATCH ARCHIVED
        # ----------------------------------------------------

        if key in archived_keys:

            coincidencias = archived_norm[
                (
                    archived_norm["location_norm"]
                    == fila_drive["location_norm"]
                )
                &
                (
                    archived_norm["property_norm"]
                    == fila_drive["property_norm"]
                )
            ]

            if not coincidencias.empty:

                fila_archived = (
                    coincidencias.iloc[0]
                )

                rented = str(
                    fila_archived.get(
                        "Rented",
                        ""
                    )
                ).strip()

                rented_date = str(
                    fila_archived.get(
                        "Rented Date",
                        ""
                    )
                ).strip()

                phase = str(
                    fila_archived.get(
                        "Phase",
                        ""
                    )
                ).strip()

                rented_normalizado = (
                    rented.lower()
                )

                if rented_normalizado in {
                    "by us",
                    "not by us"
                }:

                    estado = (
                        "ARCHIVED_ELEGIBLE"
                    )

                    detalle = (
                        f"Rented={rented} | "
                        f"Rented Date={rented_date}"
                    )

                else:

                    estado = (
                        "ARCHIVED_NO_ELEGIBLE"
                    )

                    detalle = (
                        f"Phase={phase} | "
                        f"Rented={rented} | "
                        f"Rented Date={rented_date}"
                    )

                resultados.append(
                    {
                        "location_drive":
                            fila_drive["location_drive"],

                        "property_drive":
                            fila_drive["property_drive"],

                        "estado":
                            estado,

                        "detalle":
                            detalle
                    }
                )

                continue

        # ----------------------------------------------------
        # NO COINCIDE NI CURRENT NI ARCHIVED
        # ----------------------------------------------------

        resultados.append(
            {
                "location_drive":
                    fila_drive["location_drive"],

                "property_drive":
                    fila_drive["property_drive"],

                "estado":
                    "SIN_MATCH_MONDAY",

                "detalle":
                    "No coincide con Current ni Archived"
            }
        )

    # ========================================================
    # DATAFRAME
    # ========================================================

    auditoria = pd.DataFrame(
        resultados
    )

    # ========================================================
    # RESUMEN
    # ========================================================

    if auditoria.empty:

        print(
            "\nNo hay propiedades "
            "para auditar."
        )

        return auditoria

    resumen = (
        auditoria[
            "estado"
        ]
        .value_counts()
    )

    print("\nResumen:\n")

    for estado, cantidad in resumen.items():

        print(
            f"{estado}: "
            f"{cantidad}"
        )

    # ========================================================
    # MOSTRAR LAS QUE NO SON CURRENT
    # NI ARCHIVED ELEGIBLE
    # ========================================================

    problemas = auditoria[
        ~auditoria["estado"].isin(
            [
                "CURRENT",
                "ARCHIVED_ELEGIBLE"
            ]
        )
    ].copy()

    if not problemas.empty:

        print(
            "\nPropiedades de Drive "
            "que NO se están utilizando:\n"
        )

        for _, fila in problemas.iterrows():

            print(
                f'- {fila["property_drive"]}'
            )

            print(
                f'  Location: '
                f'{fila["location_drive"]}'
            )

            print(
                f'  Estado: '
                f'{fila["estado"]}'
            )

            print(
                f'  Detalle: '
                f'{fila["detalle"]}'
            )

            print()

    return auditoria