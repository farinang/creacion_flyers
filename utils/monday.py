import requests

from config.settings import (
    MONDAY_API_URL,
    BOARD_ID,
    MONDAY_TOKEN
)


HEADERS = {
    "Authorization": MONDAY_TOKEN,
    "Content-Type": "application/json"
}


# ============================================================
# CONSULTA
# ============================================================

def consultar_monday(
    query,
    variables=None
):

    response = requests.post(
        MONDAY_API_URL,
        json={
            "query": query,
            "variables": variables or {}
        },
        headers=HEADERS
    )

    print(
        "Status:",
        response.status_code
    )

    if response.status_code != 200:

        print(
            response.text
        )

        raise Exception(
            f"Error HTTP "
            f"{response.status_code}"
        )

    resultado = (
        response.json()
    )

    if "errors" in resultado:

        raise Exception(
            resultado["errors"]
        )

    return resultado["data"]


# ============================================================
# COLUMNAS DISPONIBLES
# ============================================================

def obtener_columnas_disponibles():

    query = """
    query ($board_id: [ID!]) {

      boards(ids: $board_id) {

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

    board = (
        data["boards"][0]
    )

    print(
        "\n" +
        "=" * 100
    )

    print(
        "COLUMNAS DISPONIBLES EN MONDAY"
    )

    print(
        "=" * 100
    )

    for columna in board[
        "columns"
    ]:

        print(
            f'{columna["title"]:<25} '
            f'{columna["id"]:<35} '
            f'[{columna["type"]}]'
        )

    return board[
        "columns"
    ]


# ============================================================
# PRIMERA PAGINA
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

            column_values {
              id
              text
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

    return (
        data["boards"][0]
        ["items_page"]
    )


# ============================================================
# SIGUIENTES PAGINAS
# ============================================================

def obtener_siguiente_pagina(
    cursor
):

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

          column_values {
            id
            text
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

    return (
        data[
            "next_items_page"
        ]
    )


# ============================================================
# TODOS LOS ITEMS
# ============================================================

def obtener_todos_los_items():

    items = []

    pagina = (
        obtener_primera_pagina()
    )

    items.extend(
        pagina["items"]
    )

    cursor = (
        pagina["cursor"]
    )

    print(
        f"\nItems descargados: "
        f"{len(items)}"
    )

    while cursor:

        pagina = (
            obtener_siguiente_pagina(
                cursor
            )
        )

        items.extend(
            pagina["items"]
        )

        cursor = (
            pagina["cursor"]
        )

        print(
            f"Items descargados: "
            f"{len(items)}"
        )

    return items