import requests
import pandas as pd


# ============================================================
# CONFIGURACIÓN
# ============================================================

TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjcwMTgyNTg4MywiYWFpIjoxMSwidWlkIjoxMTUwNDUwNDUsImlhZCI6IjIwMjYtMDktMDhUMjE6NTk6MzUuMDAwWiIsInBlciI6Im1lOndyaXRlIiwiYWN0aWQiOjMxMzI4NTkwLCJyZ24iOiJ1c2UxIn0.H6mFyP0V346H2px3Rwd4PTuMsULpFQlk1_HR9pxgjXw"
BOARD_ID = 18415696704

URL = "https://api.monday.com/v2"

HEADERS = {
    "Authorization": TOKEN,
    "Content-Type": "application/json"
}


# ============================================================
# COLUMNAS QUE QUEREMOS UTILIZAR
# ============================================================

COLUMN_IDS = {

    "Bedroom": "color_mm3xssw2",

    "Bath": "color_mm3xmjhf",

    "Phase": "color_mm3xxfy2",

    "Price": "numeric_mm3xnfb9",

    "Date Listed": "date_mm6t5jrt",

    "Reminder Date": "date_mm5am4jg",

    # Status principal del Inventory
    "Status": "status",

    "Assigned": "multiple_person_mm3x4ht9",

    "Access": "text_mm3x50vh",

    "Vacancy date": "date_mm5avryw",

    "Details": "text_mm3xc81j",

    "Location": "color_mm3x1k0s",

    "Rented": "color_mm3xb3a0",

    "Rented Date": "date_mm5akp4q",

    "Last updated": "pulse_updated_mm5836zb"
}


# ============================================================
# ORDEN DE COLUMNAS EN LOS CSV
# ============================================================

COLUMNAS_SALIDA = [

    "property",
    "Status",
    "Assigned",
    "Bedroom",
    "Bath",
    "Price",
    "Date Listed",
    "Reminder Date",
    "Access",
    "Vacancy date",
    "Details",
    "Phase",
    "Location",
    "Rented",
    "Rented Date",
    "Last updated"
]


# ============================================================
# CONSULTA GENERAL A MONDAY
# ============================================================

def consultar_monday(query, variables=None):

    response = requests.post(
        URL,
        json={
            "query": query,
            "variables": variables or {}
        },
        headers=HEADERS
    )

    print("Status:", response.status_code)

    if response.status_code != 200:

        print(response.text)

        raise Exception(
            f"Error HTTP {response.status_code}"
        )

    resultado = response.json()

    if "errors" in resultado:

        print(resultado["errors"])

        raise Exception(
            resultado["errors"]
        )

    return resultado["data"]


# ============================================================
# DETECTAR TODAS LAS COLUMNAS DISPONIBLES
# ============================================================

def obtener_columnas():

    query = """
    query ($board_id: [ID!]) {

      boards(ids: $board_id) {

        id
        name

        columns {
          id
          title
          type
        }
      }
    }
    """

    data = consultar_monday(
        query,
        {
            "board_id": [
                str(BOARD_ID)
            ]
        }
    )

    board = data["boards"][0]

    print("\n" + "=" * 100)
    print("BOARD")
    print("=" * 100)

    print(board["name"])

    print("\n" + "=" * 100)
    print("TODAS LAS COLUMNAS DISPONIBLES")
    print("=" * 100)

    for columna in board["columns"]:

        print(
            f'{columna["title"]:<25} '
            f'{columna["id"]:<35} '
            f'[{columna["type"]}]'
        )

    print(
        f"\nTotal de columnas disponibles: "
        f"{len(board['columns'])}"
    )

    return board["columns"]


# ============================================================
# PRIMERA PÁGINA DE ITEMS
# ============================================================

def obtener_primera_pagina():

    query = """
    query ($board_id: [ID!]) {

      boards(ids: $board_id) {

        items_page(limit: 100) {

          cursor

          items {

            id
            name

            group {
              id
              title
            }

            column_values {
              id
              text
              value
              type
            }
          }
        }
      }
    }
    """

    data = consultar_monday(
        query,
        {
            "board_id": [
                str(BOARD_ID)
            ]
        }
    )

    return data["boards"][0]["items_page"]


# ============================================================
# SIGUIENTES PÁGINAS
# ============================================================

def obtener_siguiente_pagina(cursor):

    query = """
    query ($cursor: String!) {

      next_items_page(
        cursor: $cursor
        limit: 100
      ) {

        cursor

        items {

          id
          name

          group {
            id
            title
          }

          column_values {
            id
            text
            value
            type
          }
        }
      }
    }
    """

    data = consultar_monday(
        query,
        {
            "cursor": cursor
        }
    )

    return data["next_items_page"]


# ============================================================
# OBTENER TODOS LOS ITEMS DEL BOARD
# ============================================================

def obtener_todos_los_items():

    items = []

    # Primera página
    pagina = obtener_primera_pagina()

    items.extend(
        pagina["items"]
    )

    cursor = pagina["cursor"]

    print(
        f"\nItems descargados: "
        f"{len(items)}"
    )

    # Páginas siguientes
    while cursor:

        pagina = obtener_siguiente_pagina(
            cursor
        )

        items.extend(
            pagina["items"]
        )

        cursor = pagina["cursor"]

        print(
            f"Items descargados: "
            f"{len(items)}"
        )

    return items


# ============================================================
# CREAR DATAFRAME
# ============================================================

def crear_dataframe(items):

    registros = []

    # --------------------------------------------------------
    # Convertimos:
    #
    # status -> Status
    # color_mm3xxfy2 -> Phase
    # numeric_mm3xnfb9 -> Price
    # etc.
    # --------------------------------------------------------

    id_a_nombre = {

        column_id: nombre

        for nombre, column_id
        in COLUMN_IDS.items()
    }

    # --------------------------------------------------------
    # RECORRER ITEMS
    # --------------------------------------------------------

    for item in items:

        # ----------------------------------------------------
        # Crear registro vacío
        # ----------------------------------------------------

        registro = {
            "property": item["name"]
        }

        # Crear todas las columnas seleccionadas
        for nombre in COLUMN_IDS.keys():

            registro[nombre] = ""

        # ----------------------------------------------------
        # Leer valores devueltos por Monday
        # ----------------------------------------------------

        for valor in item["column_values"]:

            column_id = valor["id"]

            # Ignorar columnas que no necesitamos
            if column_id not in id_a_nombre:
                continue

            nombre_columna = (
                id_a_nombre[column_id]
            )

            texto = valor.get("text")

            if texto is None:
                texto = ""

            registro[
                nombre_columna
            ] = texto

        registros.append(
            registro
        )

    # ========================================================
    # CREAR DATAFRAME
    # ========================================================

    df = pd.DataFrame(
        registros
    )

    # --------------------------------------------------------
    # Ordenar columnas exactamente como queremos
    # --------------------------------------------------------

    df = df[
        COLUMNAS_SALIDA
    ]

    return df


# ============================================================
# MOSTRAR PHASES DISPONIBLES
# ============================================================

def mostrar_phases(df):

    print("\n" + "=" * 100)
    print("PHASES ENCONTRADOS")
    print("=" * 100)

    conteo = (
        df["Phase"]
        .fillna("")
        .astype(str)
        .str.strip()
        .value_counts(
            dropna=False
        )
    )

    print(conteo)


# ============================================================
# SEPARAR CURRENT Y ARCHIVED
# ============================================================

def separar_inventarios(df):

    print("\n" + "=" * 100)
    print("SEPARANDO INVENTARIOS")
    print("=" * 100)

    # --------------------------------------------------------
    # CURRENT INVENTORY
    # --------------------------------------------------------

    current = df[
        df["Phase"]
        .fillna("")
        .astype(str)
        .str.strip()
        .eq("Current")
    ].copy()

    # --------------------------------------------------------
    # ARCHIVED INVENTORY
    # --------------------------------------------------------

    archived = df[
        df["Phase"]
        .fillna("")
        .astype(str)
        .str.strip()
        .eq("Archived")
    ].copy()

    # Reiniciar índices
    current.reset_index(
        drop=True,
        inplace=True
    )

    archived.reset_index(
        drop=True,
        inplace=True
    )

    return current, archived


# ============================================================
# GUARDAR CSV
# ============================================================

def guardar_csv(
    current,
    archived
):

    archivo_current = (
        "current_inventory.csv"
    )

    archivo_archived = (
        "archived_inventory.csv"
    )

    # Current
    current.to_csv(
        archivo_current,
        index=False,
        encoding="utf-8-sig"
    )

    # Archived
    archived.to_csv(
        archivo_archived,
        index=False,
        encoding="utf-8-sig"
    )

    return (
        archivo_current,
        archivo_archived
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 100)
    print("CONSULTANDO INVENTORY 2.0")
    print("=" * 100)

    # ========================================================
    # 1. DETECTAR TODAS LAS COLUMNAS
    # ========================================================

    obtener_columnas()

    # ========================================================
    # 2. DESCARGAR TODOS LOS ITEMS
    # ========================================================

    items = obtener_todos_los_items()

    # ========================================================
    # 3. CREAR DATAFRAME
    # ========================================================

    df = crear_dataframe(
        items
    )

    # ========================================================
    # 4. MOSTRAR PHASES
    # ========================================================

    mostrar_phases(
        df
    )

    # ========================================================
    # 5. SEPARAR CURRENT Y ARCHIVED
    # ========================================================

    current, archived = (
        separar_inventarios(
            df
        )
    )

    # ========================================================
    # 6. GUARDAR CSV
    # ========================================================

    archivo_current, archivo_archived = (
        guardar_csv(
            current,
            archived
        )
    )

    # ========================================================
    # RESUMEN
    # ========================================================

    print("\n" + "=" * 100)
    print("RESUMEN")
    print("=" * 100)

    print(
        f"\nTotal items descargados: "
        f"{len(df)}"
    )

    print(
        f"Current Inventory: "
        f"{len(current)}"
    )

    print(
        f"Archived Inventory: "
        f"{len(archived)}"
    )

    print("\nColumnas guardadas:")

    for columna in COLUMNAS_SALIDA:

        print(
            f"- {columna}"
        )

    print("\nArchivos creados:")

    print(
        f"- {archivo_current}"
    )

    print(
        f"- {archivo_archived}"
    )

    print("\n" + "=" * 100)
    print("PROCESO TERMINADO")
    print("=" * 100)


# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":

    main()