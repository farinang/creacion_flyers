from utils.monday import (
    obtener_columnas_disponibles,
    obtener_todos_los_items
)

from utils.inventory import (
    crear_dataframe,
    separar_inventarios,
    guardar_inventarios
)

from utils.drive import (
    conectar_drive,
    procesar_current_drive,
    procesar_archived_drive,
    guardar_drive_datasets
)


def main():

    print("\n" + "=" * 100)
    print("RENT REALTY - CREACION DE FLYERS")
    print("=" * 100)

    # ========================================================
    # FASE 1 - MONDAY
    # ========================================================

    print("\nFASE 1 - MONDAY")

    obtener_columnas_disponibles()

    items = (
        obtener_todos_los_items()
    )

    df = crear_dataframe(
        items
    )

    current, archived = (
        separar_inventarios(
            df
        )
    )

    guardar_inventarios(
        current,
        archived
    )

    print(
        f"\nCurrent detectadas: "
        f"{len(current)}"
    )

    print(
        f"Archived con Rented Date: "
        f"{len(archived)}"
    )

    # ========================================================
    # FASE 2 - GOOGLE DRIVE
    # ========================================================

    print("\nFASE 2 - GOOGLE DRIVE")

    drive = conectar_drive()

    # --------------------------------------------------------
    # Current
    # --------------------------------------------------------

    current_drive = (
        procesar_current_drive(
            drive,
            current
        )
    )

    # --------------------------------------------------------
    # Archived
    #
    # Solo buscamos hasta conseguir
    # 9 propiedades recientes CON imagen
    # --------------------------------------------------------

    archived_drive = (
        procesar_archived_drive(
            drive,
            archived
        )
    )

    # --------------------------------------------------------
    # Guardar
    # --------------------------------------------------------

    guardar_drive_datasets(
        current_drive,
        archived_drive
    )

    # ========================================================
    # RESUMEN
    # ========================================================

    current_con_imagen = (
        current_drive[
            "image_drive_url"
        ]
        .fillna("")
        .ne("")
        .sum()
    )

    print("\n" + "=" * 100)
    print("RESUMEN")
    print("=" * 100)

    print(
        f"\nCurrent total: "
        f"{len(current_drive)}"
    )

    print(
        f"Current con imagen: "
        f"{current_con_imagen}"
    )

    print(
        f"Current sin imagen: "
        f"{len(current_drive) - current_con_imagen}"
    )

    print(
        f"\nArchived recientes "
        f"con imagen: "
        f"{len(archived_drive)}"
    )

    print("\nArchivos generados:")

    print(
        "- data/current_inventory.csv"
    )

    print(
        "- data/archived_inventory.csv"
    )

    print(
        "- data/current_inventory_drive.csv"
    )

    print(
        "- data/archived_inventory_drive.csv"
    )

    print("\nProceso terminado.")


if __name__ == "__main__":

    main()