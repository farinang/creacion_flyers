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
            "property":
                item["name"]
        }

        for nombre in (
            MONDAY_COLUMNS.keys()
        ):

            registro[
                nombre
            ] = ""

        for valor in item[
            "column_values"
        ]:

            column_id = (
                valor["id"]
            )

            if (
                column_id
                not in id_a_nombre
            ):
                continue

            nombre = (
                id_a_nombre[
                    column_id
                ]
            )

            registro[
                nombre
            ] = (
                valor.get(
                    "text"
                )
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
# ORDEN CURRENT POR LOCATION
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
        .map(
            cantidades
        )
    )

    df = (
        df.sort_values(
            by=[
                "_cantidad_location",
                "Location"
            ],
            ascending=[
                False,
                True
            ],
            kind="stable"
        )
    )

    df = df.drop(
        columns=[
            "_cantidad_location"
        ]
    )

    return (
        df.reset_index(
            drop=True
        )
    )


# ============================================================
# ARCHIVED MAS RECIENTE
# ============================================================

def ordenar_archived_por_fecha(df):

    df = df.copy()

    # ========================================================
    # CONVERTIR FECHAS
    # ========================================================

    df["_rented_date_sort"] = pd.to_datetime(
        df["Rented Date"],
        errors="coerce"
    )

    df["_last_updated_sort"] = pd.to_datetime(
        df["Last updated"],
        errors="coerce"
    )

    # ========================================================
    # INDICAR SI TIENE RENTED DATE
    # ========================================================

    df["_tiene_rented_date"] = (
        df["_rented_date_sort"]
        .notna()
    )

    # ========================================================
    # ORDEN
    #
    # 1. Primero propiedades CON Rented Date
    # 2. Rented Date más reciente primero
    # 3. Las que no tienen fecha se ordenan por Last updated
    # ========================================================

    df = df.sort_values(
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

    # ========================================================
    # QUITAR COLUMNAS TEMPORALES
    # ========================================================

    df = df.drop(
        columns=[
            "_rented_date_sort",
            "_last_updated_sort",
            "_tiene_rented_date"
        ]
    )

    return df.reset_index(
        drop=True
    )

# ============================================================
# SEPARAR
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

    current = (
        ordenar_por_location(
            current
        )
    )

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