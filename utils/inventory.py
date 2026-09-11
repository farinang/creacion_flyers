import pandas as pd

from config.settings import (
    MONDAY_COLUMNS,
    OUTPUT_COLUMNS,
    CURRENT_INVENTORY_FILE,
    ARCHIVED_INVENTORY_FILE,
    PHASE_CURRENT,
    PHASE_ARCHIVED
)


# ============================================================
# CREAR DATAFRAME
# ============================================================

def crear_dataframe(items):

    registros = []

    id_a_nombre = {

        column_id: nombre

        for nombre, column_id
        in MONDAY_COLUMNS.items()
    }

    for item in items:

        registro = {
            "property": item["name"]
        }

        for nombre in MONDAY_COLUMNS:

            registro[nombre] = ""

        for valor in item[
            "column_values"
        ]:

            column_id = valor["id"]

            if column_id not in id_a_nombre:
                continue

            nombre = (
                id_a_nombre[
                    column_id
                ]
            )

            registro[nombre] = (
                valor.get("text")
                or ""
            )

        registros.append(
            registro
        )

    df = pd.DataFrame(
        registros
    )

    return df[
        OUTPUT_COLUMNS
    ]


# ============================================================
# ORDENAR CURRENT POR CANTIDAD DE LOCATION
# ============================================================

def ordenar_por_location(df):

    df = df.copy()

    df["Location"] = (
        df["Location"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    cantidades = (
        df["Location"]
        .value_counts()
    )

    df["_cantidad_location"] = (
        df["Location"]
        .map(cantidades)
    )

    df = df.sort_values(
        by=[
            "_cantidad_location",
            "Location",
            "property"
        ],
        ascending=[
            False,
            True,
            True
        ]
    )

    df = df.drop(
        columns=[
            "_cantidad_location"
        ]
    )

    return df.reset_index(
        drop=True
    )


# ============================================================
# ORDENAR ARCHIVED POR FECHA DE RENTA
# ============================================================

def ordenar_archived_por_fecha(df):

    df = df.copy()

    # --------------------------------------------------------
    # Convertir Rented Date a datetime solo temporalmente
    # --------------------------------------------------------

    df["_rented_date_sort"] = (
        pd.to_datetime(
            df["Rented Date"],
            errors="coerce"
        )
    )

    # --------------------------------------------------------
    # Eliminar propiedades sin fecha de renta
    # --------------------------------------------------------

    df = df[
        df["_rented_date_sort"].notna()
    ].copy()

    # --------------------------------------------------------
    # Más reciente primero
    # --------------------------------------------------------

    df = df.sort_values(
        by="_rented_date_sort",
        ascending=False
    )

    df = df.drop(
        columns=[
            "_rented_date_sort"
        ]
    )

    return df.reset_index(
        drop=True
    )


# ============================================================
# SEPARAR INVENTARIOS
# ============================================================

def separar_inventarios(df):

    phase = (
        df["Phase"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    current = df[
        phase.eq(
            PHASE_CURRENT
        )
    ].copy()

    archived = df[
        phase.eq(
            PHASE_ARCHIVED
        )
    ].copy()

    # Current:
    # Location con más propiedades primero

    current = (
        ordenar_por_location(
            current
        )
    )

    # Archived:
    # renta más reciente primero

    archived = (
        ordenar_archived_por_fecha(
            archived
        )
    )

    return (
        current,
        archived
    )


# ============================================================
# GUARDAR
# ============================================================

def guardar_inventarios(
    current,
    archived
):

    current.to_csv(
        CURRENT_INVENTORY_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    archived.to_csv(
        ARCHIVED_INVENTORY_FILE,
        index=False,
        encoding="utf-8-sig"
    )